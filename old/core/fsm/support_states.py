"""
FSM состояния для AI-ассистента "Карма"
"""
from aiogram.fsm.state import State, StatesGroup


class SupportStates(StatesGroup):
    """Состояния для AI-ассистента поддержки"""
    idle = State()        # Ожидание
    chatting = State()    # Активный чат с AI