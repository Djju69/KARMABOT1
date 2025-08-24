from __future__ import annotations

from aiogram.types import Message

# Minimal text provider for main menu used by legacy parts

def main_menu_text(lang: str = "ru") -> str:
    texts = {
        "ru": "Главное меню: выберите категорию или действие ниже.",
        "en": "Main menu: choose a category or an action below.",
        "vi": "Menu chính: chọn một danh mục hoặc thao tác bên dưới.",
        "ko": "메인 메뉴: 아래에서 카테고리 또는 작업을 선택하세요.",
    }
    return texts.get(lang, texts["ru"])

# Helper to send main menu text
async def send_main_menu(message: Message, lang: str = "ru"):
    await message.answer(main_menu_text(lang))

__all__ = ["main_menu_text", "send_main_menu"]
