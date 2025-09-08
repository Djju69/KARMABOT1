"""
Сервис для создания тестовых карточек партнеров
"""
import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class TestDataCreator:
    """Сервис для создания тестовых данных партнеров"""
    
    def __init__(self):
        self.test_photo_id = "AgACAgIAAxkBAAIBY2YAAAAA"  # Заглушка для фото
    
    async def create_test_partners(self) -> bool:
        """Создать тестовых партнеров"""
        try:
            import asyncpg
            from core.settings import settings
            
            # Подключаемся к PostgreSQL
            conn = await asyncpg.connect(settings.database_url)
            try:
                # Создаем тестовых партнеров
                partners_data = [
                    {
                        "code": "TEST001",
                        "title": "Тестовый ресторан Италия",
                        "contact_name": "Мария Иванова",
                        "contact_phone": "+7 999 123 45 67",
                        "contact_email": "maria@test-restaurant.ru",
                        "base_discount_pct": 15.0,
                        "legal_info": "ООО Тестовый ресторан"
                    },
                    {
                        "code": "TEST002", 
                        "title": "Тестовое кафе Кофе",
                        "contact_name": "Алексей Петров",
                        "contact_phone": "+7 999 234 56 78",
                        "contact_email": "alex@test-cafe.ru",
                        "base_discount_pct": 10.0,
                        "legal_info": "ИП Петров А.А."
                    },
                    {
                        "code": "TEST003",
                        "title": "Тестовый кинотеатр",
                        "contact_name": "Елена Сидорова",
                        "contact_phone": "+7 999 345 67 89",
                        "contact_email": "elena@test-cinema.ru",
                        "base_discount_pct": 20.0,
                        "legal_info": "ООО Тестовый кинотеатр"
                    },
                    {
                        "code": "TEST004",
                        "title": "Тестовый фитнес клуб",
                        "contact_name": "Дмитрий Козлов",
                        "contact_phone": "+7 999 456 78 90",
                        "contact_email": "dmitry@test-fitness.ru",
                        "base_discount_pct": 25.0,
                        "legal_info": "ООО Тестовый фитнес"
                    },
                    {
                        "code": "TEST005",
                        "title": "Тестовый салон красоты",
                        "contact_name": "Анна Морозова",
                        "contact_phone": "+7 999 567 89 01",
                        "contact_email": "anna@test-beauty.ru",
                        "base_discount_pct": 30.0,
                        "legal_info": "ИП Морозова А.В."
                    }
                ]
                
                partner_ids = []
                for partner_data in partners_data:
                    partner_id = await conn.fetchval("""
                        INSERT INTO partners (
                            code, title, status, base_discount_pct, contact_name, 
                            contact_telegram, contact_phone, contact_email, legal_info,
                            created_at, approved_by, approved_at
                        ) VALUES ($1, $2, 'approved', $3, $4, $5, $6, $7, $8, $9, $10, $11)
                        RETURNING id
                    """, 
                        partner_data["code"],
                        partner_data["title"],
                        partner_data["base_discount_pct"],
                        partner_data["contact_name"],
                        123456789,  # Тестовый telegram_id
                        partner_data["contact_phone"],
                        partner_data["contact_email"],
                        partner_data["legal_info"],
                        datetime.now().isoformat(),
                        123456789,  # Тестовый admin_id
                        datetime.now().isoformat()
                    )
                    partner_ids.append(partner_id)
                
                # Создаем заведения для каждого партнера
                await self._create_test_places(conn, partner_ids)
                
                logger.info(f"Created {len(partners_data)} test partners with places")
                return True
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"Error creating test partners: {e}")
            return False
    
    async def _create_test_places(self, conn, partner_ids: List[int]):
        """Создать тестовые заведения для партнеров"""
        try:
            # Получаем существующие категории из БД
            categories = await conn.fetch("SELECT id, slug, name FROM categories ORDER BY id")
            
            place_counter = 0
            
            for category in categories:
                # Создаем 2 заведения для каждой категории
                for i in range(2):
                    partner_id = partner_ids[place_counter % len(partner_ids)]
                    place_counter += 1
                    
                    place_data = {
                        "partner_id": partner_id,
                        "title": f"{category['name']} #{i+1}",
                        "address": f"ул. Тестовая, д. {place_counter}",
                        "geo_lat": 55.7558 + (place_counter * 0.001),
                        "geo_lon": 37.6176 + (place_counter * 0.001),
                        "hours": "09:00-22:00",
                        "phone": f"+7 999 {100 + place_counter:03d} {10 + place_counter:02d} {20 + place_counter:02d}",
                        "website": f"https://test-{place_counter}.ru",
                        "price_level": "$$",
                        "rating": 4.5 + (place_counter % 5) * 0.1,
                        "reviews_count": 50 + place_counter * 10,
                        "description": f"Тестовое заведение {category['name']} с отличным сервисом и качественными услугами.",
                        "base_discount_pct": 10.0 + (place_counter % 20),
                        "loyalty_accrual_pct": 5.0 + (place_counter % 10),
                        "min_redeem": 1000,
                        "max_percent_per_bill": 50.0,
                        "cover_file_id": self.test_photo_id,
                        "gallery_file_ids": f'["{self.test_photo_id}", "{self.test_photo_id}", "{self.test_photo_id}", "{self.test_photo_id}", "{self.test_photo_id}", "{self.test_photo_id}"]',
                        "categories": f'["{category["slug"]}"]',  # Используем slug категории
                        "status": "approved"  # Статус одобрен для тестирования
                    }
                        
                        await conn.execute("""
                            INSERT INTO partner_places (
                                partner_id, title, status, address, geo_lat, geo_lon,
                                hours, phone, website, price_level, rating, reviews_count,
                                description, base_discount_pct, loyalty_accrual_pct,
                                min_redeem, max_percent_per_bill, cover_file_id,
                                gallery_file_ids, categories, created_at, created_by
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22)
                        """, 
                            place_data["partner_id"],
                            place_data["title"],
                            place_data["status"],
                            place_data["address"],
                            place_data["geo_lat"],
                            place_data["geo_lon"],
                            place_data["hours"],
                            place_data["phone"],
                            place_data["website"],
                            place_data["price_level"],
                            place_data["rating"],
                            place_data["reviews_count"],
                            place_data["description"],
                            place_data["base_discount_pct"],
                            place_data["loyalty_accrual_pct"],
                            place_data["min_redeem"],
                            place_data["max_percent_per_bill"],
                            place_data["cover_file_id"],
                            place_data["gallery_file_ids"],
                            place_data["categories"],
                            datetime.now().isoformat(),
                            123456789  # Тестовый created_by
                        ))
            
            logger.info("Created test places for all categories")
            
        except Exception as e:
            logger.error(f"Error creating test places: {e}")
            raise

# Глобальный экземпляр
test_data_creator = TestDataCreator()
