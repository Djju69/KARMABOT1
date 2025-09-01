"""
InlineKeyboard система согласно ТЗ v4.1
Канон: ТОЛЬКО контекстные действия - пагинация, подтверждения, меню ⋮
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class InlineKeyboards:
    """Система InlineKeyboard строго по канону ТЗ - только контекстные действия"""
    
    def __init__(self, i18n_texts: Dict[str, str]):
        self.texts = i18n_texts
    
    def get_pagination_keyboard(self, current_page: int, total_pages: int, 
                              callback_prefix: str = "page") -> InlineKeyboardMarkup:
        """
        Пагинация согласно ТЗ 1.3
        Принцип: Пагинация — это контекстное действие, поэтому Inline
        """
        keyboard = []
        
        # Кнопки страниц
        page_buttons = []
        for page in range(1, min(total_pages + 1, 6)):  # Максимум 5 страниц
            if page == current_page:
                continue
            page_buttons.append(
                InlineKeyboardButton(
                    text=f"Стр. {page}",
                    callback_data=f"{callback_prefix}:{page}"
                )
            )
        
        if page_buttons:
            keyboard.append(page_buttons)
        
        # Кнопка закрыть
        keyboard.append([
            InlineKeyboardButton(
                text=self.texts.get("inline.close", "Закрыть"),
                callback_data="close"
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    def get_confirmation_keyboard(self, action: str, amount: str = None) -> InlineKeyboardMarkup:
        """
        Подтверждение операций согласно ТЗ 1.4, 2.3
        Принцип: Подтверждение/отмена — контекстные действия
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    text=self.texts.get("inline.confirm", "Подтвердить"),
                    callback_data=f"confirm:{action}"
                ),
                InlineKeyboardButton(
                    text=self.texts.get("inline.cancel", "Отменить"), 
                    callback_data=f"cancel:{action}"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    def get_establishment_actions(self, establishment_id: str) -> InlineKeyboardMarkup:
        """
        Действия с заведениями согласно ТЗ 2.2
        Принцип: Действия с заведениями — контекстные
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    text="ℹ️",
                    callback_data=f"establishment:info:{establishment_id}"
                ),
                InlineKeyboardButton(
                    text="🗺",
                    callback_data=f"establishment:map:{establishment_id}"
                ),
                InlineKeyboardButton(
                    text="🎫 QR",
                    callback_data=f"establishment:qr:{establishment_id}"
                ),
                InlineKeyboardButton(
                    text="⋮",
                    callback_data=f"establishment:more:{establishment_id}"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    def get_establishment_more_menu(self, establishment_id: str) -> InlineKeyboardMarkup:
        """
        Раскрывающееся меню ⋮ Ещё для заведений
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    text=self.texts.get("inline.hide", "Скрыть"),
                    callback_data=f"establishment:hide:{establishment_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text=self.texts.get("inline.edit", "Редактировать"),
                    callback_data=f"establishment:edit:{establishment_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text=self.texts.get("inline.back", "◀️ Назад"),
                    callback_data=f"establishment:back:{establishment_id}"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    def get_admin_partner_actions(self, partner_id: str) -> InlineKeyboardMarkup:
        """
        Действия админа с партнёром согласно ТЗ 3.1
        Принцип: Административные действия — контекстные
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    text=self.texts.get("inline.block", "Блок"),
                    callback_data=f"admin:block:{partner_id}"
                ),
                InlineKeyboardButton(
                    text=self.texts.get("inline.edit", "Правка"),
                    callback_data=f"admin:edit:{partner_id}"
                ),
                InlineKeyboardButton(
                    text=self.texts.get("inline.log", "Журнал"),
                    callback_data=f"admin:log:{partner_id}"
                )
            ]
        ]
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    def get_period_selector(self, current_period: str = "7d") -> InlineKeyboardMarkup:
        """
        Выбор периода для отчётов
        Принцип: Выбор опций — контекстное действие
        """
        periods = [
            ("1d", "1 день"),
            ("7d", "7 дней"), 
            ("30d", "30 дней"),
            ("90d", "90 дней")
        ]
        
        keyboard = []
        for period_code, period_name in periods:
            text = f"✅ {period_name}" if period_code == current_period else period_name
            keyboard.append([
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"period:{period_code}"
                )
            ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_inline_keyboard(action: str, **kwargs) -> Optional[InlineKeyboardMarkup]:
    """
    Фабрика InlineKeyboard согласно канону ТЗ
    Только для контекстных действий: пагинация, подтверждения, меню ⋮
    """
    # i18n тексты
    i18n_texts = {
        "inline.close": "Закрыть",
        "inline.confirm": "Подтвердить", 
        "inline.cancel": "Отменить",
        "inline.hide": "Скрыть",
        "inline.edit": "Редактировать",
        "inline.back": "◀️ Назад",
        "inline.block": "Блок",
        "inline.log": "Журнал"
    }
    
    keyboards = InlineKeyboards(i18n_texts)
    
    try:
        if action == "pagination":
            current_page = kwargs.get('current_page', 1)
            total_pages = kwargs.get('total_pages', 1)
            callback_prefix = kwargs.get('callback_prefix', 'page')
            return keyboards.get_pagination_keyboard(current_page, total_pages, callback_prefix)
        
        elif action == "confirmation":
            confirm_action = kwargs.get('confirm_action', 'default')
            amount = kwargs.get('amount')
            return keyboards.get_confirmation_keyboard(confirm_action, amount)
        
        elif action == "establishment_actions":
            establishment_id = kwargs.get('establishment_id')
            return keyboards.get_establishment_actions(establishment_id)
        
        elif action == "establishment_more":
            establishment_id = kwargs.get('establishment_id')
            return keyboards.get_establishment_more_menu(establishment_id)
        
        elif action == "admin_partner_actions":
            partner_id = kwargs.get('partner_id')
            return keyboards.get_admin_partner_actions(partner_id)
        
        elif action == "period_selector":
            current_period = kwargs.get('current_period', '7d')
            return keyboards.get_period_selector(current_period)
        
        else:
            logger.warning(f"Unknown inline keyboard action: {action}")
            return None
            
    except Exception as e:
        logger.error(f"Error creating inline keyboard: {e}")
        return None
#             KeyboardButton(text="🇬🇧 English"),
#             KeyboardButton(text="🇰🇷 한국어")
#         ]
#     ],
#     resize_keyboard=True,
#     one_time_keyboard=True
# )
