"""
Обработчики для просмотра истории операций с пагинацией.
"""
from typing import List, Dict, Any
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

router = Router(name="history")

# Заглушка для данных истории (в реальном приложении это будет запрос к БД)
MOCK_HISTORY = [
    {"id": i, "date": f"2023-01-{i:02d}", "amount": i*100, "type": "Начисление" if i % 2 else "Списание"}
    for i in range(1, 21)
]

ITEMS_PER_PAGE = 5

def get_history_page(page: int = 1) -> tuple[str, InlineKeyboardMarkup]:
    """Генерация страницы истории с пагинацией"""
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_items = MOCK_HISTORY[start:end]
    
    # Формируем текст
    text = f"📜 История операций (страница {page}):\n\n"
    for item in page_items:
        text += f"{item['date']}: {item['type']} {item['amount']} баллов\n"
    
    # Формируем клавиатуру пагинации
    kb = []
    if page > 1:
        kb.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"history_page_{page-1}"))
    if end < len(MOCK_HISTORY):
        kb.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"history_page_{page+1}"))
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[kb]) if kb else None
    
    return text, reply_markup

@router.message(F.text == "📜 История операций")
async def show_history(message: Message):
    """Показ первой страницы истории"""
    text, reply_markup = get_history_page(1)
    await message.answer(text, reply_markup=reply_markup)

@router.callback_query(F.data.startswith("history_page_"))
async def handle_history_pagination(callback: CallbackQuery):
    """Обработка переключения страниц истории"""
    try:
        page = int(callback.data.split("_")[2])
        text, reply_markup = get_history_page(page)
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except (IndexError, ValueError):
        await callback.answer("Ошибка пагинации")
    await callback.answer()
