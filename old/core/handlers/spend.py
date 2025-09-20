"""
Обработчики для системы списания баллов с FSM.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from core.keyboards.inline import get_confirmation_keyboard
from core.utils.locales import get_text

router = Router(name="spend")

class SpendStates(StatesGroup):
    """Состояния для процесса списания баллов"""
    waiting_for_amount = State()
    waiting_for_confirmation = State()

@router.message(F.text == get_text("keyboard.spend_points", "ru"))
async def start_spend_process(message: Message, state: FSMContext):
    """Начало процесса списания баллов"""
    await message.answer(
        "Введите количество баллов для списания:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(SpendStates.waiting_for_amount)

@router.message(SpendStates.waiting_for_amount, F.text.regexp(r'^\d+$').as_("digits"))
async def process_amount(message: Message, state: FSMContext, digits: re.Match):
    """Обработка введенного количества баллов"""
    amount = int(digits.group())
    await state.update_data(amount=amount)
    
    # Запрашиваем подтверждение
    await message.answer(
        f"Вы хотите списать {amount} баллов?",
        reply_markup=get_confirmation_keyboard()
    )
    await state.set_state(SpendStates.waiting_for_confirmation)

@router.callback_query(SpendStates.waiting_for_confirmation, F.data == "confirm")
async def confirm_spend(callback: CallbackQuery, state: FSMContext):
    """Подтверждение списания баллов"""
    data = await state.get_data()
    amount = data.get("amount", 0)
    
    # Здесь должна быть логика списания баллов
    # ...
    
    await callback.message.answer(f"Списано {amount} баллов")
    await state.clear()
    await callback.answer()
