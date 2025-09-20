"""
Enhanced Partner Onboarding Workflow
Complete partner registration and verification system
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core.settings import settings
from core.utils.locales_v2 import get_text, translations
from core.services import profile_service
from core.database.db_v2 import db_v2
from core.logger import get_logger

logger = get_logger(__name__)

router = Router(name=__name__)

class PartnerOnboardingStates(StatesGroup):
    waiting_for_business_type = State()
    waiting_for_business_name = State()
    waiting_for_description = State()
    waiting_for_contact_info = State()
    waiting_for_location = State()
    waiting_for_verification_documents = State()
    waiting_for_terms_acceptance = State()
    verification_pending = State()
    verification_approved = State()
    verification_rejected = State()

class PartnerOnboardingService:
    """Service for partner onboarding workflow"""
    
    @staticmethod
    async def start_onboarding(message: Message, state: FSMContext):
        """Start partner onboarding process"""
        try:
            user_id = message.from_user.id
            
            # Check if user is already a partner
            existing_partner = await db_v2.get_partner(user_id)
            if existing_partner:
                await message.answer(
                    "✅ Вы уже зарегистрированы как партнер!\n\n"
                    "Используйте /partner для входа в кабинет партнера."
                )
                return
            
            # Start onboarding flow
            await state.set_state(PartnerOnboardingStates.waiting_for_business_type)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🍽️ Ресторан/Кафе",
                        callback_data="partner_type:restaurant"
                    ),
                    InlineKeyboardButton(
                        text="🛍️ Магазин",
                        callback_data="partner_type:shop"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🏨 Отель",
                        callback_data="partner_type:hotel"
                    ),
                    InlineKeyboardButton(
                        text="💆 Спа/Красота",
                        callback_data="partner_type:spa"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🚗 Транспорт",
                        callback_data="partner_type:transport"
                    ),
                    InlineKeyboardButton(
                        text="🎯 Развлечения",
                        callback_data="partner_type:entertainment"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🏥 Здоровье",
                        callback_data="partner_type:health"
                    ),
                    InlineKeyboardButton(
                        text="📚 Образование",
                        callback_data="partner_type:education"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отмена",
                        callback_data="partner_onboarding:cancel"
                    )
                ]
            ])
            
            await message.answer(
                "🏪 **Добро пожаловать в программу партнерства!**\n\n"
                "Для начала регистрации выберите тип вашего бизнеса:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error starting partner onboarding: {e}")
            await message.answer("❌ Произошла ошибка. Попробуйте позже.")
    
    @staticmethod
    async def process_business_type(callback: CallbackQuery, state: FSMContext):
        """Process business type selection"""
        try:
            business_type = callback.data.split(":")[1]
            await state.update_data(business_type=business_type)
            await state.set_state(PartnerOnboardingStates.waiting_for_business_name)
            
            await callback.message.edit_text(
                f"✅ Тип бизнеса: {business_type}\n\n"
                "📝 Теперь введите название вашего заведения:\n\n"
                "Пример: \"Ресторан \"Золотой дракон\"\""
            )
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error processing business type: {e}")
            await callback.answer("❌ Произошла ошибка")
    
    @staticmethod
    async def process_business_name(message: Message, state: FSMContext):
        """Process business name input"""
        try:
            business_name = message.text.strip()
            
            if len(business_name) < 3:
                await message.answer("❌ Название должно содержать минимум 3 символа")
                return
            
            await state.update_data(business_name=business_name)
            await state.set_state(PartnerOnboardingStates.waiting_for_description)
            
            await message.answer(
                f"✅ Название: {business_name}\n\n"
                "📝 Опишите ваше заведение (минимум 20 символов):\n\n"
                "Расскажите о ваших услугах, особенностях, атмосфере..."
            )
            
        except Exception as e:
            logger.error(f"Error processing business name: {e}")
            await message.answer("❌ Произошла ошибка")
    
    @staticmethod
    async def process_description(message: Message, state: FSMContext):
        """Process business description"""
        try:
            description = message.text.strip()
            
            if len(description) < 20:
                await message.answer("❌ Описание должно содержать минимум 20 символов")
                return
            
            await state.update_data(description=description)
            await state.set_state(PartnerOnboardingStates.waiting_for_contact_info)
            
            await message.answer(
                f"✅ Описание сохранено\n\n"
                "📞 Введите контактную информацию:\n\n"
                "Формат:\n"
                "📞 Телефон: +7 (XXX) XXX-XX-XX\n"
                "📧 Email: example@domain.com\n"
                "🌐 Сайт: https://example.com (необязательно)"
            )
            
        except Exception as e:
            logger.error(f"Error processing description: {e}")
            await message.answer("❌ Произошла ошибка")
    
    @staticmethod
    async def process_contact_info(message: Message, state: FSMContext):
        """Process contact information"""
        try:
            contact_info = message.text.strip()
            
            # Basic validation
            if not any(char.isdigit() for char in contact_info):
                await message.answer("❌ Контактная информация должна содержать телефон")
                return
            
            await state.update_data(contact_info=contact_info)
            await state.set_state(PartnerOnboardingStates.waiting_for_location)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📍 Отправить геолокацию",
                        callback_data="partner_location:send"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="✏️ Ввести адрес вручную",
                        callback_data="partner_location:manual"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отмена",
                        callback_data="partner_onboarding:cancel"
                    )
                ]
            ])
            
            await message.answer(
                f"✅ Контакты сохранены\n\n"
                "📍 Укажите местоположение вашего заведения:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error processing contact info: {e}")
            await message.answer("❌ Произошла ошибка")
    
    @staticmethod
    async def process_location_manual(callback: CallbackQuery, state: FSMContext):
        """Process manual location input"""
        try:
            await state.set_state(PartnerOnboardingStates.waiting_for_location)
            
            await callback.message.edit_text(
                "📍 Введите адрес вашего заведения:\n\n"
                "Формат: Город, Улица, Дом, Офис/Этаж\n\n"
                "Пример: Нячанг, ул. Транг Фу, 123, офис 5"
            )
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error processing manual location: {e}")
            await callback.answer("❌ Произошла ошибка")
    
    @staticmethod
    async def process_location_text(message: Message, state: FSMContext):
        """Process location text input"""
        try:
            location = message.text.strip()
            
            if len(location) < 10:
                await message.answer("❌ Адрес должен содержать минимум 10 символов")
                return
            
            await state.update_data(location=location)
            await state.set_state(PartnerOnboardingStates.waiting_for_verification_documents)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📄 Загрузить документы",
                        callback_data="partner_docs:upload"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⏭️ Пропустить (позже)",
                        callback_data="partner_docs:skip"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отмена",
                        callback_data="partner_onboarding:cancel"
                    )
                ]
            ])
            
            await message.answer(
                f"✅ Адрес: {location}\n\n"
                "📄 Для верификации загрузите документы:\n\n"
                "• Справка о регистрации бизнеса\n"
                "• Лицензия (если требуется)\n"
                "• Фото заведения\n\n"
                "Или пропустите этот шаг и загрузите позже:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Error processing location text: {e}")
            await message.answer("❌ Произошла ошибка")
    
    @staticmethod
    async def process_documents_skip(callback: CallbackQuery, state: FSMContext):
        """Skip document upload"""
        try:
            await state.update_data(verification_documents="pending")
            await state.set_state(PartnerOnboardingStates.waiting_for_terms_acceptance)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Принимаю условия",
                        callback_data="partner_terms:accept"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📄 Прочитать условия",
                        callback_data="partner_terms:read"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отмена",
                        callback_data="partner_onboarding:cancel"
                    )
                ]
            ])
            
            await callback.message.edit_text(
                "📋 **Условия партнерства**\n\n"
                "1. Вы обязуетесь предоставлять качественные услуги\n"
                "2. Соблюдать правила платформы\n"
                "3. Предоставлять актуальную информацию\n"
                "4. Отвечать на отзывы клиентов\n\n"
                "Принимаете ли вы условия партнерства?",
                reply_markup=keyboard
            )
            
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error skipping documents: {e}")
            await callback.answer("❌ Произошла ошибка")
    
    @staticmethod
    async def process_terms_acceptance(callback: CallbackQuery, state: FSMContext):
        """Process terms acceptance"""
        try:
            await state.update_data(terms_accepted=True, accepted_at=datetime.utcnow())
            
            # Complete onboarding
            data = await state.get_data()
            await PartnerOnboardingService._create_partner_profile(callback.message, data)
            
            await callback.message.edit_text(
                "🎉 **Поздравляем!**\n\n"
                "Вы успешно зарегистрированы как партнер!\n\n"
                "📋 Ваша заявка отправлена на модерацию.\n"
                "⏰ Ожидайте подтверждения в течение 24 часов.\n\n"
                "📱 Вы получите уведомление о статусе заявки."
            )
            
            await state.clear()
            await callback.answer()
            
        except Exception as e:
            logger.error(f"Error processing terms acceptance: {e}")
            await callback.answer("❌ Произошла ошибка")
    
    @staticmethod
    async def _create_partner_profile(message: Message, data: Dict[str, Any]):
        """Create partner profile in database"""
        try:
            user_id = message.from_user.id
            full_name = message.from_user.full_name or "Unknown"
            
            # Create partner record
            partner_data = {
                "user_id": user_id,
                "full_name": full_name,
                "business_type": data.get("business_type"),
                "business_name": data.get("business_name"),
                "description": data.get("description"),
                "contact_info": data.get("contact_info"),
                "location": data.get("location"),
                "verification_status": "pending",
                "terms_accepted": data.get("terms_accepted", False),
                "terms_accepted_at": data.get("accepted_at"),
                "created_at": datetime.utcnow()
            }
            
            # Save to database
            partner = await db_v2.create_partner(partner_data)
            
            # Log the registration
            logger.info(f"Partner registered: user_id={user_id}, partner_id={partner.id}")
            
            return partner
            
        except Exception as e:
            logger.error(f"Error creating partner profile: {e}")
            raise

# Command handlers
@router.message(Command("become_partner"))
async def start_partner_onboarding(message: Message, state: FSMContext):
    """Start partner onboarding process"""
    await PartnerOnboardingService.start_onboarding(message, state)

@router.message(F.text.in_(["➕ Стать партнером", "➕ Become Partner", "➕ Trở thành đối tác", "➕ 파트너 되기"]))
async def start_partner_onboarding_button(message: Message, state: FSMContext):
    """Start partner onboarding via button"""
    await PartnerOnboardingService.start_onboarding(message, state)

# Callback handlers
@router.callback_query(F.data.startswith("partner_type:"))
async def handle_business_type(callback: CallbackQuery, state: FSMContext):
    """Handle business type selection"""
    await PartnerOnboardingService.process_business_type(callback, state)

@router.callback_query(F.data.startswith("partner_location:"))
async def handle_location_option(callback: CallbackQuery, state: FSMContext):
    """Handle location option selection"""
    action = callback.data.split(":")[1]
    
    if action == "manual":
        await PartnerOnboardingService.process_location_manual(callback, state)
    elif action == "send":
        await callback.message.edit_text(
            "📍 Отправьте геолокацию вашего заведения\n\n"
            "Нажмите на скрепку 📎 → Местоположение → Отправить"
        )
        await callback.answer()

@router.callback_query(F.data.startswith("partner_docs:"))
async def handle_documents_option(callback: CallbackQuery, state: FSMContext):
    """Handle document upload option"""
    action = callback.data.split(":")[1]
    
    if action == "skip":
        await PartnerOnboardingService.process_documents_skip(callback, state)
    elif action == "upload":
        await callback.message.edit_text(
            "📄 Загрузите документы для верификации:\n\n"
            "• Справка о регистрации бизнеса\n"
            "• Лицензия (если требуется)\n"
            "• Фото заведения\n\n"
            "Отправьте файлы по одному"
        )
        await callback.answer()

@router.callback_query(F.data.startswith("partner_terms:"))
async def handle_terms_option(callback: CallbackQuery, state: FSMContext):
    """Handle terms option"""
    action = callback.data.split(":")[1]
    
    if action == "accept":
        await PartnerOnboardingService.process_terms_acceptance(callback, state)
    elif action == "read":
        await callback.message.edit_text(
            "📄 **Полные условия партнерства**\n\n"
            "1. **Качество услуг**: Вы обязуетесь предоставлять качественные услуги клиентам\n"
            "2. **Соблюдение правил**: Соблюдать правила и политики платформы\n"
            "3. **Актуальная информация**: Поддерживать актуальную информацию о заведении\n"
            "4. **Отзывы клиентов**: Отвечать на отзывы и комментарии клиентов\n"
            "5. **Конфиденциальность**: Не разглашать конфиденциальную информацию\n"
            "6. **Ответственность**: Нести ответственность за предоставляемые услуги\n\n"
            "Принимаете ли вы эти условия?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Принимаю",
                        callback_data="partner_terms:accept"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отмена",
                        callback_data="partner_onboarding:cancel"
                    )
                ]
            ])
        )
        await callback.answer()

@router.callback_query(F.data == "partner_onboarding:cancel")
async def cancel_onboarding(callback: CallbackQuery, state: FSMContext):
    """Cancel onboarding process"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Регистрация партнера отменена.\n\n"
        "Вы можете начать регистрацию позже командой /become_partner"
    )
    await callback.answer()

# State handlers
@router.message(PartnerOnboardingStates.waiting_for_business_name)
async def handle_business_name(message: Message, state: FSMContext):
    """Handle business name input"""
    await PartnerOnboardingService.process_business_name(message, state)

@router.message(PartnerOnboardingStates.waiting_for_description)
async def handle_description(message: Message, state: FSMContext):
    """Handle description input"""
    await PartnerOnboardingService.process_description(message, state)

@router.message(PartnerOnboardingStates.waiting_for_contact_info)
async def handle_contact_info(message: Message, state: FSMContext):
    """Handle contact info input"""
    await PartnerOnboardingService.process_contact_info(message, state)

@router.message(PartnerOnboardingStates.waiting_for_location)
async def handle_location_text(message: Message, state: FSMContext):
    """Handle location text input"""
    await PartnerOnboardingService.process_location_text(message, state)

# Location handler
@router.message(F.location)
async def handle_location(message: Message, state: FSMContext):
    """Handle location message"""
    try:
        current_state = await state.get_state()
        if current_state == PartnerOnboardingStates.waiting_for_location:
            location = f"Lat: {message.location.latitude}, Lon: {message.location.longitude}"
            await state.update_data(location=location)
            await state.set_state(PartnerOnboardingStates.waiting_for_verification_documents)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="📄 Загрузить документы",
                        callback_data="partner_docs:upload"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⏭️ Пропустить (позже)",
                        callback_data="partner_docs:skip"
                    )
                ]
            ])
            
            await message.answer(
                f"✅ Геолокация получена\n\n"
                "📄 Для верификации загрузите документы:",
                reply_markup=keyboard
            )
            
    except Exception as e:
        logger.error(f"Error handling location: {e}")
        await message.answer("❌ Произошла ошибка при обработке геолокации")
