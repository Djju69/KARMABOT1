"""Basic ping/pong and start command handlers."""
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

router = Router(name="ping_router")

@router.message(CommandStart())
async def on_start(msg: Message):
    """Handle /start command."""
    await msg.answer("✅ Бот на связи. Главное меню: /menu")

@router.message(Command("menu"))
async def on_menu(msg: Message):
    """Handle /menu command."""
    await msg.answer("🗂 Главное меню (stub)")

# catch-all — ограничен группами, чтобы не перехватывать личные чаты
@router.message(F.text & F.chat.type.in_({"group", "supergroup"}))
async def on_any_text_group(msg: Message):
    """Handle any text message in group chats."""
    await msg.answer("👋 Принял текст. Наберите /menu или /start.")
