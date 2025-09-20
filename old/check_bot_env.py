#!/usr/bin/env python3
"""
Script to verify required environment variables for the bot.
"""
import os
import logging
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_required_vars() -> Dict[str, bool]:
    """Check for required environment variables."""
    required_vars = [
        'BOT_TOKEN',
        'TELEGRAM_TOKEN',
        'DATABASE_URL',
        'REDIS_URL'
    ]
    
    results = {}
    for var in required_vars:
        value = os.getenv(var)
        results[var] = value is not None
        status = "✅" if results[var] else "❌"
        logger.info(f"{status} {var}: {'Set' if results[var] else 'Not set'}")
        if value and var.endswith('_TOKEN') and len(value) > 10:
            logger.info(f"   Token found: {value[:5]}...{value[-5:]}")
    
    return results

def check_optional_vars() -> Dict[str, Optional[str]]:
    """Check optional but recommended environment variables."""
    optional_vars = [
        'SENTRY_DSN',
        'ENVIRONMENT',
        'LOG_LEVEL',
        'ADMIN_IDS',
        'WEBHOOK_URL'
    ]
    
    results = {}
    for var in optional_vars:
        value = os.getenv(var)
        results[var] = value
        if value is not None:
            logger.info(f"ℹ️  {var}: Set")
            if var.endswith(('_TOKEN', '_SECRET', '_KEY', '_PASSWORD')) and len(value) > 10:
                logger.info(f"   Value found: {value[:3]}...{value[-3:]}")
        else:
            logger.warning(f"⚠️  {var}: Not set (optional but recommended)")
    
    return results

def check_database_connection() -> bool:
    """Check if database connection is possible."""
    try:
        # Try to import database module
        from core.database.database import Database
        db = Database()
        # Try to execute a simple query
        db.execute("SELECT 1")
        logger.info("✅ Database connection: Successful")
        return True
    except ImportError:
        logger.warning("⚠️  Database module not found")
        return False
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def main():
    """Main function to run all checks."""
    print("\n=== Environment Variable Check ===\n")
    
    # Check required variables
    print("\n[REQUIRED VARIABLES]")
    required_results = check_required_vars()
    
    # Check optional variables
    print("\n[OPTIONAL VARIABLES]")
    check_optional_vars()
    
    # Check database connection
    print("\n[DATABASE CONNECTION]")
    db_ok = check_database_connection()
    
    # Summary
    print("\n=== SUMMARY ===")
    missing_required = [var for var, present in required_results.items() if not present]
    
    if missing_required:
        logger.error(f"❌ Missing required variables: {', '.join(missing_required)}")
        return 1
    elif not db_ok:
        logger.warning("⚠️  Database connection check failed")
        return 0
    else:
        logger.info("✅ All required variables are set and database is accessible")
        return 0

if __name__ == "__main__":
    exit(main())
