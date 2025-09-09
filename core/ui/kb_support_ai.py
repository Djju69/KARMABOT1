"""
Клавиатуры для AI-ассистента "Карма"
"""
from aiogram.utils.keyboard import InlineKeyboardBuilder


def kb_support_ai():
    """Кнопка для запуска AI-ассистента под /help"""
    kb = InlineKeyboardBuilder()
    kb.button(text="🤖 Задать вопрос ИИ", callback_data="support_ai_start")
    kb.adjust(1)
    return kb.as_markup()


def kb_ai_controls():
    """Кнопки управления в AI-режиме"""
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Выйти", callback_data="support_ai_exit")
    kb.button(text="📨 Эскалировать", callback_data="support_ai_escalate")
    kb.adjust(2)
    return kb.as_markup()
