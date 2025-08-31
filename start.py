#!/usr/bin/env python3
"""
Main entry point for running both web server and bot concurrently.
"""
import logging
from logging.handlers import RotatingFileHandler
import os
import asyncio
import signal
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            'app.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
    ]
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import web app and bot after path is set
try:
    # First try to import web app
    try:
        from web.main import app as web_app
        import uvicorn
        WEB_IMPORTED = True
        logger.info("✅ Web app imported successfully")
    except ImportError as e:
        logger.warning(f"❌ Web app import failed: {e}")
        WEB_IMPORTED = False
        
    # Then try to import bot from main_v2
    try:
        from main_v2 import main as bot_main
        BOT_IMPORTED = True
        logger.info("✅ Bot imported successfully from main_v2")
    except ImportError as e:
        logger.error(f"❌ Bot import failed: {e}")
        BOT_IMPORTED = False
        
        # Try alternative import
        try:
            sys.path.append(project_root)
            from bot.bot import bot
            BOT_IMPORTED = True
            logger.info("✅ Bot imported successfully from bot.bot")
        except ImportError as e2:
            logger.error(f"❌ Alternative bot import failed: {e2}")
    
    # Try to import settings and Sentry if available
    try:
        from core.config import settings
        from core.monitoring import setup_sentry
        
        if hasattr(settings, 'sentry_dsn') and settings.sentry_dsn:
            setup_sentry(settings.sentry_dsn)
            logger.info("✅ Sentry initialized")
    except ImportError as e:
        logger.warning(f"⚠️ Could not import settings or Sentry: {e}")
        
    if not WEB_IMPORTED and not BOT_IMPORTED:
        raise ImportError("❌ Failed to import both web app and bot")
        
except Exception as e:
    logger.error(f"❌ Critical error during imports: {e}", exc_info=True)
    # Try to start at least the web server if possible
    if 'web_app' in locals():
        port = int(os.getenv("PORT", 8000))
        logger.warning(f"⚠️ Starting web server only on port {port}")
        uvicorn.run(web_app, host="0.0.0.0", port=port)
    sys.exit(1)

# Global flag for shutdown
shutdown_event = asyncio.Event()

def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Shutdown signal received, stopping services...")
    shutdown_event.set()

async def run_web_server():
    """Run the FastAPI web server if available."""
    if not WEB_IMPORTED:
        logger.warning("Web server not available - skipping")
        return
        
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    try:
        config = uvicorn.Config(
            app=web_app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        
        server = uvicorn.Server(config)
        logger.info(f"Starting web server on {host}:{port}")
        
        try:
            await server.serve()
        except asyncio.CancelledError:
            logger.info("Web server shutdown requested")
        except Exception as e:
            logger.error(f"Web server error: {e}")
            raise
        finally:
            logger.info("Web server stopped")
            
    except Exception as e:
        logger.error(f"Failed to start web server: {e}")
        if BOT_IMPORTED:
            logger.info("Continuing with bot only...")
        else:
            raise

async def run_bot():
    """Run the Telegram bot if available."""
    if not BOT_IMPORTED:
        logger.warning("❌ Bot not available - skipping")
        return
        
    try:
        logger.info("🤖 Starting Telegram bot...")
        if 'bot_main' in globals():
            # If we imported main() from main_v2
            logger.info("🚀 Starting bot using main_v2.main()")
            await bot_main()
        elif 'bot' in globals():
            # If we have a direct bot instance
            logger.info("🚀 Starting bot using direct bot instance")
            await bot.start_polling()
        else:
            raise RuntimeError("No valid bot instance found to start")
            
    except asyncio.CancelledError:
        logger.info("🛑 Bot shutdown requested")
    except Exception as e:
        logger.error(f"❌ Bot error: {e}", exc_info=True)
        if not WEB_IMPORTED:
            raise  # Only raise if web server is not available
        logger.warning("⚠️ Continuing with web server only...")
    finally:
        # Ensure bot is properly stopped
        if 'bot' in globals() and hasattr(bot, 'session') and bot.session and not bot.session.closed:
            logger.info("🛑 Closing bot session...")
            await bot.session.close()
        logger.info("✅ Bot stopped")

async def main():
    """Main entry point for running all services."""
    # Register signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(
                sig, 
                lambda s=sig: asyncio.create_task(shutdown(sig, loop))
            )
        except (NotImplementedError, RuntimeError) as e:
            logger.warning(f"Could not set signal handler for {sig}: {e}")
    
    # Start services that are available
    tasks = []
    
    if WEB_IMPORTED:
        web_task = asyncio.create_task(run_web_server())
        tasks.append(web_task)
        
    if BOT_IMPORTED:
        bot_task = asyncio.create_task(run_bot())
        tasks.append(bot_task)
    
    if not tasks:
        logger.error("No services available to start")
        return 1
    
    try:
        # Wait for shutdown signal or any task to complete
        done, pending = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # If we get here, one of the tasks completed (possibly with an error)
        for task in done:
            try:
                await task  # This will raise any exceptions
            except Exception as e:
                logger.error(f"Service failed: {e}")
        
        # If we have pending tasks, wait for them to complete
        if pending:
            logger.info("Waiting for remaining services to shut down...")
            await asyncio.wait(pending, timeout=10.0)
            
    except asyncio.CancelledError:
        logger.info("Main task cancelled")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        return 1
    finally:
        # Cancel any remaining tasks
        for task in tasks:
            if not task.done():
                task.cancel()
        
        # Wait for all tasks to complete
        if tasks:
            await asyncio.wait(tasks, timeout=5.0, return_exceptions=True)
        
        logger.info("Application shutdown complete")
        return 0

async def shutdown(sig, loop):
    """Handle the shutdown process gracefully."""
    if shutdown_event.is_set():
        return  # Already shutting down
        
    logger.info(f"Received exit signal {sig.name}...")
    shutdown_event.set()
    
    # Get all running tasks except current one
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    
    if not tasks:
        logger.info("No tasks to cancel")
        loop.stop()
        return
    
    logger.info(f"Cancelling {len(tasks)} outstanding tasks...")
    
    # Cancel all tasks
    for task in tasks:
        if not task.done():
            task.cancel()
    
    # Wait for tasks to complete with timeout
    try:
        await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=10.0  # Max 10 seconds for graceful shutdown
        )
        logger.info("All tasks completed successfully")
    except asyncio.TimeoutError:
        logger.warning("Timeout waiting for tasks to complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    finally:
        # Stop the event loop
        loop.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
