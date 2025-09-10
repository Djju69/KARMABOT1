"""
User profile and related handlers.
Handles user profile viewing and management.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import Optional, Dict, Any
import logging

from ..keyboards.reply_v2 import (
    get_return_to_main_menu
)
from ..utils.locales_v2 import get_text
from ..services.user_service import (
    get_user_balance,
    get_user_level,
    get_user_history,
    subtract_karma,
    add_karma,
    get_or_create_user
)

logger = logging.getLogger(__name__)
router = Router()

class UserStates(StatesGroup):
    """States for user profile interactions"""
    viewing_profile = State()
    viewing_points = State()
    viewing_history = State()
    spending_points = State()
    viewing_settings = State()

@router.message(F.text.in_(["👤 Профиль", "👤 Profile", "👤 Hồ sơ", "👤 프로필"]))
@router.message(Command("profile"))
async def user_profile_handler(message: Message, state: FSMContext):
    """
    Handle user profile command.
    Shows user profile with balance, level and navigation options.
    """
    try:
        # Get or create user in database
        user = await get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            lang_code='ru'  # Default language, should be fetched from user settings
        )
        
        # Get user balance and level
        balance = await get_user_balance(user.telegram_id)
        level = await get_user_level(user.telegram_id)
        
        # Format profile message
        profile_text = get_text("cabinet.user_profile", user.lang_code).format(
            points=balance,
            level=level
        )
        
        # Get profile keyboard with user language
        keyboard = get_return_to_main_menu(lang)
        
        # Send or update profile message
        await message.answer(profile_text, reply_markup=keyboard)
        await state.set_state(UserStates.viewing_profile)
        await state.update_data(current_screen="profile")
        
    except Exception as e:
        logger.error(f"Error in user_profile_handler: {e}", exc_info=True)
        await message.answer(
            get_text("error_occurred", 'ru'),
            reply_markup=get_return_to_main_menu()
        )


@router.message(F.text.in_(["💰 Баллы", "💰 Points", "💰 Điểm", "💰 포인트"]))
@router.message(Command("points"))
async def user_points_handler(message: Message, state: FSMContext):
    """
    Handle points viewing.
    Shows user's current balance and points-related actions.
    """
    try:
        # Get or create user in database
        user = await get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            lang_code='ru'
        )
        
        # Get user balance
        balance = await get_user_balance(user.telegram_id)
        
        # Format points message
        points_text = get_text("cabinet.user_points", user.lang_code).format(
            points=balance
        )
        
        # Get points keyboard
        keyboard = get_return_to_main_menu(lang)
        
        await message.answer(points_text, reply_markup=keyboard)
        await state.set_state(UserStates.viewing_points)
        await state.update_data(current_screen="points")
        
    except Exception as e:
        logger.error(f"Error in user_points_handler: {e}", exc_info=True)
        await message.answer(
            get_text("error_occurred", 'ru'),
            reply_markup=get_return_to_main_menu()
        )


@router.message(F.text.in_(["📜 История", "📜 History", "📜 Lịch sử", "📜 내역"]))
@router.message(Command("history"))
async def user_history_handler(message: Message, state: FSMContext):
    """
    Handle transaction history.
    Shows paginated list of user's transactions.
    """
    try:
        # Get user data
        user = await get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            lang_code='ru'
        )
        
        # Get transaction history (first page)
        history_data = await get_user_history(user.telegram_id, page=1)
        
        # Format history message
        if not history_data["transactions"]:
            history_text = get_text("no_history", user.lang_code)
        else:
            history_text = get_text("cabinet.history_header", user.lang_code) + "\n\n"
            for tx in history_data["transactions"]:
                date_str = tx.created_at.strftime("%d.%m.%Y %H:%M")
                sign = "+" if tx.amount > 0 else ""
                history_text += f"{date_str}: {sign}{tx.amount} - {tx.description}\n"
        
        # Create inline keyboard for pagination
        keyboard_buttons = []
        if history_data["has_previous"]:
            keyboard_buttons.append(
                InlineKeyboardButton(
                    text="⬅️ " + get_text("prev_page", user.lang_code),
                    callback_data=f"history_page:{history_data['current_page'] - 1}"
                )
            )
        
        if history_data["has_next"]:
            keyboard_buttons.append(
                InlineKeyboardButton(
                    text=get_text("next_page", user.lang_code) + " ➡️",
                    callback_data=f"history_page:{history_data['current_page'] + 1}"
                )
            )
        
        keyboard = [keyboard_buttons] if keyboard_buttons else []
        keyboard.append([
            InlineKeyboardButton(
                text=get_text("keyboard.close", user.lang_code),
                callback_data="close_history"
            )
        ])
        
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        # Send history message
        await message.answer(history_text, reply_markup=reply_markup)
        await state.set_state(UserStates.viewing_history)
        await state.update_data(current_screen="history")
        
    except Exception as e:
        logger.error(f"Error in user_history_handler: {e}", exc_info=True)
        await message.answer(
            get_text("error_occurred", 'ru'),
            reply_markup=get_return_to_main_menu()
        )


@router.message(F.text.in_(["💳 Потратить", "💳 Spend", "💳 Tiêu điểm", "💳 사용"]))
@router.message(Command("spend"))
async def spend_points_handler(message: Message, state: FSMContext):
    """
    Start spend points flow.
    Asks user to enter amount to spend.
    """
    try:
        user = await get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            lang_code='ru'
        )
        
        # Get user balance
        balance = await get_user_balance(user.telegram_id)
        
        if balance <= 0:
            await message.answer(
                get_text("not_enough_points", user.lang_code),
                reply_markup=get_return_to_main_menu(lang)
            )
            return
        
        # Ask for amount to spend
        await message.answer(
            get_text("enter_amount_to_spend", user.lang_code).format(balance=balance),
            reply_markup=get_return_to_main_menu(user.lang_code)
        )
        
        await state.set_state(UserStates.spending_points)
        await state.update_data(current_screen="spend_points")
        
    except Exception as e:
        logger.error(f"Error in spend_points_handler: {e}", exc_info=True)
        await message.answer(
            get_text("error_occurred", 'ru'),
            reply_markup=get_return_to_main_menu()
        )


@router.message(UserStates.spending_points)
async def process_spend_amount(message: Message, state: FSMContext):
    """
    Process amount to spend and ask for confirmation.
    """
    try:
        user = await get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            lang_code='ru'
        )
        
        # Parse amount
        try:
            amount = int(message.text.strip())
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except (ValueError, AttributeError):
            await message.answer(
                get_text("invalid_amount", user.lang_code),
                reply_markup=get_return_to_main_menu(user.lang_code)
            )
            return
        
        # Check balance
        balance = await get_user_balance(user.telegram_id)
        if amount > balance:
            await message.answer(
                get_text("not_enough_points", user.lang_code),
                reply_markup=get_return_to_main_menu(user.lang_code)
            )
            return
        
        # Save amount in state and ask for confirmation
        await state.update_data(amount_to_spend=amount)
        
        # Create confirmation message with inline buttons
        confirm_text = get_text("confirm_spend", user.lang_code).format(
            amount=amount,
            remaining=balance - amount
        )
        
        keyboard = [
            [
                InlineKeyboardButton(
                    text=get_text("keyboard.confirm", user.lang_code),
                    callback_data="confirm_spend"
                ),
                InlineKeyboardButton(
                    text=get_text("keyboard.cancel", user.lang_code),
                    callback_data="cancel_spend"
                )
            ]
        ]
        
        await message.answer(
            confirm_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
    except Exception as e:
        logger.error(f"Error in process_spend_amount: {e}", exc_info=True)
        await message.answer(
            get_text("error_occurred", 'ru'),
            reply_markup=get_return_to_main_menu()
        )


@router.callback_query(F.data.startswith("history_page:"))
async def handle_history_pagination(callback: CallbackQuery, state: FSMContext):
    """Handle pagination for transaction history"""
    try:
        page = int(callback.data.split(":")[1])
        user = await get_or_create_user(telegram_id=callback.from_user.id)
        
        # Get transaction history for the requested page
        history_data = await get_user_history(user.telegram_id, page=page)
        
        # Format history message (same as in user_history_handler)
        if not history_data["transactions"]:
            history_text = get_text("no_history", user.lang_code)
        else:
            history_text = get_text("cabinet.history_header", user.lang_code) + "\n\n"
            for tx in history_data["transactions"]:
                date_str = tx.created_at.strftime("%d.%m.%Y %H:%M")
                sign = "+" if tx.amount > 0 else ""
                history_text += f"{date_str}: {sign}{tx.amount} - {tx.description}\n"
        
        # Update keyboard with new page
        keyboard_buttons = []
        if history_data["has_previous"]:
            keyboard_buttons.append(
                InlineKeyboardButton(
                    text="⬅️ " + get_text("prev_page", user.lang_code),
                    callback_data=f"history_page:{history_data['current_page'] - 1}"
                )
            )
        
        if history_data["has_next"]:
            keyboard_buttons.append(
                InlineKeyboardButton(
                    text=get_text("next_page", user.lang_code) + " ➡️",
                    callback_data=f"history_page:{history_data['current_page'] + 1}"
                )
            )
        
        keyboard = [keyboard_buttons] if keyboard_buttons else []
        keyboard.append([
            InlineKeyboardButton(
                text=get_text("keyboard.close", user.lang_code),
                callback_data="close_history"
            )
        ])
        
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        # Update message with new page
        await callback.message.edit_text(history_text, reply_markup=reply_markup)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in handle_history_pagination: {e}", exc_info=True)
        await callback.answer(get_text("error_occurred", 'ru'), show_alert=True)


@router.callback_query(F.data == "close_history")
async def close_history(callback: CallbackQuery, state: FSMContext):
    """Close history view"""
    try:
        await callback.message.delete()
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in close_history: {e}", exc_info=True)
        await callback.answer(get_text("error_occurred", 'ru'), show_alert=True)


@router.callback_query(F.data == "confirm_spend")
async def confirm_spend_points(callback: CallbackQuery, state: FSMContext):
    """Confirm and process points spending"""
    try:
        user_data = await state.get_data()
        amount = user_data.get("amount_to_spend")
        
        if not amount:
            await callback.answer(get_text("error_occurred", 'ru'), show_alert=True)
            return
        
        user = await get_or_create_user(telegram_id=callback.from_user.id)
        
        # Process points spending
        success = await subtract_karma(
            user_id=user.telegram_id,
            amount=amount,
            reason=get_text("points_spent", user.lang_code)
        )
        
        if success:
            # Get updated balance
            balance = await get_user_balance(user.telegram_id)
            
            # Send success message
            success_text = get_text("points_spent_success", user.lang_code).format(
                amount=amount,
                remaining=balance
            )
            
            await callback.message.edit_text(success_text)
            await callback.answer()
            
            # Return to profile
            await user_profile_handler(
                Message(
                    chat=callback.message.chat,
                    from_user=callback.from_user,
                    text=get_text("keyboard.back", user.lang_code)
                ),
                state
            )
        else:
            await callback.answer(
                get_text("not_enough_points", user.lang_code),
                show_alert=True
            )
            
    except Exception as e:
        logger.error(f"Error in confirm_spend_points: {e}", exc_info=True)
        await callback.answer(get_text("error_occurred", 'ru'), show_alert=True)


@router.callback_query(F.data == "cancel_spend")
async def cancel_spend_points(callback: CallbackQuery, state: FSMContext):
    """Cancel points spending"""
    try:
        await callback.message.delete()
        await callback.answer()
        
        # Return to profile
        user = await get_or_create_user(telegram_id=callback.from_user.id)
        await user_profile_handler(
            Message(
                chat=callback.message.chat,
                from_user=callback.from_user,
                text=get_text("keyboard.back", user.lang_code)
            ),
            state
        )
        
    except Exception as e:
        logger.error(f"Error in cancel_spend_points: {e}", exc_info=True)
        await callback.answer(get_text("error_occurred", 'ru'), show_alert=True)


@router.message(F.text.in_(["⚙️ Настройки", "⚙️ Settings", "⚙️ Cài đặt", "⚙️ 설정"]))
@router.message(Command("settings"))
async def user_settings_handler(message: Message, state: FSMContext):
    """
    Handle user settings command.
    Shows user settings and preferences.
    """
    try:
        user = await get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            lang_code='ru'
        )
        
        # Format settings message
        settings_text = get_text("settings_header", user.lang_code)
        
        # Get settings keyboard with user language
        keyboard = get_return_to_main_menu(user.lang_code)
        
        await message.answer(settings_text, reply_markup=keyboard)
        await state.set_state(UserStates.viewing_settings)
        await state.update_data(current_screen="settings")
        
    except Exception as e:
        logger.error(f"Error in user_settings_handler: {e}", exc_info=True)
        await message.answer(
            get_text("error_occurred", 'ru'),
            reply_markup=get_return_to_main_menu()
        )


@router.message(F.text.in_(["◀️ Назад", "◀️ Back", "◀️ Quay lại", "◀️ 뒤로"]))
async def back_handler(message: Message, state: FSMContext):
    """Handle back button navigation"""
    try:
        # Get current screen from state
        user_data = await state.get_data()
        current_screen = user_data.get("current_screen", "profile")
        
        # Return to the appropriate screen based on current state
        if current_screen in ["points", "history", "settings"]:
            await user_profile_handler(message, state)
        else:
            # Default to main menu if no specific screen
            await message.answer(
                get_text("returning_to_main", 'ru'),
                reply_markup=get_return_to_main_menu()
            )
    except Exception as e:
        logger.error(f"Error in back_handler: {e}", exc_info=True)
        await message.answer(
            get_text("error_occurred", 'ru'),
            reply_markup=get_return_to_main_menu()
        )


def register_user_handlers(dp):
    """Register user handlers with the dispatcher"""
    dp.include_router(router)
