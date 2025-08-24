"""
Partner FSM handlers for adding cards
Behind FEATURE_PARTNER_FSM flag for safe deployment
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
import logging

from ..settings import settings
from ..database.db_v2 import db_v2, Card
from ..utils.locales_v2 import translations

logger = logging.getLogger(__name__)

# FSM States for adding cards
class AddCardStates(StatesGroup):
    choose_category = State()
    enter_title = State()
    enter_description = State()
    enter_contact = State()
    enter_address = State()
    upload_photo = State()
    enter_discount = State()
    preview_card = State()
    confirm_submit = State()

# Router for partner handlers
partner_router = Router()

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard with cancel option"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отменить")]],
        resize_keyboard=True
    )

def get_skip_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard with skip and cancel options"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏭️ Пропустить")],
            [KeyboardButton(text="❌ Отменить")]
        ],
        resize_keyboard=True
    )

def get_categories_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard with categories"""
    categories = db_v2.get_categories()
    buttons = []
    
    for category in categories:
        buttons.append([InlineKeyboardButton(
            text=f"{category.emoji} {category.name}",
            callback_data=f"partner_cat:{category.slug}"
        )])
    
    buttons.append([InlineKeyboardButton(text="❌ Отменить", callback_data="partner_cancel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_preview_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for card preview"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить на модерацию", callback_data="partner_submit")],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data="partner_edit")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="partner_cancel")]
    ])

def format_card_preview(card_data: dict, category_name: str) -> str:
    """Format card preview text"""
    text = f"📋 **Предпросмотр карточки**\n\n"
    text += f"📂 **Категория:** {category_name}\n"
    text += f"📝 **Название:** {card_data.get('title', 'Не указано')}\n"
    
    if card_data.get('description'):
        text += f"📄 **Описание:** {card_data['description']}\n"
    
    if card_data.get('contact'):
        text += f"📞 **Контакт:** {card_data['contact']}\n"
    
    if card_data.get('address'):
        text += f"📍 **Адрес:** {card_data['address']}\n"
    
    if card_data.get('discount_text'):
        text += f"🎫 **Скидка:** {card_data['discount_text']}\n"
    
    if card_data.get('photo_file_id'):
        text += f"📸 **Фото:** Прикреплено\n"
    
    text += f"\n💡 После отправки карточка попадет на модерацию."
    
    return text

# Command to start adding card
@partner_router.message(Command("add_card"))
async def start_add_card(message: Message, state: FSMContext):
    """Start adding new card (only if feature enabled)"""
    if not settings.features.partner_fsm:
        await message.answer("🚧 Функция добавления карточек временно недоступна.")
        return
    
    # Get or create partner
    partner = db_v2.get_or_create_partner(
        message.from_user.id,
        message.from_user.full_name
    )
    
    await state.update_data(partner_id=partner.id)
    await state.set_state(AddCardStates.choose_category)
    
    await message.answer(
        "🏪 **Добавление новой карточки**\n\n"
        "Выберите категорию для вашего заведения:",
        reply_markup=get_categories_keyboard()
    )

# Category selection
@partner_router.callback_query(F.data.startswith("partner_cat:"))
async def select_category(callback: CallbackQuery, state: FSMContext):
    """Handle category selection"""
    category_slug = callback.data.split(":")[1]
    category = db_v2.get_category_by_slug(category_slug)
    
    if not category:
        await callback.answer("❌ Категория не найдена")
        return
    
    await state.update_data(
        category_id=category.id,
        category_name=category.name
    )
    await state.set_state(AddCardStates.enter_title)
    
    await callback.message.edit_text(
        f"✅ Выбрана категория: **{category.name}**\n\n"
        f"📝 Теперь введите название вашего заведения:\n"
        f"*(например: \"Ресторан У Моря\")*",
        reply_markup=None
    )
    
    await callback.message.answer(
        "Введите название:",
        reply_markup=get_cancel_keyboard()
    )

# Title input
@partner_router.message(AddCardStates.enter_title, F.text)
async def enter_title(message: Message, state: FSMContext):
    """Handle title input"""
    if message.text == "❌ Отменить":
        await cancel_add_card(message, state)
        return
    # Edit mode: allow skipping title change
    data = await state.get_data()
    if message.text == "⏭️ Пропустить" and data.get('edit_card_id'):
        # Keep existing title, move next
        await state.set_state(AddCardStates.enter_description)
        await message.answer(
            f"📄 Теперь введите описание заведения (или Пропустить):",
            reply_markup=get_skip_keyboard()
        )
        return

    title = message.text.strip()
    if len(title) < 3:
        await message.answer("❌ Название слишком короткое. Минимум 3 символа.")
        return
    
    if len(title) > 100:
        await message.answer("❌ Название слишком длинное. Максимум 100 символов.")
        return
    
    await state.update_data(title=title)
    await state.set_state(AddCardStates.enter_description)
    
    await message.answer(
        f"✅ Название: **{title}**\n\n"
        f"📄 Теперь введите описание заведения:\n"
        f"*(расскажите о ваших услугах, особенностях, атмосфере)*",
        reply_markup=get_skip_keyboard()
    )

# Description input
@partner_router.message(AddCardStates.enter_description, F.text)
async def enter_description(message: Message, state: FSMContext):
    """Handle description input"""
    if message.text == "❌ Отменить":
        await cancel_add_card(message, state)
        return
    
    description = None
    if message.text != "⏭️ Пропустить":
        description = message.text.strip()
        if len(description) > 500:
            await message.answer("❌ Описание слишком длинное. Максимум 500 символов.")
            return
    
    await state.update_data(description=description)
    await state.set_state(AddCardStates.enter_contact)
    
    await message.answer(
        f"📞 Введите контактную информацию:\n"
        f"*(телефон, Telegram, WhatsApp, Instagram)*",
        reply_markup=get_skip_keyboard()
    )

# Contact input
@partner_router.message(AddCardStates.enter_contact, F.text)
async def enter_contact(message: Message, state: FSMContext):
    """Handle contact input"""
    if message.text == "❌ Отменить":
        await cancel_add_card(message, state)
        return
    
    contact = None
    if message.text != "⏭️ Пропустить":
        contact = message.text.strip()
        if len(contact) > 200:
            await message.answer("❌ Контакт слишком длинный. Максимум 200 символов.")
            return
    
    await state.update_data(contact=contact)
    await state.set_state(AddCardStates.enter_address)
    
    await message.answer(
        f"📍 Введите адрес заведения:\n"
        f"*(улица, район, ориентиры)*",
        reply_markup=get_skip_keyboard()
    )

# Address input
@partner_router.message(AddCardStates.enter_address, F.text)
async def enter_address(message: Message, state: FSMContext):
    """Handle address input"""
    if message.text == "❌ Отменить":
        await cancel_add_card(message, state)
        return
    
    address = None
    if message.text != "⏭️ Пропустить":
        address = message.text.strip()
        if len(address) > 300:
            await message.answer("❌ Адрес слишком длинный. Максимум 300 символов.")
            return
    
    await state.update_data(address=address)
    await state.set_state(AddCardStates.upload_photo)
    
    await message.answer(
        f"📸 Загрузите фото заведения:\n"
        f"*(интерьер, блюда, фасад)*",
        reply_markup=get_skip_keyboard()
    )

# Photo upload
@partner_router.message(AddCardStates.upload_photo, F.photo)
async def upload_photo(message: Message, state: FSMContext):
    """Handle photo upload"""
    photo_file_id = message.photo[-1].file_id  # Get largest photo
    
    await state.update_data(photo_file_id=photo_file_id)
    await state.set_state(AddCardStates.enter_discount)
    
    await message.answer(
        f"✅ Фото загружено!\n\n"
        f"🎫 Введите информацию о скидке:\n"
        f"*(например: \"10% на все меню\", \"Скидка 15% по QR-коду\")*",
        reply_markup=get_skip_keyboard()
    )

@partner_router.message(AddCardStates.upload_photo, F.text)
async def skip_photo(message: Message, state: FSMContext):
    """Handle photo skip"""
    if message.text == "❌ Отменить":
        await cancel_add_card(message, state)
        return
    
    if message.text == "⏭️ Пропустить":
        await state.set_state(AddCardStates.enter_discount)
        await message.answer(
            f"🎫 Введите информацию о скидке:\n"
            f"*(например: \"10% на все меню\", \"Скидка 15% по QR-коду\")*",
            reply_markup=get_skip_keyboard()
        )
    else:
        await message.answer("📸 Пожалуйста, загрузите фото или нажмите 'Пропустить'")

# Discount input
@partner_router.message(AddCardStates.enter_discount, F.text)
async def enter_discount(message: Message, state: FSMContext):
    """Handle discount input"""
    if message.text == "❌ Отменить":
        await cancel_add_card(message, state)
        return
    
    discount_text = None
    if message.text != "⏭️ Пропустить":
        discount_text = message.text.strip()
        if len(discount_text) > 100:
            await message.answer("❌ Описание скидки слишком длинное. Максимум 100 символов.")
            return
    
    await state.update_data(discount_text=discount_text)
    await state.set_state(AddCardStates.preview_card)
    
    # Show preview
    data = await state.get_data()
    preview_text = format_card_preview(data, data.get('category_name', ''))
    
    if data.get('photo_file_id'):
        await message.answer_photo(
            photo=data['photo_file_id'],
            caption=preview_text,
            reply_markup=get_preview_keyboard()
        )
    else:
        await message.answer(
            preview_text,
            reply_markup=get_preview_keyboard()
        )

# Submit card
@partner_router.callback_query(F.data == "partner_submit")
async def submit_card(callback: CallbackQuery, state: FSMContext):
    """Submit card for moderation"""
    data = await state.get_data()
    
    try:
        if data.get('edit_card_id'):
            # Update existing card (partial)
            card_id = int(data['edit_card_id'])
            fields = {
                'category_id': data.get('category_id'),
                'title': data.get('title'),
                'description': data.get('description'),
                'contact': data.get('contact'),
                'address': data.get('address'),
                'photo_file_id': data.get('photo_file_id'),
                'discount_text': data.get('discount_text'),
                'status': 'pending'  # re-moderate after edit
            }
            # Remove None to avoid overwriting with NULL unless explicitly skipped fields kept
            fields = {k: v for k, v in fields.items() if v is not None}
            db_v2.update_card_fields(card_id, **fields)

            await callback.message.edit_text(
                f"✅ **Изменения сохранены!**\n\n"
                f"📋 ID карточки: #{card_id}\n"
                f"⏳ Статус: Отправлена на повторную модерацию",
                reply_markup=None
            )
        else:
            # Create new card
            card = Card(
                id=None,
                partner_id=data['partner_id'],
                category_id=data['category_id'],
                title=data['title'],
                description=data.get('description'),
                contact=data.get('contact'),
                address=data.get('address'),
                photo_file_id=data.get('photo_file_id'),
                discount_text=data.get('discount_text'),
                status='pending'  # Waiting for moderation
            )
            
            card_id = db_v2.create_card(card)
            
            await callback.message.edit_text(
                f"✅ **Карточка отправлена на модерацию!**\n\n"
                f"📋 ID карточки: #{card_id}\n"
                f"⏳ Статус: На рассмотрении\n\n"
                f"💡 Вы получите уведомление, когда модератор рассмотрит вашу карточку.",
                reply_markup=None
            )
        
        # Notify admin about new card
        if settings.features.moderation:
            try:
                from aiogram import Bot
                bot = Bot.get_current()
                await bot.send_message(
                    settings.bots.admin_id,
                    f"🆕 **Новая карточка на модерацию**\n\n"
                    f"ID: #{card_id}\n"
                    f"Партнер: {callback.from_user.full_name}\n"
                    f"Категория: {data.get('category_name')}\n"
                    f"Название: {data['title']}\n\n"
                    f"Используйте /moderate для просмотра."
                )
            except Exception as e:
                logger.error(f"Failed to notify admin: {e}")
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Failed to create card: {e}")
        await callback.answer("❌ Ошибка при создании карточки. Попробуйте позже.")

# Cancel adding card
@partner_router.callback_query(F.data == "partner_cancel")
async def cancel_add_card_callback(callback: CallbackQuery, state: FSMContext):
    """Cancel adding card via callback"""
    await callback.message.edit_text(
        "❌ Добавление карточки отменено.",
        reply_markup=None
    )
    await state.clear()

async def cancel_add_card(message: Message, state: FSMContext):
    """Cancel adding card via message"""
    await message.answer("❌ Добавление карточки отменено.")
    await state.clear()

# Handle text messages in FSM states
@partner_router.message(AddCardStates.choose_category)
async def invalid_category_input(message: Message):
    """Handle invalid input in category selection"""
    await message.answer("❌ Пожалуйста, выберите категорию из списка выше.")

# Register router only if feature is enabled
def get_partner_router() -> Router:
    """Get partner router if feature is enabled"""
    if settings.features.partner_fsm:
        return partner_router
    return Router()  # Empty router if disabled
