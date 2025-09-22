#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QR Code handlers for KARMABOT1 Telegram Bot
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, StateFilter
from typing import Dict, Any, List
import json

from core.services.qr_code_service import QRCodeService
from core.database import get_db
from core.logger import get_logger
def _back_to_main_menu_keyboard():
    # Inline back button to main menu (existing handler listens to callback_data="main_menu").
    try:
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]]
        )
    except Exception:
        return None

logger = get_logger(__name__)

router = Router()


class QRCodeStates(StatesGroup):
    """States for QR code generation"""
    waiting_for_discount_type = State()
    waiting_for_discount_value = State()
    waiting_for_expiration = State()
    waiting_for_description = State()


@router.message(Command("qr_codes"))
async def show_qr_codes_menu(message: Message, state: FSMContext):
    """Show QR codes menu"""
    try:
        await state.clear()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Мои QR-коды", callback_data="qr_my_codes")],
            [InlineKeyboardButton(text="➕ Создать QR-код", callback_data="qr_create")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="qr_stats")],
            [InlineKeyboardButton(text="❓ Помощь", callback_data="qr_help")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        
        await message.answer(
            "🎫 <b>QR-коды и скидки</b>\n\n"
            "Здесь вы можете:\n"
            "• Создавать QR-коды для получения скидок\n"
            "• Просматривать свои QR-коды\n"
            "• Отслеживать статистику использования\n\n"
            "Выберите действие:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error showing QR codes menu: {e}")
        await message.answer(
            "❌ Произошла ошибка при загрузке меню QR-кодов. Попробуйте позже.",
            reply_markup=_back_to_main_menu_keyboard()
        )


@router.callback_query(F.data == "qr_my_codes")
async def show_my_qr_codes(callback: CallbackQuery, state: FSMContext):
    """Show user's QR codes"""
    try:
        await callback.answer()
        
        db = next(get_db())
        qr_service = QRCodeService(db)
        user_id = callback.from_user.id
        
        # Get user's QR codes
        qr_codes = await qr_service.get_user_qr_codes(
            user_id=user_id,
            limit=10,
            include_used=True
        )
        
        if not qr_codes:
            await callback.message.edit_text(
                "📭 <b>У вас пока нет QR-кодов</b>\n\n"
                "Создайте свой первый QR-код для получения скидок!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="➕ Создать QR-код", callback_data="qr_create")],
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
                ]),
                parse_mode="HTML"
            )
            return
        
        # Format QR codes list
        text = "🎫 <b>Ваши QR-коды</b>\n\n"
        
        for i, qr in enumerate(qr_codes[:5], 1):  # Show first 5
            status_emoji = "✅" if qr["is_used"] else "⏰" if not qr["is_used"] else "❌"
            status_text = "Использован" if qr["is_used"] else "Активен"
            
            text += f"{i}. {status_emoji} <b>{qr['description']}</b>\n"
            text += f"   💰 Скидка: {qr['discount_value']} {qr['discount_type']}\n"
            text += f"   📅 Создан: {qr['created_at'][:10]}\n"
            text += f"   ⏰ Статус: {status_text}\n\n"
        
        if len(qr_codes) > 5:
            text += f"... и еще {len(qr_codes) - 5} QR-кодов\n\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Создать новый", callback_data="qr_create")],
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="qr_my_codes")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error showing user QR codes: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при загрузке QR-кодов. Попробуйте позже.",
            reply_markup=_back_to_main_menu_keyboard()
        )


@router.callback_query(F.data == "qr_create")
async def start_qr_creation(callback: CallbackQuery, state: FSMContext):
    """Start QR code creation process"""
    try:
        await callback.answer()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 Баллы лояльности", callback_data="qr_type_loyalty_points")],
            [InlineKeyboardButton(text="📊 Процент скидки", callback_data="qr_type_percentage")],
            [InlineKeyboardButton(text="💵 Фиксированная сумма", callback_data="qr_type_fixed_amount")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        
        await callback.message.edit_text(
            "🎫 <b>Создание QR-кода</b>\n\n"
            "Выберите тип скидки:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error starting QR creation: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при создании QR-кода. Попробуйте позже.",
            reply_markup=_back_to_main_menu_keyboard()
        )


@router.callback_query(F.data.regexp(r"^qr_create:[0-9]+$"))
async def start_qr_creation_for_card(callback: CallbackQuery, state: FSMContext):
    """Start QR code creation process for specific card"""
    try:
        await callback.answer()
        
        # Извлекаем ID карточки
        card_id = int(callback.data.split(":")[1])
        
        # Получаем информацию о карточке
        from core.database import db_v2
        card = db_v2.get_card_by_id(card_id)
        
        if not card:
            await callback.answer("❌ Карточка не найдена", show_alert=True)
            return
        
        # Сохраняем ID карточки в состоянии
        await state.update_data(card_id=card_id, card_title=card.get('title', 'Без названия'))
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 Баллы лояльности", callback_data="qr_type_loyalty_points")],
            [InlineKeyboardButton(text="📊 Процент скидки", callback_data="qr_type_percentage")],
            [InlineKeyboardButton(text="💵 Фиксированная сумма", callback_data="qr_type_fixed_amount")],
            [InlineKeyboardButton(text="◀️ Назад к карточке", callback_data=f"act:view:{card_id}")]
        ])
        
        await callback.message.edit_text(
            f"🎫 <b>Создание QR-кода для карточки</b>\n\n"
            f"📋 <b>Карточка:</b> {card.get('title', 'Без названия')}\n\n"
            f"Выберите тип скидки:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        await state.set_state(QRStates.selecting_type)
        
    except Exception as e:
        logger.error(f"Error starting QR creation for card: {e}")
        await callback.answer("❌ Ошибка при создании QR-кода", show_alert=True)


@router.callback_query(F.data.startswith("qr_type_"))
async def select_discount_type(callback: CallbackQuery, state: FSMContext):
    """Select discount type"""
    try:
        await callback.answer()
        
        discount_type = callback.data.split("_")[2]  # loyalty_points, percentage, fixed_amount
        
        # Store discount type in state
        await state.update_data(discount_type=discount_type)
        await state.set_state(QRCodeStates.waiting_for_discount_value)
        
        # Set appropriate message based on type
        if discount_type == "loyalty_points":
            text = "💰 <b>Баллы лояльности</b>\n\nВведите количество баллов для скидки:"
        elif discount_type == "percentage":
            text = "📊 <b>Процент скидки</b>\n\nВведите процент скидки (1-100):"
        else:  # fixed_amount
            text = "💵 <b>Фиксированная сумма</b>\n\nВведите сумму скидки в рублях:"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="qr_codes")]
        ])
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error selecting discount type: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при выборе типа скидки. Попробуйте позже.",
            reply_markup=_back_to_main_menu_keyboard()
        )


@router.message(QRCodeStates.waiting_for_discount_value)
async def process_discount_value(message: Message, state: FSMContext):
    """Process discount value input"""
    try:
        # Get discount value
        try:
            discount_value = int(message.text)
            if discount_value <= 0:
                await message.answer("❌ Значение должно быть положительным числом. Попробуйте еще раз:")
                return
        except ValueError:
            await message.answer("❌ Введите корректное число. Попробуйте еще раз:")
            return
        
        # Store discount value
        await state.update_data(discount_value=discount_value)
        await state.set_state(QRCodeStates.waiting_for_expiration)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="1 час", callback_data="qr_exp_1")],
            [InlineKeyboardButton(text="6 часов", callback_data="qr_exp_6")],
            [InlineKeyboardButton(text="24 часа", callback_data="qr_exp_24")],
            [InlineKeyboardButton(text="3 дня", callback_data="qr_exp_72")],
            [InlineKeyboardButton(text="7 дней", callback_data="qr_exp_168")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="qr_codes")]
        ])
        
        await message.answer(
            "⏰ <b>Срок действия QR-кода</b>\n\n"
            "Выберите, как долго будет действовать QR-код:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error processing discount value: {e}")
        await message.answer(
            "❌ Ошибка при обработке значения скидки. Попробуйте позже.",
            reply_markup=_back_to_main_menu_keyboard()
        )


@router.callback_query(F.data.startswith("qr_exp_"))
async def select_expiration(callback: CallbackQuery, state: FSMContext):
    """Select expiration time"""
    try:
        await callback.answer()
        
        hours = int(callback.data.split("_")[2])  # 1, 6, 24, 72, 168
        
        # Store expiration
        await state.update_data(expires_in_hours=hours)
        await state.set_state(QRCodeStates.waiting_for_description)
        
        await callback.message.edit_text(
            "📝 <b>Описание скидки</b>\n\n"
            "Введите описание для вашего QR-кода (например: 'Скидка 10% на кофе'):",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error selecting expiration: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при выборе срока действия. Попробуйте позже.",
            reply_markup=_back_to_main_menu_keyboard()
        )


@router.message(QRCodeStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    """Process description and create QR code"""
    try:
        description = message.text.strip()
        
        if len(description) > 200:
            await message.answer("❌ Описание слишком длинное (максимум 200 символов). Попробуйте еще раз:")
            return
        
        # Get all data from state
        data = await state.get_data()
        discount_type = data.get("discount_type")
        discount_value = data.get("discount_value")
        expires_in_hours = data.get("expires_in_hours")
        
        # Create QR code
        db = next(get_db())
        qr_service = QRCodeService(db)
        user_id = message.from_user.id
        
        qr_code = await qr_service.generate_qr_code(
            user_id=user_id,
            discount_type=discount_type,
            discount_value=discount_value,
            expires_in_hours=expires_in_hours,
            description=description
        )
        
        # Clear state
        await state.clear()
        
        # Send QR code image
        await message.answer_photo(
            photo=qr_code["qr_image"],
            caption=f"🎫 <b>QR-код создан!</b>\n\n"
                   f"📝 <b>Описание:</b> {description}\n"
                   f"💰 <b>Скидка:</b> {discount_value} {discount_type}\n"
                   f"⏰ <b>Действует:</b> {expires_in_hours} часов\n"
                   f"🆔 <b>ID:</b> {qr_code['qr_id']}\n\n"
                   f"Покажите этот QR-код партнеру для получения скидки!",
            parse_mode="HTML"
        )
        
        # Show menu
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Мои QR-коды", callback_data="qr_my_codes")],
            [InlineKeyboardButton(text="➕ Создать еще", callback_data="qr_create")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        
        await message.answer(
            "Что хотите сделать дальше?",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error creating QR code: {e}")
        await message.answer(
            "❌ Ошибка при создании QR-кода. Попробуйте позже.",
            reply_markup=_back_to_main_menu_keyboard()
        )


@router.callback_query(F.data == "qr_stats")
async def show_qr_stats(callback: CallbackQuery, state: FSMContext):
    """Show QR code statistics"""
    try:
        await callback.answer()
        
        db = next(get_db())
        qr_service = QRCodeService(db)
        user_id = callback.from_user.id
        
        stats = await qr_service.get_qr_code_stats(user_id)
        
        text = "📊 <b>Статистика QR-кодов</b>\n\n"
        text += f"🎫 Всего создано: {stats['total_codes']}\n"
        text += f"✅ Использовано: {stats['used_codes']}\n"
        text += f"⏰ Активных: {stats['active_codes']}\n"
        text += f"❌ Просроченных: {stats['expired_codes']}\n"
        text += f"📈 Процент использования: {stats['usage_rate']:.1f}%\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Мои QR-коды", callback_data="qr_my_codes")],
            [InlineKeyboardButton(text="➕ Создать QR-код", callback_data="qr_create")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error showing QR stats: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при загрузке статистики. Попробуйте позже.",
            reply_markup=_back_to_main_menu_keyboard()
        )


@router.callback_query(F.data == "qr_help")
async def show_qr_help(callback: CallbackQuery, state: FSMContext):
    """Show QR code help"""
    try:
        await callback.answer()
        
        text = "❓ <b>Помощь по QR-кодам</b>\n\n"
        text += "🎫 <b>Что такое QR-коды?</b>\n"
        text += "QR-коды - это способ получить скидки в партнерских заведениях.\n\n"
        text += "💰 <b>Типы скидок:</b>\n"
        text += "• Баллы лояльности - скидка в баллах\n"
        text += "• Процент скидки - скидка в процентах\n"
        text += "• Фиксированная сумма - скидка в рублях\n\n"
        text += "⏰ <b>Срок действия:</b>\n"
        text += "QR-коды действуют ограниченное время (1 час - 7 дней)\n\n"
        text += "🔍 <b>Как использовать:</b>\n"
        text += "1. Создайте QR-код\n"
        text += "2. Покажите его партнеру\n"
        text += "3. Получите скидку!\n\n"
        text += "📊 <b>Статистика:</b>\n"
        text += "Отслеживайте использование ваших QR-кодов"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Мои QR-коды", callback_data="qr_my_codes")],
            [InlineKeyboardButton(text="➕ Создать QR-код", callback_data="qr_create")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error showing QR help: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при загрузке справки. Попробуйте позже.",
            reply_markup=_back_to_main_menu_keyboard()
        )
