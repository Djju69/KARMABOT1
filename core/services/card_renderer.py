"""
Unified card rendering service with template support
Implements Protocol pattern for extensibility and backward compatibility
"""
from typing import Protocol, Dict, Any, Optional
from abc import abstractmethod
from pathlib import Path
import logging

from ..utils.locales_v2 import get_text, get_all_texts
from ..settings import settings

logger = logging.getLogger(__name__)

class CardRenderer(Protocol):
    """Protocol for card rendering implementations"""
    
    @abstractmethod
    def render_card(self, card: Dict[str, Any], lang: str = 'ru') -> str:
        """Render card to text format"""
        pass
    
    @abstractmethod
    def render_card_preview(self, card: Dict[str, Any], lang: str = 'ru') -> str:
        """Render card preview for moderation/editing"""
        pass

class DefaultCardRenderer:
    """Default implementation of card renderer"""
    
    def __init__(self):
        self.template_cache = {}
    
    def _load_template(self, template_name: str) -> str:
        """Load template from file with caching"""
        if template_name in self.template_cache:
            return self.template_cache[template_name]
        
        template_path = Path(f"templates/{template_name}.txt")
        
        if template_path.exists():
            try:
                template_content = template_path.read_text(encoding='utf-8')
                self.template_cache[template_name] = template_content
                return template_content
            except Exception as e:
                logger.warning(f"Failed to load template {template_name}: {e}")
        
        # Fallback to built-in template
        return self._get_builtin_template(template_name)
    
    def _get_builtin_template(self, template_name: str) -> str:
        """Get built-in template as fallback"""
        templates = {
            'card': '''**{title}**

{description}

{contact_section}
{address_section}
{discount_section}

{actions}''',
            
            'card_preview': '''📋 **Предпросмотр карточки**

📂 **Категория:** {category_name}
📝 **Название:** {title}
{description_section}
{contact_section}
{address_section}
{discount_section}
{photo_section}

📅 **Создана:** {created_at}
⏳ **Статус:** {status}'''
        }
        
        return templates.get(template_name, '{title}\n{description}')
    
    def render_card(self, card: Dict[str, Any], lang: str = 'ru') -> str:
        """Render card for public display"""
        t = get_all_texts(lang)
        template = self._load_template('card')
        
        # Prepare sections
        contact_section = ""
        if card.get('contact'):
            contact_section = f"📞 **{t['contact_info']}:** {card['contact']}"
        
        address_section = ""
        if card.get('address'):
            address_section = f"📍 **{t['address_info']}:** {card['address']}"
        
        discount_section = ""
        if card.get('discount_text'):
            discount_section = f"🎫 **{t['discount_info']}:** {card['discount_text']}"
        
        # Actions (can be customized per category)
        actions = self._render_card_actions(card, t)
        
        # Format template
        try:
            return template.format(
                title=card.get('title', 'Без названия'),
                description=card.get('description', ''),
                contact_section=contact_section,
                address_section=address_section,
                discount_section=discount_section,
                actions=actions
            ).strip()
        except KeyError as e:
            logger.error(f"Template formatting error: {e}")
            return self._render_simple_card(card, t)
    
    def render_card_preview(self, card: Dict[str, Any], lang: str = 'ru') -> str:
        """Render card preview for moderation"""
        t = get_all_texts(lang)
        template = self._load_template('card_preview')
        
        # Prepare optional sections
        description_section = ""
        if card.get('description'):
            description_section = f"📄 **Описание:** {card['description']}"
        
        contact_section = ""
        if card.get('contact'):
            contact_section = f"📞 **Контакт:** {card['contact']}"
        
        address_section = ""
        if card.get('address'):
            address_section = f"📍 **Адрес:** {card['address']}"
        
        discount_section = ""
        if card.get('discount_text'):
            discount_section = f"🎫 **Скидка:** {card['discount_text']}"
        
        photo_section = ""
        if card.get('photo_file_id'):
            photo_section = "📸 **Фото:** Прикреплено"
        
        # Status translation
        status_map = {
            'draft': t.get('card_status_draft', '📝 Черновик'),
            'pending': t.get('card_status_pending', '⏳ На модерации'),
            'approved': t.get('card_status_approved', '✅ Одобрено'),
            'published': t.get('card_status_published', '🎉 Опубликовано'),
            'rejected': t.get('card_status_rejected', '❌ Отклонено'),
            'archived': t.get('card_status_archived', '🗂️ Архив')
        }
        
        status_text = status_map.get(card.get('status', 'draft'), card.get('status', 'draft'))
        
        try:
            return template.format(
                category_name=card.get('category_name', 'Неизвестно'),
                title=card.get('title', 'Без названия'),
                description_section=description_section,
                contact_section=contact_section,
                address_section=address_section,
                discount_section=discount_section,
                photo_section=photo_section,
                created_at=card.get('created_at', 'Неизвестно'),
                status=status_text
            ).strip()
        except KeyError as e:
            logger.error(f"Preview template formatting error: {e}")
            return f"**{card.get('title', 'Карточка')}**\n{card.get('description', '')}"
    
    def _render_card_actions(self, card: Dict[str, Any], t: Dict[str, str]) -> str:
        """Render action buttons text for card"""
        actions = []
        
        if card.get('contact'):
            actions.append(f"📞 {t.get('call_business', 'Связаться')}")
        
        if card.get('google_maps_url'):
            actions.append(f"🗺️ {t.get('show_on_map', 'Показать на карте')}")
        
        if card.get('discount_text'):
            actions.append(f"📱 {t.get('create_qr', 'Создать QR')}")
        
        if actions:
            return "**Действия:** " + " | ".join(actions)
        
        return ""
    
    def _render_simple_card(self, card: Dict[str, Any], t: Dict[str, str]) -> str:
        """Simple fallback renderer"""
        text = f"**{card.get('title', 'Без названия')}**\n"
        
        if card.get('description'):
            text += f"{card['description']}\n"
        
        if card.get('contact'):
            text += f"\n📞 {card['contact']}"
        
        if card.get('address'):
            text += f"\n📍 {card['address']}"
        
        if card.get('discount_text'):
            text += f"\n🎫 {card['discount_text']}"
        
        return text.strip()

class LegacyCardRenderer:
    """Legacy renderer for backward compatibility"""
    
    def render_card(self, card: Dict[str, Any], lang: str = 'ru') -> str:
        """Render in legacy format"""
        # Simple format matching original code
        text = f"{card.get('title', 'Без названия')}\n"
        
        if card.get('description'):
            text += f"{card['description']}\n"
        
        if card.get('discount_text'):
            text += f"\nСкидка: {card['discount_text']}"
        
        return text.strip()
    
    def render_card_preview(self, card: Dict[str, Any], lang: str = 'ru') -> str:
        """Legacy preview format"""
        return self.render_card(card, lang)

class CardRenderingService:
    """Main service for card rendering with pluggable renderers"""
    
    def __init__(self):
        self._renderers = {
            'default': DefaultCardRenderer(),
            'legacy': LegacyCardRenderer()
        }
        self._current_renderer = 'default'
    
    def register_renderer(self, name: str, renderer: CardRenderer):
        """Register custom renderer"""
        self._renderers[name] = renderer
    
    def set_renderer(self, name: str):
        """Switch active renderer"""
        if name in self._renderers:
            self._current_renderer = name
        else:
            logger.warning(f"Renderer '{name}' not found, using default")
    
    def get_renderer(self) -> CardRenderer:
        """Get current active renderer"""
        return self._renderers[self._current_renderer]
    
    def render_card(self, card: Dict[str, Any], lang: str = 'ru', renderer: Optional[str] = None) -> str:
        """Render card using specified or current renderer"""
        renderer_name = renderer or self._current_renderer
        
        if renderer_name not in self._renderers:
            renderer_name = 'default'
        
        try:
            return self._renderers[renderer_name].render_card(card, lang)
        except Exception as e:
            logger.error(f"Card rendering failed with {renderer_name}: {e}")
            # Fallback to legacy renderer
            return self._renderers['legacy'].render_card(card, lang)
    
    def render_card_preview(self, card: Dict[str, Any], lang: str = 'ru', renderer: Optional[str] = None) -> str:
        """Render card preview"""
        renderer_name = renderer or self._current_renderer
        
        if renderer_name not in self._renderers:
            renderer_name = 'default'
        
        try:
            return self._renderers[renderer_name].render_card_preview(card, lang)
        except Exception as e:
            logger.error(f"Card preview rendering failed with {renderer_name}: {e}")
            return self._renderers['legacy'].render_card_preview(card, lang)
    
    def render_cards_list(self, cards: list, lang: str = 'ru', max_cards: int = 10) -> str:
        """Render list of cards with pagination"""
        if not cards:
            t = get_all_texts(lang)
            return "📭 Карточки не найдены."
        
        # Limit cards for performance
        display_cards = cards[:max_cards]
        
        result = []
        for i, card in enumerate(display_cards, 1):
            card_text = self.render_card(card, lang)
            result.append(f"**{i}.** {card_text}")
        
        if len(cards) > max_cards:
            result.append(f"\n... и еще {len(cards) - max_cards} карточек")
        
        return "\n\n".join(result)

# Global service instance
card_service = CardRenderingService()

# Convenience functions for backward compatibility
def render_card(card: Dict[str, Any], lang: str = 'ru') -> str:
    """Render single card"""
    return card_service.render_card(card, lang)

def render_card_preview(card: Dict[str, Any], lang: str = 'ru') -> str:
    """Render card preview"""
    return card_service.render_card_preview(card, lang)

def render_cards_list(cards: list, lang: str = 'ru') -> str:
    """Render list of cards"""
    return card_service.render_cards_list(cards, lang)

# Export main components
__all__ = [
    'CardRenderer',
    'DefaultCardRenderer', 
    'LegacyCardRenderer',
    'CardRenderingService',
    'card_service',
    'render_card',
    'render_card_preview', 
    'render_cards_list'
]
