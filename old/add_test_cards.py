#!/usr/bin/env python3
"""
Добавление тестовых карточек в базу данных
"""
import os
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def add_test_cards():
    """Добавить тестовые карточки"""
    logger.info("🔍 Добавляем тестовые карточки...")
    
    try:
        from core.database.db_v2 import db_v2, Card, Partner
        
        # Создаем тестового партнера
        test_partner = db_v2.get_or_create_partner(999999998, "Тестовый Партнер")
        logger.info(f"✅ Партнер создан: ID={test_partner.id}")
        
        # Тестовые карточки
        test_cards = [
            {
                'title': '🍽️ Ресторан "Золотой Дракон"',
                'description': 'Китайская кухня высшего качества. Свежие морепродукты и традиционные блюда.',
                'address': 'ул. Нгуен Хюэ, 123, Нячанг',
                'contact': '+84 258 123 456',
                'discount_text': 'Скидка 15% на все блюда',
                'category_id': 1,  # Рестораны
                'status': 'approved'
            },
            {
                'title': '🧘‍♀️ SPA "Тропический Рай"',
                'description': 'Роскошный SPA-центр с видом на море. Массаж, сауна, бассейн.',
                'address': 'ул. Чан Фу, 456, Нячанг',
                'contact': '+84 258 234 567',
                'discount_text': 'Массаж в подарок при покупке пакета',
                'category_id': 2,  # SPA
                'status': 'approved'
            },
            {
                'title': '🏍️ Аренда байков "Скорость"',
                'description': 'Прокат мотоциклов и скутеров. Новые модели, страховка включена.',
                'address': 'ул. Хунг Вуонг, 789, Нячанг',
                'contact': '+84 258 345 678',
                'discount_text': 'Скидка 20% при аренде на неделю',
                'category_id': 3,  # Транспорт
                'status': 'approved'
            },
            {
                'title': '🏨 Отель "Морской Бриз"',
                'description': '4-звездочный отель на первой линии. Все номера с видом на море.',
                'address': 'ул. Чан Фу, 321, Нячанг',
                'contact': '+84 258 456 789',
                'discount_text': 'Бесплатный завтрак при бронировании',
                'category_id': 4,  # Отели
                'status': 'approved'
            },
            {
                'title': '🚁 Экскурсии "Небесные Виды"',
                'description': 'Вертолетные экскурсии над Нячангом. Фотосессии и романтические туры.',
                'address': 'Аэропорт Камрань, Нячанг',
                'contact': '+84 258 567 890',
                'discount_text': 'Скидка 10% для групп от 4 человек',
                'category_id': 5,  # Экскурсии
                'status': 'approved'
            },
            {
                'title': '🛍️ Магазин "Сувениры Вьетнама"',
                'description': 'Аутентичные сувениры и подарки. Кофе, чай, изделия ручной работы.',
                'address': 'ул. Нгуен Тхи Минь Кхай, 654, Нячанг',
                'contact': '+84 258 678 901',
                'discount_text': 'Скидка 25% на весь ассортимент',
                'category_id': 6,  # Магазины
                'status': 'approved'
            }
        ]
        
        added_cards = []
        for card_data in test_cards:
            card = Card(
                id=None,
                partner_id=test_partner.id,
                category_id=card_data['category_id'],
                title=card_data['title'],
                description=card_data['description'],
                address=card_data['address'],
                contact=card_data['contact'],
                discount_text=card_data['discount_text'],
                status=card_data['status']
            )
            
            card_id = db_v2.create_card(card)
            added_cards.append(card_id)
            logger.info(f"✅ Карточка создана: ID={card_id}, Title={card.title}")
        
        logger.info(f"🎉 Всего добавлено карточек: {len(added_cards)}")
        
        # Проверяем что карточки добавились
        category_slugs = ['restaurants', 'spa', 'transport', 'hotels', 'tours', 'shops']
        for slug in category_slugs:
            cards = db_v2.get_cards_by_category(slug, status='approved')
            logger.info(f"📊 Категория {slug}: {len(cards)} карточек")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка добавления карточек: {e}")
        return False

async def main():
    """Главная функция"""
    logger.info("🚀 Добавление тестовых карточек в базу данных")
    
    success = await add_test_cards()
    
    if success:
        logger.info("🎉 ТЕСТОВЫЕ КАРТОЧКИ ДОБАВЛЕНЫ!")
        logger.info("✅ Теперь каталог не будет пустым")
        logger.info("✅ Пользователи смогут выбирать категории")
    else:
        logger.error("❌ НЕ УДАЛОСЬ ДОБАВИТЬ КАРТОЧКИ")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
