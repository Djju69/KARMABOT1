"""
Обработчики для многоуровневой реферальной системы
"""
import logging
from typing import Dict, Any, List
from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.services.multilevel_referral_service import multilevel_referral_service
from core.services.referral_service import referral_service
from core.utils.locales_v2 import get_text
from core.keyboards.restaurant_keyboards import select_restoran
from core.logger import get_logger

logger = get_logger(__name__)
router = Router(name="referral_handlers")

@router.message(F.text.in_(["Пригласить друзей", "Invite friends", "Mời bạn bè", "친구 초대"]))
async def show_invite_menu(message: Message, state: FSMContext):
    """Внутреннее меню "Пригласить друзей" (ровно 3 пункта)"""
    lang = (await state.get_data()).get("lang", "ru")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("invite.my_link", lang) or "🔗 Моя ссылка", callback_data="invite_my_link")],
        [InlineKeyboardButton(text=get_text("invite.invited", lang) or "📋 Приглашённые", callback_data="invite_invited")],
        [InlineKeyboardButton(text=get_text("invite.earnings", lang) or "💵 Доходы", callback_data="invite_earnings")],
    ])
    await message.answer(get_text("menu.invite_friends", lang) or "Пригласить друзей", reply_markup=kb)

@router.callback_query(F.data == "invite_my_link")
async def invite_my_link(cb: CallbackQuery, state: FSMContext):
    lang = (await state.get_data()).get("lang", "ru")
    try:
        link = await referral_service.get_referral_link(cb.from_user.id)
    except Exception:
        link = "soon://ref"
    text = (get_text("invite.my_link", lang) or "🔗 Моя ссылка") + f"\n\n`{link}`"
    await cb.message.edit_text(text, parse_mode="Markdown")
    await cb.answer()

@router.callback_query(F.data == "invite_invited")
async def invite_invited(cb: CallbackQuery, state: FSMContext):
    lang = (await state.get_data()).get("lang", "ru")
    # Заглушка с безопасной выдачей
    text = get_text("invite.invited", lang) or "📋 Приглашённые"
    text += "\n\nСкоро. Пагинация >10 поддерживается."
    await cb.message.edit_text(text)
    await cb.answer()

@router.callback_query(F.data == "invite_earnings")
async def invite_earnings(cb: CallbackQuery, state: FSMContext):
    lang = (await state.get_data()).get("lang", "ru")
    # Заглушка с безопасной выдачей
    text = get_text("invite.earnings", lang) or "💵 Доходы"
    text += "\n\nСкоро. Диапазоны: все / 30д / 7д / сегодня."
    await cb.message.edit_text(text)
    await cb.answer()
async def show_referral_program(message: Message, state: FSMContext):
    """Показ реферальной программы"""
    try:
        user_id = message.from_user.id
        lang = (await state.get_data()).get("lang", "ru")
        
        # Получаем статистику рефералов
        stats = await multilevel_referral_service.get_referral_stats(user_id)
        
        # Получаем реферальную ссылку
        referral_link = await referral_service.get_referral_link(user_id)
        
        text = get_text(lang, "referral_program_title") or "👥 Реферальная программа"
        text += f"\n\n📊 Ваша статистика:"
        text += f"\n• Рефералов 1-го уровня: {stats['level_1']['count']}"
        text += f"\n• Рефералов 2-го уровня: {stats['level_2']['count']}"
        text += f"\n• Рефералов 3-го уровня: {stats['level_3']['count']}"
        text += f"\n• Всего заработано: {stats['total_earnings']:.2f} руб."
        
        text += f"\n\n🔗 Ваша реферальная ссылка:"
        text += f"\n`{referral_link}`"
        
        text += f"\n\n💰 Система бонусов:"
        text += f"\n• 1-й уровень: 50% от покупок"
        text += f"\n• 2-й уровень: 30% от покупок"
        text += f"\n• 3-й уровень: 20% от покупок"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text(lang, "referral_tree") or "🌳 Дерево рефералов",
                    callback_data="show_referral_tree"
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text(lang, "referral_history") or "📈 История доходов",
                    callback_data="show_referral_history"
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text(lang, "back_to_main") or "◀️ Главное меню",
                    callback_data="back_to_main"
                )
            ]
        ])
        
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка показа реферальной программы: {e}")
        await message.answer("❌ Ошибка загрузки реферальной программы")

@router.callback_query(F.data == "show_referral_tree")
async def show_referral_tree(callback: CallbackQuery, state: FSMContext):
    """Показ дерева рефералов"""
    try:
        user_id = callback.from_user.id
        lang = (await state.get_data()).get("lang", "ru")
        
        # Получаем дерево рефералов
        tree = await multilevel_referral_service.get_referral_tree(user_id)
        
        text = get_text(lang, "referral_tree_title") or "🌳 Дерево рефералов"
        text += f"\n\n📊 Общая статистика:"
        text += f"\n• Всего рефералов: {tree['total_referrals']}"
        text += f"\n• Общие доходы: {tree['total_earnings']:.2f} руб."
        
        # Показываем по уровням
        for level in sorted(tree['levels'].keys()):
            level_data = tree['levels'][level]
            text += f"\n\n🔸 {level}-й уровень:"
            text += f"\n• Количество: {level_data['count']}"
            text += f"\n• Доходы: {level_data['total_earnings']:.2f} руб."
            
            # Показываем последних 3 рефералов
            recent_referrals = level_data['referrals'][:3]
            if recent_referrals:
                text += f"\n• Последние рефералы:"
                for ref in recent_referrals:
                    text += f"\n  - ID: {ref['user_id']} (заработано: {ref['total_earnings']:.2f} руб.)"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text(lang, "back_to_referrals") or "◀️ К рефералам",
                    callback_data="back_to_referrals"
                )
            ]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка показа дерева рефералов: {e}")
        await callback.answer("❌ Ошибка загрузки дерева рефералов")

@router.callback_query(F.data == "show_referral_history")
async def show_referral_history(callback: CallbackQuery, state: FSMContext):
    """Показ истории доходов от рефералов"""
    try:
        user_id = callback.from_user.id
        lang = (await state.get_data()).get("lang", "ru")
        
        async with get_db() as db:
            from core.models.referral_tree import ReferralBonus
            from sqlalchemy import select, desc
            
            # Получаем последние 10 бонусов
            result = await db.execute(
                select(ReferralBonus)
                .where(ReferralBonus.referrer_id == user_id)
                .order_by(desc(ReferralBonus.created_at))
                .limit(10)
            )
            bonuses = result.scalars().all()
        
        text = get_text(lang, "referral_history_title") or "📈 История доходов"
        
        if not bonuses:
            text += "\n\n📭 Пока нет доходов от рефералов"
        else:
            text += f"\n\n📊 Последние {len(bonuses)} начислений:"
            
            for bonus in bonuses:
                text += f"\n\n🔸 {bonus.level}-й уровень:"
                text += f"\n• Сумма: {bonus.bonus_amount:.2f} руб."
                text += f"\n• От реферала: {bonus.referred_id}"
                text += f"\n• Дата: {bonus.created_at.strftime('%d.%m.%Y %H:%M')}"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text(lang, "back_to_referrals") or "◀️ К рефералам",
                    callback_data="back_to_referrals"
                )
            ]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка показа истории рефералов: {e}")
        await callback.answer("❌ Ошибка загрузки истории")

@router.callback_query(F.data == "back_to_referrals")
async def back_to_referrals(callback: CallbackQuery, state: FSMContext):
    """Возврат к реферальной программе"""
    await show_referral_program(callback.message, state)
    await callback.answer()

@router.message(F.text.startswith("/invite"))
async def process_invite_command(message: Message, state: FSMContext):
    """Обработка команды /invite для регистрации по реферальной ссылке"""
    try:
        user_id = message.from_user.id
        lang = (await state.get_data()).get("lang", "ru")
        
        # Извлекаем ID реферера из команды
        command_parts = message.text.split()
        if len(command_parts) < 2:
            await message.answer("❌ Неверная ссылка приглашения")
            return
        
        try:
            referrer_id = int(command_parts[1])
        except ValueError:
            await message.answer("❌ Неверная ссылка приглашения")
            return
        
        # Проверяем, что пользователь не приглашает сам себя
        if user_id == referrer_id:
            await message.answer("❌ Вы не можете пригласить сами себя")
            return
        
        # Добавляем реферала в систему
        result = await multilevel_referral_service.add_referral(user_id, referrer_id)
        
        text = get_text(lang, "referral_registration_success") or "✅ Регистрация по реферальной ссылке успешна!"
        text += f"\n\n🎉 Вы стали рефералом {result['level']}-го уровня"
        text += f"\n👤 Ваш реферер: {referrer_id}"
        
        # Показываем главное меню
        keyboard = select_restoran(lang)
        await message.answer(text, reply_markup=keyboard)
        
        # Уведомляем реферера
        try:
            await message.bot.send_message(
                chat_id=referrer_id,
                text=f"🎉 У вас новый реферал!\n👤 Пользователь {user_id} присоединился к вашей команде"
            )
        except Exception as e:
            logger.warning(f"Не удалось уведомить реферера {referrer_id}: {e}")
        
    except Exception as e:
        logger.error(f"Ошибка обработки команды /invite: {e}")
        await message.answer("❌ Ошибка регистрации по реферальной ссылке")

@router.message(F.text == "🔗 Моя реферальная ссылка")
async def show_my_referral_link(message: Message, state: FSMContext):
    """Показ реферальной ссылки пользователя"""
    try:
        user_id = message.from_user.id
        lang = (await state.get_data()).get("lang", "ru")
        
        # Получаем реферальную ссылку
        referral_link = await referral_service.get_referral_link(user_id)
        
        text = get_text(lang, "my_referral_link") or "🔗 Ваша реферальная ссылка"
        text += f"\n\n`{referral_link}`"
        text += f"\n\n📋 Скопируйте ссылку и поделитесь с друзьями!"
        text += f"\n💰 За каждого реферала вы получите бонусы от их покупок"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text(lang, "share_link") or "📤 Поделиться",
                    url=f"https://t.me/share/url?url={referral_link}&text=Присоединяйся%20к%20KARMABOT1!"
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text(lang, "back_to_main") or "◀️ Главное меню",
                    callback_data="back_to_main"
                )
            ]
        ])
        
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка показа реферальной ссылки: {e}")
        await message.answer("❌ Ошибка загрузки реферальной ссылки")
