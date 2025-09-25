"""
Enhanced category handlers with unified card rendering
Backward compatible with existing functionality
"""
from aiogram import Router, F, Bot as AioBot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram import Bot
import logging

from ..database.db_v2 import db_v2
from ..services.card_renderer import card_service
from ..utils.helpers import get_city_id_from_message
from ..keyboards.reply_v2 import (
    get_return_to_main_menu, 
    get_location_request_keyboard,
    get_categories_keyboard,
    get_transport_reply_keyboard,
    get_tours_reply_keyboard,
    get_spa_reply_keyboard,
    get_hotels_reply_keyboard,
    get_shops_reply_keyboard,
)
from ..keyboards.inline_v2 import (
    get_pagination_row,
    get_catalog_item_row,
    get_restaurant_filters_inline,
    get_categories_inline,
    get_catalog_card_actions,
)
from ..utils.locales_v2 import get_text, get_all_texts
from ..utils.telemetry import log_event
from ..settings import settings
from ..services.profile import profile_service
from ..services.performance_service import cached_query, monitor_performance
from typing import Optional

logger = logging.getLogger(__name__)

# Odoo helpers (pure functions, no side effects)
def _map_slug_to_odoo_category(slug: str) -> str:
    m = {
        'restaurants': 'restaurant',
        'spa': 'spa',
        'transport': 'transport',
        'hotels': 'hotel',
        'tours': 'tours',
        'shops': 'retail',
    }
    return m.get(slug, 'retail')

def _merge_cards_without_duplicates(local_cards: list[dict], remote_cards: list[dict]) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    merged: list[dict] = []
    for c in local_cards:
        key = (str(c.get('title') or '').strip().lower(), str(c.get('address') or '').strip().lower())
        seen.add(key)
        merged.append(c)
    for c in remote_cards:
        key = (str(c.get('title') or '').strip().lower(), str(c.get('address') or '').strip().lower())
        if key in seen:
            continue
        seen.add(key)
        merged.append(c)
    return merged

# Router for category handlers
category_router = Router(name="category_router")

async def show_categories_v2(message: Message, bot: Bot, lang: str):
    """Показывает Reply-клавиатуру с 6 категориями согласно ТЗ."""
    try:
        logger.warning(f"ДИАГНОСТИКА: Начало show_categories_v2 для пользователя {message.from_user.id}")
        await log_event("categories_menu_shown", user=message.from_user, lang=lang)
        
        # Получаем клавиатуру категорий
        keyboard = get_categories_keyboard(lang)
        logger.warning(f"ДИАГНОСТИКА: Получена клавиатура категорий для пользователя {message.from_user.id}")
        
        # Получаем текст сообщения
        text = get_text('choose_category', lang)
        if not text:
            text = "Выберите категорию:"  # Дефолтный текст, если перевод отсутствует
            logger.warning(f"ДИАГНОСТИКА: Не найден перевод 'choose_category' для языка {lang}, используем дефолтный текст")
        
        # Отправляем сообщение с клавиатурой
        logger.warning(f"ДИАГНОСТИКА: Отправляем сообщение с клавиатурой пользователю {message.from_user.id}")
        await message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        logger.warning(f"ДИАГНОСТИКА: Сообщение с клавиатурой успешно отправлено пользователю {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in show_categories_v2: {e}", exc_info=True)  # Добавляем exc_info=True для полного стектрейса
        try:
            await message.answer(
                get_text('catalog_error', lang) or "Произошла ошибка при загрузке категорий. Пожалуйста, попробуйте позже.",
                reply_markup=get_return_to_main_menu(lang),
                parse_mode="HTML"
            )
            logger.warning(f"ДИАГНОСТИКА: Отправлено сообщение об ошибке пользователю {message.from_user.id}")
        except Exception as e2:
            logger.error(f"КРИТИЧЕСКАЯ ОШИБКА: Не удалось отправить сообщение об ошибке: {e2}", exc_info=True)


# --- Этап 2: Интеграция с сервисом каталога ---

async def show_cards(user_id: int, category: str, sub_slug: Optional[str] = None, page: int = 1):
    """
    Загружает и отображает карточки по фильтрам (унифицированная точка входа):
    - category: обязательный slug ('restaurants'|'spa'|'transport'|'hotels'|'tours'|'shops')
    - sub_slug: подкатегория (например 'asia', 'group', 'bikes'), по умолчанию 'all'
    - page: номер страницы (>=1)
    """
    try:
        bot = AioBot.get_current()
    except Exception:
        # В редких случаях контекст отсутствует — не выполняем
        return
    try:
        lang = await profile_service.get_lang(user_id) or 'ru'
    except Exception:
        lang = 'ru'
    try:
        city_id = await profile_service.get_city_id(user_id)
    except Exception:
        city_id = None
    await show_catalog_page(
        bot=bot,
        chat_id=user_id,
        lang=lang,
        slug=category,
        sub_slug=(sub_slug or 'all'),
        page=max(1, int(page or 1)),
        city_id=city_id,
    )
@cached_query("catalog", ttl=300)
@monitor_performance("show_catalog_page")
async def show_catalog_page(bot: Bot, chat_id: int, lang: str, slug: str, sub_slug: str = "all", page: int = 1, city_id: int | None = None, message_id: int | None = None):
    """
    Универсальный обработчик для отображения страницы каталога с фильтрацией по sub_slug.
    """
    try:
        
        # 1. Получение данных и фильтрация
        try:
            # Используем существующий импорт log_event
            await log_event("catalog_query", slug=slug, sub_slug=sub_slug, page=page, city_id=city_id, lang=lang)
            logger.warning(f"🔧 LOG_EVENT SUCCESS")
        except Exception as e:
            logger.warning(f"🔧 LOG_EVENT ERROR: {e}")
            
        logger.info(f"ДИАГНОСТИКА: Запрашиваем карточки для категории '{slug}', статус 'published'")
        
        logger.warning(f"🔧 ABOUT TO QUERY DATABASE for {slug}")
        
        # Запрос к базе данных с обработкой ошибок соединения
        try:
            all_cards = db_v2.get_cards_by_category(slug, status='published', limit=100, sub_slug=sub_slug)
            logger.warning(f"🔧 DATABASE RETURNED: {len(all_cards) if all_cards else 0} cards")
            logger.info(f"ДИАГНОСТИКА: Получено {len(all_cards)} карточек для категории '{slug}' подкатегории '{sub_slug}'")
            
            # Фильтруем по подкатегории если нужно (теперь это делается в БД)
            if sub_slug and sub_slug != 'all' and all_cards:
                logger.info(f"ДИАГНОСТИКА: Фильтрация по подкатегории '{sub_slug}' выполнена в БД")
                
        except Exception as db_error:
            logger.error(f"❌ Database error in show_catalog_page: {db_error}")
            # Возвращаем пустой список при ошибке
            all_cards = []

        # Optionally enrich from Odoo without changing UI. Only when sub_slug == 'all'.
        if sub_slug == "all":
            try:
                from core.services import odoo_api
                if odoo_api.is_configured:
                    od = await odoo_api.get_cards_by_category(category=_map_slug_to_odoo_category(slug))
                    if od.get('success') and isinstance(od.get('cards'), list):
                        odoo_cards_raw = od['cards']
                        odoo_cards: list[dict] = []
                        for c in odoo_cards_raw:
                            try:
                                odoo_cards.append({
                                    'title': c.get('name') or 'Без названия',
                                    'description': c.get('description') or '',
                                    'address': c.get('address') or '',
                                    'contact': c.get('phone') or '',
                                    'discount_text': (f"Cashback {c.get('cashback_percent')}%" if c.get('cashback_percent') is not None else None),
                                    'photos_count': len(c.get('photos') or []),
                                })
                            except Exception:
                                continue
                        if odoo_cards:
                            all_cards = _merge_cards_without_duplicates(all_cards, odoo_cards)
            except Exception:
                # Do not fail catalog rendering if Odoo is unreachable
                pass
        if city_id is not None and all_cards and 'city_id' in all_cards[0]:
            all_cards = [c for c in all_cards if c.get('city_id') == city_id]
        if sub_slug != "all" and all_cards and 'sub_slug' in all_cards[0]:
             all_cards = [c for c in all_cards if str(c.get('sub_slug') or '').lower() == sub_slug]

        # 2. Пагинация
        per_page = 5
        total_items = len(all_cards)
        total_pages = max(1, (total_items + per_page - 1) // per_page)
        page = max(1, min(page, total_pages))
        cards_page = all_cards[(page - 1) * per_page:page * per_page]

        # 3. Рендеринг контента
        if not cards_page:
            text = get_text('catalog_empty_sub', lang)
            kb = None
            await bot.send_message(chat_id, text, reply_markup=kb)
        else:
            # Отправляем каждую карточку отдельным сообщением с индивидуальными кнопками
            header = f"{get_text('catalog_found', lang)}: {total_items} | {get_text('catalog_page', lang)}. {page}/{total_pages}"
            
            # Сначала отправляем заголовок
            await bot.send_message(chat_id, header)
            
            # Затем отправляем каждую карточку отдельно
            for i, card in enumerate(cards_page, 1):
                try:
                    card_text = card_service.render_card(card, lang)
                    text = f"**{i}.** {card_text}"
                    logger.warning(f"ДИАГНОСТИКА: Карточка {i} отрендерена успешно")
                    
                    # Кнопки для этой карточки
                    card_buttons = [
                        InlineKeyboardButton(text="📱 QR", callback_data=f"qr_create:{card.get('id')}"),
                        InlineKeyboardButton(text="📷 Фото", callback_data=f"gallery:{card.get('id')}"),
                        InlineKeyboardButton(text="⭐", callback_data=f"favorite:{card.get('id')}"),
                        InlineKeyboardButton(text="ℹ️", callback_data=f"act:view:{card.get('id')}")
                    ]
                    kb = InlineKeyboardMarkup(inline_keyboard=[card_buttons])
                    
                    await bot.send_message(chat_id, text, reply_markup=kb)
                    logger.warning(f"ДИАГНОСТИКА: Карточка {i} отправлена отдельным сообщением")
                    
                    # Небольшая задержка между сообщениями
                    import asyncio
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"ДИАГНОСТИКА: Ошибка рендеринга карточки {i}: {e}")
                    await bot.send_message(chat_id, f"**{i}.** Ошибка отображения карточки")
            
            # В конце отправляем пагинацию
            pagination_row = [get_pagination_row(slug, page, total_pages, sub_slug)]
            kb_pagination = InlineKeyboardMarkup(inline_keyboard=pagination_row)
            await bot.send_message(chat_id, "📄 Навигация по страницам:", reply_markup=kb_pagination)
        await log_event("catalog_rendered", slug=slug, sub_slug=sub_slug, page=page, total_items=total_items)

    except Exception as e:
        logger.error(f"show_catalog_page error for slug={slug}, sub_slug={sub_slug}: {e}")
        # Отправляем пользователю понятное сообщение об ошибке
        try:
            await bot.send_message(chat_id, "❌ Ошибка загрузки каталога. Попробуйте позже.")
        except Exception as send_error:
            logger.error(f"Failed to send error message: {send_error}")


async def on_restaurants(message: Message, bot: Bot, lang: str, city_id: int | None, state: FSMContext):
    # Показываем reply клавиатуру с фильтрами кухни
    from ..keyboards.reply_v2 import get_restaurants_reply_keyboard
    await log_event("category_open", user=message.from_user, slug="restaurants", lang=lang, city_id=city_id)
    await message.answer(
        text=get_text('restaurants_choose_cuisine', lang),
        reply_markup=get_restaurants_reply_keyboard(lang)
    )

async def on_spa(message: Message, bot: Bot, lang: str, city_id: int | None):
    """Show SPA submenu (salon/massage/sauna)."""
    await log_event("category_open", user=message.from_user, slug="spa", lang=lang, city_id=city_id)
    await message.answer(get_text('spa_choose', lang), reply_markup=get_spa_reply_keyboard(lang))

async def on_hotels(message: Message, bot: Bot, lang: str, city_id: int | None):
    """Show Hotels submenu (hotels/apartments)."""
    await log_event("category_open", user=message.from_user, slug="hotels", lang=lang, city_id=city_id)
    await message.answer(get_text('hotels_choose', lang), reply_markup=get_hotels_reply_keyboard(lang))

async def on_transport(message: Message, bot: Bot, lang: str):
    logger.warning(f"🔧 ON_TRANSPORT CALLED: user={message.from_user.id}, lang={lang}")
    await log_event("category_open", user=message.from_user, slug="transport", lang=lang)
    
    logger.warning(f"🔧 SENDING TRANSPORT KEYBOARD")
    await message.answer(get_text('transport_choose', lang), reply_markup=get_transport_reply_keyboard(lang))
    logger.warning(f"🔧 TRANSPORT KEYBOARD SENT")

async def on_tours(message: Message, bot: Bot, lang: str):
    await log_event("category_open", user=message.from_user, slug="tours", lang=lang)
    await message.answer(get_text('tours_choose', lang), reply_markup=get_tours_reply_keyboard(lang))


# --- Обработчики подменю --- 

async def on_transport_submenu(message: Message, bot: Bot, lang: str, city_id: int | None, state: FSMContext):
    """Обработчик для кнопок подменю 'Транспорт'."""
    logger.warning(f"🔧 ON_TRANSPORT_SUBMENU CALLED: user={message.from_user.id}, text={message.text}")
    
    sub_slug_map = {
        get_text('transport_bikes', lang): 'bikes',
        get_text('transport_cars', lang): 'cars',
        get_text('transport_bicycles', lang): 'bicycles'
    }
    sub_slug = sub_slug_map.get(message.text, "all")
    logger.warning(f"🔧 MAPPED TEXT '{message.text}' TO SUB_SLUG '{sub_slug}'")
    
    await log_event("category_sub_open", user=message.from_user, slug="transport", sub_slug=sub_slug, lang=lang, city_id=city_id)
    try:
        await state.update_data(category='transport', sub_slug=sub_slug, page=1)
        logger.warning(f"🔧 STATE UPDATED: category=transport, sub_slug={sub_slug}, page=1")
    except Exception as e:
        logger.warning(f"🔧 STATE UPDATE FAILED: {e}")
        pass
    
    logger.warning(f"🔧 CALLING show_catalog_page for transport/{sub_slug}")
    try:
        await show_catalog_page(bot, message.chat.id, lang, 'transport', sub_slug, page=1, city_id=city_id)
        logger.warning(f"🔧 FINISHED show_catalog_page for transport/{sub_slug}")
    except Exception as e:
        logger.error(f"🔧 SHOW_CATALOG_PAGE ERROR for transport/{sub_slug}: {e}")
        await message.answer(f"❌ Ошибка загрузки карточек: {e}")
    
    # УНИВЕРСАЛЬНАЯ ОЧИСТКА FSM ДЛЯ ВСЕХ КАТЕГОРИЙ - ПОСЛЕ показа карточек
    try:
        # Сохраняем важные данные (политика, язык)
        current_data = await state.get_data()
        policy_accepted = current_data.get('policy_accepted', False)
        lang = current_data.get('lang', 'ru')
        started = current_data.get('started', False)
        
        # Очищаем только состояние каталога, сохраняя политику
        await state.clear()
        
        # Восстанавливаем важные данные
        if policy_accepted:
            await state.update_data(policy_accepted=True, lang=lang, started=started)
            
        logger.warning(f"🔧 FSM STATE CLEARED for transport/{sub_slug} (policy preserved)")
    except Exception as e:
        logger.warning(f"🔧 FSM STATE CLEAR FAILED: {e}")
    
    logger.warning(f"🔧 FINISHED on_transport_submenu")

async def on_tours_submenu(message: Message, bot: Bot, lang: str, city_id: int | None, state: FSMContext):
    """Обработчик для кнопок подменю 'Экскурсии'."""
    sub_slug_map = {
        get_text('tours_group', lang): 'group',
        get_text('tours_private', lang): 'private'
    }
    sub_slug = sub_slug_map.get(message.text, "all")
    await log_event("category_sub_open", user=message.from_user, slug="tours", sub_slug=sub_slug, lang=lang, city_id=city_id)
    try:
        await state.update_data(category='tours', sub_slug=sub_slug, page=1)
    except Exception:
        pass
    
    try:
        await show_catalog_page(bot, message.chat.id, lang, 'tours', sub_slug, page=1, city_id=city_id)
    except Exception as e:
        logger.error(f"🔧 SHOW_CATALOG_PAGE ERROR for tours/{sub_slug}: {e}")
        await message.answer(f"❌ Ошибка загрузки карточек: {e}")
    
    # УНИВЕРСАЛЬНАЯ ОЧИСТКА FSM ДЛЯ ВСЕХ КАТЕГОРИЙ - ПОСЛЕ показа карточек
    try:
        # Сохраняем важные данные (политика, язык)
        current_data = await state.get_data()
        policy_accepted = current_data.get('policy_accepted', False)
        lang = current_data.get('lang', 'ru')
        started = current_data.get('started', False)
        
        # Очищаем только состояние каталога, сохраняя политику
        await state.clear()
        
        # Восстанавливаем важные данные
        if policy_accepted:
            await state.update_data(policy_accepted=True, lang=lang, started=started)
            
        logger.warning(f"🔧 FSM STATE CLEARED for tours/{sub_slug} (policy preserved)")
    except Exception as e:
        logger.warning(f"🔧 FSM STATE CLEAR FAILED: {e}")

async def on_spa_submenu(message: Message, bot: Bot, lang: str, city_id: int | None, state: FSMContext):
    """Обработчик для кнопок подменю 'SPA'."""
    sub_slug_map = {
        get_text('spa_salon', lang): 'salon',
        get_text('spa_massage', lang): 'massage',
        get_text('spa_sauna', lang): 'sauna',
    }
    sub_slug = sub_slug_map.get(message.text, "all")
    await log_event("category_sub_open", user=message.from_user, slug="spa", sub_slug=sub_slug, lang=lang, city_id=city_id)
    try:
        await state.update_data(category='spa', sub_slug=sub_slug, page=1)
    except Exception:
        pass
    
    try:
        await show_catalog_page(bot, message.chat.id, lang, 'spa', sub_slug, page=1, city_id=city_id)
    except Exception as e:
        logger.error(f"🔧 SHOW_CATALOG_PAGE ERROR for spa/{sub_slug}: {e}")
        await message.answer(f"❌ Ошибка загрузки карточек: {e}")
    
    # УНИВЕРСАЛЬНАЯ ОЧИСТКА FSM ДЛЯ ВСЕХ КАТЕГОРИЙ - ПОСЛЕ показа карточек
    try:
        # Сохраняем важные данные (политика, язык)
        current_data = await state.get_data()
        policy_accepted = current_data.get('policy_accepted', False)
        lang = current_data.get('lang', 'ru')
        started = current_data.get('started', False)
        
        # Очищаем только состояние каталога, сохраняя политику
        await state.clear()
        
        # Восстанавливаем важные данные
        if policy_accepted:
            await state.update_data(policy_accepted=True, lang=lang, started=started)
            
        logger.warning(f"🔧 FSM STATE CLEARED for spa/{sub_slug} (policy preserved)")
    except Exception as e:
        logger.warning(f"🔧 FSM STATE CLEAR FAILED: {e}")

async def on_hotels_submenu(message: Message, bot: Bot, lang: str, city_id: int | None, state: FSMContext):
    """Обработчик для кнопок подменю 'Отели'."""
    sub_slug_map = {
        get_text('hotels_hotels', lang): 'hotel',
        get_text('hotels_apartments', lang): 'apartments',
    }
    sub_slug = sub_slug_map.get(message.text, "all")
    await log_event("category_sub_open", user=message.from_user, slug="hotels", sub_slug=sub_slug, lang=lang, city_id=city_id)
    try:
        await state.update_data(category='hotels', sub_slug=sub_slug, page=1)
    except Exception:
        pass
    
    try:
        await show_catalog_page(bot, message.chat.id, lang, 'hotels', sub_slug, page=1, city_id=city_id)
    except Exception as e:
        logger.error(f"🔧 SHOW_CATALOG_PAGE ERROR for hotels/{sub_slug}: {e}")
        await message.answer(f"❌ Ошибка загрузки карточек: {e}")
    
    # УНИВЕРСАЛЬНАЯ ОЧИСТКА FSM ДЛЯ ВСЕХ КАТЕГОРИЙ - ПОСЛЕ показа карточек
    try:
        # Сохраняем важные данные (политика, язык)
        current_data = await state.get_data()
        policy_accepted = current_data.get('policy_accepted', False)
        lang = current_data.get('lang', 'ru')
        started = current_data.get('started', False)
        
        # Очищаем только состояние каталога, сохраняя политику
        await state.clear()
        
        # Восстанавливаем важные данные
        if policy_accepted:
            await state.update_data(policy_accepted=True, lang=lang, started=started)
            
        logger.warning(f"🔧 FSM STATE CLEARED for hotels/{sub_slug} (policy preserved)")
    except Exception as e:
        logger.warning(f"🔧 FSM STATE CLEAR FAILED: {e}")

async def on_shops(message: Message, bot: Bot, lang: str, city_id: int | None):
    """Show Shops & Services submenu (shops/services)."""
    logger.warning(f"🔧 ON_SHOPS CALLED: user={message.from_user.id}, lang={lang}, city_id={city_id}")
    await log_event("category_open", user=message.from_user, slug="shops", lang=lang, city_id=city_id)
    
    logger.warning(f"🔧 SENDING SHOPS KEYBOARD")
    await message.answer(get_text('shops_choose', lang), reply_markup=get_shops_reply_keyboard(lang))
    logger.warning(f"🔧 SHOPS KEYBOARD SENT")

async def on_shops_submenu(message: Message, bot: Bot, lang: str, city_id: int | None, state: FSMContext):
    """Обработчик для кнопок подменю 'Магазины и услуги'."""
    logger.warning(f"🔧 ON_SHOPS_SUBMENU CALLED: user={message.from_user.id}, text={message.text}")
    
    sub_slug_map = {
        get_text('shops_shops', lang): 'shops',
        get_text('shops_services', lang): 'services',
    }
    sub_slug = sub_slug_map.get(message.text, "all")
    logger.warning(f"🔧 MAPPED TEXT '{message.text}' TO SUB_SLUG '{sub_slug}'")
    
    await log_event("category_sub_open", user=message.from_user, slug="shops", sub_slug=sub_slug, lang=lang, city_id=city_id)
    try:
        await state.update_data(category='shops', sub_slug=sub_slug, page=1)
        logger.warning(f"🔧 STATE UPDATED: category=shops, sub_slug={sub_slug}, page=1")
    except Exception as e:
        logger.warning(f"🔧 STATE UPDATE FAILED: {e}")
        pass
    
    logger.warning(f"🔧 CALLING show_catalog_page for shops/{sub_slug}")
    try:
        await show_catalog_page(bot, message.chat.id, lang, 'shops', sub_slug, page=1, city_id=city_id)
        logger.warning(f"🔧 FINISHED show_catalog_page for shops/{sub_slug}")
    except Exception as e:
        logger.error(f"🔧 SHOW_CATALOG_PAGE ERROR for shops/{sub_slug}: {e}")
        await message.answer(f"❌ Ошибка загрузки карточек: {e}")
    
    # УНИВЕРСАЛЬНАЯ ОЧИСТКА FSM ДЛЯ ВСЕХ КАТЕГОРИЙ - ПОСЛЕ показа карточек
    try:
        # Сохраняем важные данные (политика, язык)
        current_data = await state.get_data()
        policy_accepted = current_data.get('policy_accepted', False)
        lang = current_data.get('lang', 'ru')
        started = current_data.get('started', False)
        
        # Очищаем только состояние каталога, сохраняя политику
        await state.clear()
        
        # Восстанавливаем важные данные
        if policy_accepted:
            await state.update_data(policy_accepted=True, lang=lang, started=started)
            
        logger.warning(f"🔧 FSM STATE CLEARED for shops/{sub_slug} (policy preserved)")
    except Exception as e:
        logger.warning(f"🔧 FSM STATE CLEAR FAILED: {e}")
    
    logger.warning(f"🔧 FINISHED on_shops_submenu")

async def show_nearest_v2(message: Message, bot: Bot, lang: str, city_id: int | None):
    """Enhanced nearest places handler"""
    t = get_all_texts(lang)
    
    city_hint = f" (город #{city_id})" if city_id else ""
    title = get_text('nearest_places_title', lang)
    request_text = get_text('nearest_places_request', lang)
    
    await message.answer(
        f"{title}**{city_hint}\n\n{request_text}",
        reply_markup=get_location_request_keyboard(lang)
    )

async def handle_location_v2(message: Message, bot: Bot, lang: str, city_id: int | None):
    """Enhanced location handler with actual nearby search"""
    
    try:
        latitude = message.location.latitude
        longitude = message.location.longitude
        
        logger.info(f"Received location: {latitude}, {longitude}")
        
        # Импортируем утилиты геопоиска
        from ..utils.geo import find_places_in_radius, format_distance
        
        # Получаем все опубликованные карточки с координатами
        all_cards = []
        categories = db_v2.get_categories(active_only=True)
        
        for category in categories:
            cards = db_v2.get_cards_by_category(category.slug, status='published', limit=50)
            # Добавляем информацию о категории к каждой карточке
            for card in cards:
                if isinstance(card, dict):
                    card['category_slug'] = category.slug
                    card['category_name'] = category.name
                else:
                    # Если card - это объект, конвертируем в dict
                    card_dict = dict(card) if hasattr(card, '__dict__') else card
                    card_dict['category_slug'] = category.slug
                    card_dict['category_name'] = category.name
                    card = card_dict
                all_cards.append(card)
        
        # Ищем ближайшие заведения в радиусе 5 км
        nearby_cards = find_places_in_radius(
            latitude=latitude,
            longitude=longitude,
            places=all_cards,
            radius_km=5.0,
            limit=10
        )
        
        if nearby_cards:
            response = get_text('nearest_places_found', lang) + "\n\n"
            
            # Группируем по категориям для лучшего отображения
            by_category = {}
            for card in nearby_cards:
                category = card.get('category_name', 'Другое')
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(card)
            
            # Отображаем результаты по категориям
            for category_name, cards in by_category.items():
                response += f"**{category_name}:**\n"
                for card in cards:
                    distance_str = format_distance(card['distance_km'])
                    name = card.get('name', 'Без названия')
                    address = card.get('address', 'Адрес не указан')
                    response += f"• {name} - {distance_str}\n"
                    if address:
                        response += f"  📍 {address}\n"
                response += "\n"
            
            # Добавляем информацию о точности поиска
            count_text = get_text('nearest_places_count', lang).format(count=len(nearby_cards))
            tip_text = get_text('nearest_places_tip', lang)
            response += f"{count_text}\n{tip_text}"
            
        else:
            response = get_text('nearest_places_none', lang) + "\n\n"
            response += get_text('nearest_places_none_desc', lang)
        
        await log_event("nearest_results_shown", user=message.from_user, count=len(nearby_cards), radius_km=5.0)
        await message.answer(response)
        
        # Return to main menu
        from ..windows.main_menu import main_menu_text
        await bot.send_message(
            chat_id=message.chat.id, 
            text=main_menu_text(lang), 
            reply_markup=get_return_to_main_menu(lang)
        )
        
    except Exception as e:
        logger.error(f"Error in handle_location_v2: {e}")
        error_text = get_text('location_error', lang)
        await message.answer(
            error_text,
            reply_markup=get_return_to_main_menu(lang)
        )

async def category_selected_v2(message: Message, bot: Bot, lang: str):
    """Enhanced category selection with unified card rendering"""
    category_text = message.text
    
    try:
        # Extract category name (remove emoji if present)
        category_name = category_text
        if ' ' in category_text:
            parts = category_text.split(' ', 1)
            if len(parts[0]) <= 2:  # Likely emoji
                category_name = parts[1]
        
        # Find category by name
        categories = db_v2.get_categories()
        matching_category = None
        
        for category in categories:
            if category.name == category_text or category.name == category_name:
                matching_category = category
                break
        
        if not matching_category:
            # Fallback to legacy handling for backward compatibility
            await handle_legacy_category(message, bot, category_text)
            return
        
        # Get cards for this category
        cards = db_v2.get_cards_by_category(
            matching_category.slug, 
            status='published', 
            limit=10
        )
        
        if cards:
            response = f"🗂️ **{matching_category.name}**\n\n"
            response += card_service.render_cards_list(cards, lang)
            
            # Add category-specific actions
            if matching_category.slug == 'restaurants':
                response += "\n\n💡 *Покажите QR-код перед заказом, чтобы получить скидку!*"
            
        else:
            response = get_text('category_empty', lang).format(category_name=matching_category.name) + "\n\n"
            
            if settings.features.partner_fsm:
                response += get_text('category_empty_partner', lang)
        
        await message.answer(response)
        
        # Return to main menu after showing results
        from ..windows.main_menu import main_menu_text
        await bot.send_message(
            chat_id=message.chat.id,
            text=main_menu_text(lang),
            reply_markup=get_return_to_main_menu(lang)
        )
        
    except Exception as e:
        logger.error(f"Error in category_selected_v2: {e}")
        await handle_legacy_category(message, bot, category_text)

# Обработчики для новых категорий (v2)
@category_router.message(F.text == get_text('category_restaurants', 'ru'))
async def handle_restaurants_v2(message: Message, bot: Bot, lang: str = 'ru'):
    """Обработчик категории Рестораны и кафе"""
    await on_restaurants(message, bot, lang, None)

@category_router.message(F.text == get_text('category_spa', 'ru'))
async def handle_spa_v2(message: Message, bot: Bot, lang: str = 'ru'):
    """Обработчик категории SPA и массаж"""
    await on_spa(message, bot, lang, None)

@category_router.message(F.text == get_text('category_transport', 'ru'))
async def handle_transport_v2(message: Message, bot: Bot, lang: str = 'ru'):
    """Обработчик категории Транспорт"""
    await on_transport(message, bot, lang, None)

@category_router.message(F.text == get_text('category_hotels', 'ru'))
async def handle_hotels_v2(message: Message, bot: Bot, lang: str = 'ru'):
    """Обработчик категории Отели"""
    await on_hotels(message, bot, lang, None)

@category_router.message(F.text == get_text('category_tours', 'ru'))
async def handle_tours_v2(message: Message, bot: Bot, lang: str = 'ru'):
    """Обработчик категории Экскурсии"""
    await on_tours(message, bot, lang, None)

@category_router.message(F.text == get_text('category_shops_services', 'ru'))
async def handle_shops_v2(message: Message, bot: Bot, lang: str = 'ru'):
    """Обработчик категории Магазины и услуги"""
    await on_shops(message, bot, lang, None)

async def handle_legacy_category(message: Message, bot: Bot, category_text: str):
    """Fallback to legacy category handling for backward compatibility"""
    lang = 'ru'
    
    # Legacy category responses (preserved exactly)
    if category_text == '🍜 Рестораны':
        restaurants_text = get_text('legacy_restaurants', lang)
        await message.answer(restaurants_text)
    elif category_text == '🧘 SPA и массаж':
        spa_text = get_text('legacy_spa', lang)
        await message.answer(spa_text)
    elif category_text == '🛵 Аренда байков':
        transport_text = get_text('legacy_transport', lang)
        await message.answer(transport_text)
    elif category_text == '🏨 Отели':
        hotels_text = get_text('legacy_hotels', lang)
        await message.answer(hotels_text)
    elif category_text == '🗺️ Экскурсии':
        tours_text = get_text('legacy_tours', lang)
        await message.answer(tours_text)
    else:
        choose_text = get_text('legacy_choose_category', lang)
        await message.answer(choose_text)

# Profile handler (new feature)
async def handle_profile(message: Message, bot: Bot, lang: str):
    """Handle profile button press"""
    if not settings.features.partner_fsm:
        profile_text = get_text('profile_development', lang)
        await message.answer(profile_text)
        return
    
    t = get_all_texts(lang)
    
    # Get partner info
    partner = db_v2.get_partner_by_tg_id(message.from_user.id)
    
    if not partner:
        # New user
        response = f"👤 **{t['profile_main']}**\n\n"
        welcome_text = get_text('profile_welcome', lang)
        add_desc = get_text('profile_add_card_desc', lang)
        cards_desc = get_text('profile_my_cards_desc', lang)
        stats_desc = get_text('profile_stats_desc', lang)
        start_text = get_text('profile_start_add', lang)
        
        response += f"{welcome_text}\n\n"
        response += f"➕ {t['add_card']}{add_desc}\n"
        response += f"📋 {t['my_cards']}{cards_desc}\n"
        response += f"📊 {t['profile_stats']}{stats_desc}\n\n"
        response += start_text
    else:
        # Existing partner
        cards = db_v2.get_partner_cards(partner.id)
        
        response = f"👤 **{t['profile_main']}**\n\n"
        hello_text = get_text('profile_hello_partner', lang).format(name=partner.display_name or 'Партнер')
        response += f"{hello_text}\n\n"
        response += f"📊 **{t['profile_stats']}:**\n"
        response += f"   • {t['cards_count']}: {len(cards)}\n"
        
        # Count by status
        status_counts = {}
        for card in cards:
            status = card['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        if status_counts:
            by_status_text = get_text('profile_stats_by_status', lang)
            response += f"\n{by_status_text}\n"
            for status, count in status_counts.items():
                status_emoji = {
                    'draft': '📝',
                    'pending': '⏳', 
                    'published': '✅',
                    'rejected': '❌',
                    'archived': '🗂️'
                }.get(status, '📄')
                response += f"   • {status_emoji} {status}: {count}\n"
    
    from ..keyboards.reply_v2 import get_profile_keyboard
    await message.answer(response, reply_markup=get_profile_keyboard(lang))

 


@category_router.callback_query(F.data.regexp(r"^pg:(restaurants|spa|transport|hotels|tours|shops):([a-zA-Z0-9_]+):([0-9]+)$"))
async def on_catalog_pagination(callback: CallbackQuery, bot: Bot, lang: str, city_id: int | None, state: FSMContext):
    """Хендлер пагинации каталога. Формат: pg:<slug>:<sub_slug>:<page>"""
    try:
        _, slug, sub_slug, page_str = callback.data.split(":")
        page = int(page_str)

        # Сначала отвечаем на callback чтобы убрать "часики"
        await callback.answer()
        
        # Вызываем универсальную функцию для обновления сообщения
        await log_event("catalog_page_click", user=callback.from_user, slug=slug, sub_slug=sub_slug, page=page)
        await show_catalog_page(bot, callback.message.chat.id, lang, slug, sub_slug, page, city_id, callback.message.message_id)
        
        try:
            await state.update_data(category=slug, sub_slug=sub_slug, page=page)
        except Exception:
            pass
            
    except Exception as e:
        logger.error(f"on_catalog_pagination error: {e}")
        try:
            await callback.answer(get_text('catalog_error', lang), show_alert=False)
        except:
            pass


@category_router.callback_query(F.data.regexp(r"^filt:restaurants:(asia|europe|street|vege|all)$"))
async def on_restaurants_filter(callback: CallbackQuery, bot: Bot, lang: str, city_id: int | None, state: FSMContext):
    """Применение фильтра ресторанов и перерисовка pg:restaurants:1.
    Формат: filt:restaurants:<filter>
    """
    try:
        # Сначала отвечаем на callback
        await callback.answer()
        
        _, _, filt = callback.data.split(":")
        await log_event("restaurants_filter", user=callback.from_user, filter=filt, lang=lang, city_id=city_id)
        slug = 'restaurants'
        page = 1

        # Получаем карточки категории (5 шт.)
        all_cards = db_v2.get_cards_by_category(slug, status='published', limit=50)
        # Опциональная фильтрация по городу, если поле присутствует
        if city_id is not None and all_cards and 'city_id' in all_cards[0]:
            all_cards = [c for c in all_cards if (c.get('city_id') == city_id)]
        if filt != 'all':
            # Локальная фильтрация по sub_slug, если поле присутствует
            cards = [c for c in all_cards if str(c.get('sub_slug') or '').lower() == filt]
        else:
            cards = all_cards

        # Обрезаем до 5 элементов (первая страница)
        per_page = 5
        count = len(cards)
        pages = max(1, (count + per_page - 1) // per_page)
        cards_page = cards[:per_page]

        # Рендер строк элементов (каждый ряд = [ℹ️, (карта)])
        inline_rows = []
        for c in cards_page:
            listing_id = c.get('id') if isinstance(c, dict) else getattr(c, 'id', None)
            gmaps = c.get('google_maps_url') if isinstance(c, dict) else getattr(c, 'google_maps_url', None)
            inline_rows.append(get_catalog_item_row(listing_id, gmaps, lang))

        # Блок фильтров (с активным маркером) + пагинация
        filter_block = get_restaurant_filters_inline(active=filt, lang=lang)
        kb_rows = filter_block.inline_keyboard + [get_pagination_row(slug, page, pages)]
        kb = inline_rows + kb_rows

        header = f"Найдено {count}. Стр. {page}/{pages}"
        await callback.message.edit_text(
            text=header + "\n\n" + card_service.render_cards_list(cards_page, lang, max_cards=5),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
        )
        try:
            await state.update_data(category='restaurants', sub_slug=filt, page=page)
        except Exception:
            pass
        
        await callback.answer()
        
        # УНИВЕРСАЛЬНАЯ ОЧИСТКА FSM ДЛЯ ВСЕХ КАТЕГОРИЙ - ПОСЛЕ показа карточек
        try:
            # Сохраняем важные данные (политика, язык)
            current_data = await state.get_data()
            policy_accepted = current_data.get('policy_accepted', False)
            lang = current_data.get('lang', 'ru')
            started = current_data.get('started', False)
            
            # Очищаем только состояние каталога, сохраняя политику
            await state.clear()
            
            # Восстанавливаем важные данные
            if policy_accepted:
                await state.update_data(policy_accepted=True, lang=lang, started=started)
                
            logger.warning(f"🔧 FSM STATE CLEARED for restaurants/{filt} (policy preserved)")
        except Exception as e:
            logger.warning(f"🔧 FSM STATE CLEAR FAILED: {e}")
    except Exception as e:
        logger.error(f"on_restaurants_filter error: {e}")
        error_text = get_text('error_try_later', lang)
        await callback.answer(error_text, show_alert=False)


@category_router.callback_query(F.data.regexp(r"^act:view:[0-9]+$"))
async def on_card_view(callback: CallbackQuery, bot: Bot):
    """Просмотр карточки по id. Формат: act:view:<id>"""
    try:
        # Получаем язык пользователя (по умолчанию русский)
        lang = 'ru'
        
        _, _, id_str = callback.data.split(":")
        listing_id = int(id_str)
        await log_event("card_view", user=callback.from_user, id=listing_id)

        # Пытаемся получить карточку; если интерфейса нет — показываем заглушку.
        card = None
        try:
            card = db_v2.get_card_by_id(listing_id)
        except Exception:
            card = None

        # Доставим первый снимок (если есть) как фото с подписью и инлайн‑кнопками
        if card:
            card_dict = card if isinstance(card, dict) else dict(card)
            text = card_service.render_card(card_dict, lang)
            # Получим фото (multi‑photo aware)
            from ..database.db_v2 import db_v2 as _db
            try:
                photos = _db.get_card_photos(listing_id)
            except Exception:
                photos = []
            # Попробуем отрисовать фото + подпись, иначе просто текст
            try:
                if photos:
                    fid = photos[0].get('file_id') if isinstance(photos[0], dict) else getattr(photos[0], 'file_id', None)
                    if fid:
                        # Предпочтительно отправить новым сообщением, чтобы не зависеть от предыстории сообщения
                        try:
                            await callback.message.delete()
                        except Exception:
                            pass
                        await callback.message.answer_photo(
                            photo=fid,
                            caption=text,
                            reply_markup=get_catalog_card_actions(listing_id, lang)
                        )
                    else:
                        raise RuntimeError("empty fid")
                else:
                    raise RuntimeError("no photos")
            except Exception:
                # fallback: редактируем текст
                await callback.message.edit_text(text=text, reply_markup=get_catalog_card_actions(listing_id, lang))
        else:
            text = get_text('card_soon_available', lang).format(card_id=str(listing_id))
            await callback.message.edit_text(text=text, reply_markup=get_catalog_card_actions(listing_id, lang))
        await callback.answer()
    except Exception as e:
        logger.error(f"on_card_view error: {e}")
        error_text = get_text('error_try_later', lang)
        await callback.answer(error_text, show_alert=False)

def get_category_router() -> Router:
    """Get category router (always enabled)"""
    return category_router

# Export handlers for registration
__all__ = [
    'show_categories_v2',
    'show_nearest_v2',
    'show_places_page',
    'show_offers_page',
    'show_place_details',
    'show_offer_details',
    'show_category_items',
    'handle_location_v2',
    'category_selected_v2',
    'handle_profile',
    'get_category_router',
    # -- Новые обработчики для Этапа 1 --
    'on_restaurants',
    'on_spa',
    'on_hotels',
    'on_transport',
    'on_tours',
    'on_transport_submenu',
    'on_tours_submenu'
    , 'on_spa_submenu', 'on_hotels_submenu',
    'on_shops', 'on_shops_submenu'
]


@category_router.callback_query(F.data.regexp(r"^gallery:[0-9]+$"))
async def on_card_gallery(callback: CallbackQuery):
    """Показ галереи фото карточки (до 6 шт.) — формат: gallery:<id>."""
    try:
        _, id_str = callback.data.split(":", 1)
        card_id = int(id_str)
    except Exception:
        await callback.answer()
        return
    
    try:
        from core.database import db_v2
        photos = db_v2.get_card_photos(card_id)
    except Exception:
        photos = []
    
    if not photos:
        await callback.answer("📭 Фото пока нет", show_alert=False)
        return
    
    # Get card info for caption
    try:
        card = db_v2.get_card_by_id(card_id)
        card_title = card.get('title', 'Карточка') if card else 'Карточка'
    except Exception:
        card_title = 'Карточка'
    
    media: list[InputMediaPhoto] = []
    for idx, p in enumerate(photos[:6]):
        # Use photo_url if available, otherwise photo_file_id
        photo_url = p.get('photo_url')
        photo_file_id = p.get('photo_file_id')
        
        if photo_url:
            media_item = InputMediaPhoto(media=photo_url)
        elif photo_file_id:
            media_item = InputMediaPhoto(media=photo_file_id)
        else:
            continue
            
        if idx == 0:
            media_item.caption = f"📷 Галерея: {card_title}"
        
        media.append(media_item)
    
    if media:
        try:
            await callback.message.answer_media_group(media)
        except Exception as e:
            logger.error(f"Error sending media group: {e}")
            await callback.answer("❌ Ошибка при загрузке фотографий", show_alert=True)
    else:
        await callback.answer("📭 Нет доступных фотографий", show_alert=False)
    
    await callback.answer()


@category_router.callback_query()
async def debug_all_category_callbacks(callback: CallbackQuery):
    """Универсальный обработчик для отладки всех callback'ов в категориях."""
    logger.warning(f"🔧 ALL CATEGORY CALLBACKS: user={callback.from_user.id}, data={callback.data}")
    await callback.answer()

@category_router.callback_query(F.data == "catalog:back")
async def on_catalog_back(callback: CallbackQuery, bot: Bot, lang: str, city_id: int | None, state: FSMContext):
    """Возврат к списку каталога с параметрами из FSM: category/sub_slug/page."""
    try:
        data = await state.get_data()
        slug = str(data.get('category') or 'restaurants')
        sub_slug = str(data.get('sub_slug') or 'all')
        page = int(data.get('page') or 1)
    except Exception:
        slug, sub_slug, page = 'restaurants', 'all', 1
    try:
        # Попробуем редактировать; если это фото-сообщение — отправим новое
        header_only = False
        await show_catalog_page(
            bot=bot,
            chat_id=callback.message.chat.id,
            lang=lang,
            slug=slug,
            sub_slug=sub_slug,
            page=page,
            city_id=city_id,
            message_id=callback.message.message_id,
        )
    except Exception:
        await show_catalog_page(
            bot=bot,
            chat_id=callback.message.chat.id,
            lang=lang,
            slug=slug,
            sub_slug=sub_slug,
            page=page,
            city_id=city_id,
        )
    await callback.answer()

@category_router.callback_query(F.data.regexp(r"^favorite:[0-9]+$"))
async def on_add_to_favorites(callback: CallbackQuery):
    """Add card to favorites"""
    try:
        # Извлекаем ID карточки
        card_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id
        
        # Проверяем, есть ли уже в избранном
        from core.database import db_v2
        is_favorite = db_v2.is_favorite(user_id, card_id)
        
        if is_favorite:
            # Удаляем из избранного
            success = db_v2.remove_from_favorites(user_id, card_id)
            if success:
                await callback.answer("💔 Удалено из избранного")
            else:
                await callback.answer("❌ Ошибка при удалении из избранного", show_alert=True)
        else:
            # Добавляем в избранное
            success = db_v2.add_to_favorites(user_id, card_id)
            if success:
                await callback.answer("⭐ Добавлено в избранное!")
            else:
                await callback.answer("❌ Ошибка при добавлении в избранное", show_alert=True)
        
    except Exception as e:
        logger.error(f"Error adding to favorites: {e}")
        await callback.answer("❌ Ошибка при работе с избранным", show_alert=True)
