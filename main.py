import os
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Project settings
from core.settings import settings

# Routers: some modules export router directly, others use get_*_router() factories
from core.handlers import (
    basic,
    callback,
    admin_cabinet,
    profile,
    partner,
    activity,
    category_handlers,
)
from core.handlers.main_menu_router import main_menu_router

logger = logging.getLogger("bot.boot")


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()

    # 1) Include direct routers
    dp.include_router(basic.router)
    dp.include_router(callback.router)
    dp.include_router(admin_cabinet.router)
    dp.include_router(main_menu_router)

    # 2) Include routers from factories
    for getr in (
        getattr(profile, "get_profile_router", None),
        getattr(partner, "get_partner_router", None),
        getattr(activity, "get_activity_router", None),
        getattr(category_handlers, "get_category_router", None),
    ):
        if callable(getr):
            r = getr()
            if r:
                dp.include_router(r)

    return dp


async def run_bot():
    bot = Bot(
        token=settings.bots.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    
    # Critical: disable webhook before polling to avoid conflicts
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logger.warning(f"Webhook cleanup warning: {e}")

    dp = build_dispatcher()
    await dp.start_polling(bot)


def run_web():
    # Run uvicorn in a single worker without reload to avoid duplicate processes
    import uvicorn
    uvicorn.run(
        "web.app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        reload=False,
        workers=1,
        access_log=False,
    )


async def main():
    # ROLE controls the mode: bot | web | botweb
    role = os.getenv("ROLE", "botweb").lower()
    if role == "bot":
        await run_bot()
    elif role == "web":
        run_web()
    else:
        # botweb: run both services in a single process without workers
        await asyncio.gather(
            run_bot(),
            asyncio.to_thread(run_web),
        )


if __name__ == "__main__":
    # Prevent duplicate starts due to imports
    asyncio.run(main())
