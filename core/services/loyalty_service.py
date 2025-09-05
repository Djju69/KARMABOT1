"""
Сервис для работы с системой лояльности.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any
from uuid import UUID, uuid4
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, text
from sqlalchemy.exc import SQLAlchemyError

from core.models.loyalty_models import (
    LoyaltyTransaction,
    LoyaltyBalance,
    ActivityType,
    LoyaltyTransactionType,
    ActivityRule,
    ReferralProgram,
    ReferralLink,
    Referral
)
from core.database import get_db, execute_in_transaction
from core.logger import get_logger
from core.common.exceptions import NotFoundError, ValidationError

logger = get_logger(__name__)

# Стандартные правила начисления баллов
DEFAULT_ACTIVITY_RULES = {
    ActivityType.DAILY_CHECKIN: ActivityRule(
        activity_type=ActivityType.DAILY_CHECKIN,
        points=10,
        cooldown_hours=24,
        daily_cap=10,
        is_active=True
    ),
    ActivityType.PROFILE_COMPLETION: ActivityRule(
        activity_type=ActivityType.PROFILE_COMPLETION,
        points=50,
        cooldown_hours=0,  # Одноразово
        is_active=True
    ),
    ActivityType.CARD_BINDING: ActivityRule(
        activity_type=ActivityType.CARD_BINDING,
        points=100,
        cooldown_hours=0,  # Одноразово
        is_active=True
    ),
    ActivityType.GEO_CHECKIN: ActivityRule(
        activity_type=ActivityType.GEO_CHECKIN,
        points=20,
        cooldown_hours=4,
        daily_cap=3,
        is_active=True
    ),
    ActivityType.REFERRAL_SIGNUP: ActivityRule(
        activity_type=ActivityType.REFERRAL_SIGNUP,
        points=50,  # Бонус приглашенному
        cooldown_hours=0,
        is_active=True
    )
}

DEFAULT_REFERRAL_PROGRAM = ReferralProgram(
    referrer_bonus=100,
    referee_bonus=50,
    is_active=True
)

class LoyaltyService:
    """Сервис для работы с системой лояльности."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.activity_rules: Dict[ActivityType, ActivityRule] = {}
        self.referral_program: Optional[ReferralProgram] = None
    
    async def initialize(self):
        """Инициализация сервиса - загрузка правил из БД."""
        await self._load_activity_rules()
        await self._load_referral_program()
    
    async def _load_activity_rules(self):
        """Загрузка правил начисления баллов из БД."""
        try:
            result = await self.db.execute(
                """
                SELECT activity_type, points, cooldown_hours, daily_cap, is_active
                FROM loyalty_activity_rules
                WHERE is_active = true
                """
            )
            
            for row in result.mappings():
                try:
                    activity_type = ActivityType(row['activity_type'])
                    self.activity_rules[activity_type] = ActivityRule(
                        activity_type=activity_type,
                        points=row['points'],
                        cooldown_hours=row['cooldown_hours'],
                        daily_cap=row['daily_cap'],
                        is_active=row['is_active']
                    )
                except ValueError as e:
                    get_logger(__name__).warning(
                        f"Неизвестный тип активности в БД: {row['activity_type']}"
                    )
            
            # Если в БД нет правил, используем значения по умолчанию
            if not self.activity_rules:
                self.activity_rules = DEFAULT_ACTIVITY_RULES
                get_logger(__name__).warning("Используются правила по умолчанию")
                
        except Exception as e:
            get_logger(__name__).error(
                f"Ошибка при загрузке правил активностей: {str(e)}"
            )
            self.activity_rules = DEFAULT_ACTIVITY_RULES
    
    async def _load_referral_program(self):
        """Загрузка настроек реферальной программы из БД."""
        try:
            # В будущем можно реализовать загрузку из таблицы настроек
            self.referral_program = DEFAULT_REFERRAL_PROGRAM
        except Exception as e:
            get_logger(__name__).error(
                f"Ошибка при загрузке настроек реферальной программы: {str(e)}"
            )
            self.referral_program = DEFAULT_REFERRAL_PROGRAM
    
    async def get_balance(self, user_id: UUID) -> LoyaltyBalance:
        """
        Получение текущего баланса пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            LoyaltyBalance: Текущий баланс пользователя
            
        Raises:
            NotFoundError: Если пользователь не найден
        """
        try:
            result = await self.db.execute(
                """
                SELECT user_id, total_points, available_points, last_updated
                FROM loyalty_balances
                WHERE user_id = :user_id
                """,
                {"user_id": user_id}
            )
            
            row = result.mappings().first()
            if not row:
                # Если у пользователя еще нет записи о балансе, создаем ее
                return await self._create_initial_balance(user_id)
                
            return LoyaltyBalance(
                user_id=row['user_id'],
                total_points=row['total_points'],
                available_points=row['available_points'],
                last_updated=row['last_updated']
            )
            
        except Exception as e:
            get_logger(__name__).error(
                f"Ошибка при получении баланса пользователя {user_id}: {str(e)}"
            )
            raise
    
    async def _create_initial_balance(self, user_id: UUID) -> LoyaltyBalance:
        """Создание начального баланса для пользователя."""
        try:
            # Проверяем существование пользователя
            user_exists = await self.db.execute(
                "SELECT 1 FROM users WHERE id = :user_id",
                {"user_id": user_id}
            )
            
            if not user_exists.scalar():
                raise NotFoundError(f"Пользователь с ID {user_id} не найден")
            
            # Создаем начальный баланс
            await self.db.execute(
                """
                INSERT INTO loyalty_balances (user_id, total_points, available_points)
                VALUES (:user_id, 0, 0)
                """,
                {"user_id": user_id}
            )
            
            return LoyaltyBalance(
                user_id=user_id,
                total_points=0,
                available_points=0,
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            get_logger(__name__).error(
                f"Ошибка при создании начального баланса для пользователя {user_id}: {str(e)}"
            )
            raise
    
    async def add_points(
        self,
        user_id: UUID,
        points: int,
        transaction_type: LoyaltyTransactionType,
        activity_type: Optional[ActivityType] = None,
        reference_id: Optional[UUID] = None,
        description: Optional[str] = None
    ) -> LoyaltyTransaction:
        """
        Добавление баллов пользователю.
        
        Args:
            user_id: ID пользователя
            points: Количество баллов для начисления (должно быть положительным)
            transaction_type: Тип транзакции
            activity_type: Тип активности (если применимо)
            reference_id: ID связанной сущности
            description: Описание транзакции
            
        Returns:
            LoyaltyTransaction: Созданная транзакция
            
        Raises:
            ValidationError: Если количество баллов не положительное
            SQLAlchemyError: При ошибках работы с БД
        """
        if points <= 0:
            raise ValidationError("Количество баллов должно быть положительным")
        
        async with self.db.begin():
            try:
                # Создаем запись о транзакции
                result = await self.db.execute(
                    """
                    INSERT INTO loyalty_transactions 
                        (user_id, points, transaction_type, activity_type, reference_id, description)
                    VALUES 
                        (:user_id, :points, :transaction_type, :activity_type, :reference_id, :description)
                    RETURNING id, created_at
                    """,
                    {
                        "user_id": user_id,
                        "points": points,
                        "transaction_type": transaction_type.value,
                        "activity_type": activity_type.value if activity_type else None,
                        "reference_id": reference_id,
                        "description": description
                    }
                )
                
                row = result.mappings().first()
                
                # Обновляем баланс пользователя
                await self.db.execute(
                    """
                    INSERT INTO loyalty_balances (user_id, total_points, available_points)
                    VALUES (:user_id, :points, :points)
                    ON CONFLICT (user_id) 
                    DO UPDATE SET
                        total_points = loyalty_balances.total_points + EXCLUDED.total_points,
                        available_points = loyalty_balances.available_points + EXCLUDED.available_points,
                        last_updated = NOW()
                    """,
                    {"user_id": user_id, "points": points}
                )
                
                # Логируем активность, если это активность
                if activity_type:
                    await self.db.execute(
                        """
                        INSERT INTO user_activity_logs (user_id, activity_type, points_awarded)
                        VALUES (:user_id, :activity_type, :points)
                        """,
                        {
                            "user_id": user_id,
                            "activity_type": activity_type.value,
                            "points": points
                        }
                    )
                
                # Получаем обновленный баланс
                balance = await self.get_balance(user_id)
                
                # Создаем объект транзакции для возврата
                transaction = LoyaltyTransaction(
                    id=row['id'],
                    user_id=user_id,
                    points=points,
                    transaction_type=transaction_type,
                    activity_type=activity_type,
                    reference_id=reference_id,
                    description=description,
                    created_at=row['created_at']
                )
                
                get_logger(__name__).info(
                    f"Начислено {points} баллов пользователю {user_id}. "
                    f"Новый баланс: {balance.available_points}/{balance.total_points}"
                )
                
                return transaction
                
            except Exception as e:
                get_logger(__name__).error(
                    f"Ошибка при начислении {points} баллов пользователю {user_id}: {str(e)}"
                )
                await self.db.rollback()
                raise
    
    async def spend_points(
        self,
        user_id: UUID,
        points: int,
        description: Optional[str] = None
    ) -> LoyaltyTransaction:
        """
        Списание баллов с баланса пользователя.
        
        Args:
            user_id: ID пользователя
            points: Количество баллов для списания (должно быть положительным)
            description: Описание списания
            
        Returns:
            LoyaltyTransaction: Созданная транзакция списания
            
        Raises:
            ValidationError: Если недостаточно баллов или некорректные данные
            SQLAlchemyError: При ошибках работы с БД
        """
        if points <= 0:
            raise ValidationError("Количество баллов для списания должно быть положительным")
        
        async with self.db.begin():
            try:
                # Проверяем баланс с блокировкой строки
                balance_result = await self.db.execute(
                    """
                    SELECT available_points 
                    FROM loyalty_balances 
                    WHERE user_id = :user_id
                    FOR UPDATE
                    """,
                    {"user_id": user_id}
                )
                
                available_points = balance_result.scalar()
                
                if available_points is None:
                    raise NotFoundError(f"Баланс пользователя {user_id} не найден")
                    
                if available_points < points:
                    raise ValidationError(
                        f"Недостаточно баллов. Доступно: {available_points}, требуется: {points}"
                    )
                
                # Создаем запись о списании
                result = await self.db.execute(
                    """
                    INSERT INTO loyalty_transactions 
                        (user_id, points, transaction_type, description) 
                    VALUES 
                        (:user_id, -:points, :transaction_type, :description)
                    RETURNING id, created_at
                    """,
                    {
                        "user_id": user_id,
                        "points": points,
                        "description": description,
                        "transaction_type": LoyaltyTransactionType.SPEND.value
                    }
                )
                
                row = result.mappings().first()
                
                # Обновляем баланс пользователя
                await self.db.execute(
                    """
                    UPDATE loyalty_balances
                    SET 
                        available_points = available_points - :points,
                        last_updated = NOW()
                    WHERE user_id = :user_id
                    """,
                    {"user_id": user_id, "points": points}
                )
                
                # Получаем обновленный баланс
                balance = await self.get_balance(user_id)
                
                # Создаем объект транзакции для возврата
                transaction = LoyaltyTransaction(
                    id=row['id'],
                    user_id=user_id,
                    points=-points,
                    transaction_type=LoyaltyTransactionType.SPEND,
                    description=description,
                    created_at=row['created_at']
                )
                
                get_logger(__name__).info(
                    f"Списано {points} баллов у пользователя {user_id}. "
                    f"Остаток: {balance.available_points}/{balance.total_points}"
                )
                
                return transaction
                
            except Exception as e:
                get_logger(__name__).error(
                    f"Ошибка при списании {points} баллов у пользователя {user_id}: {str(e)}"
                )
                await self.db.rollback()
                raise
    
    async def record_activity(
        self,
        user_id: UUID,
        activity_type: ActivityType,
        location: Optional[Tuple[float, float]] = None,
        partner_id: Optional[UUID] = None
    ) -> LoyaltyTransaction:
        """
        Запись активности пользователя и начисление баллов, если возможно.
        
        Args:
            user_id: ID пользователя
            activity_type: Тип активности
            location: Координаты (широта, долгота) для гео-проверки
            partner_id: ID партнера (если активность связана с партнером)
            
        Returns:
            LoyaltyTransaction: Созданная транзакция
            
        Raises:
            ValidationError: Если активность не может быть засчитана
            SQLAlchemyError: При ошибках работы с БД
        """
        rule = self.activity_rules.get(activity_type)
        if not rule or not rule.is_active:
            raise ValidationError(f"Активность '{activity_type.value}' временно недоступна")
        
        async with self.db.begin():
            try:
                # Проверяем кулдаун
                if rule.cooldown_hours > 0:
                    last_activity = await self.db.execute(
                        """
                        SELECT created_at 
                        FROM user_activity_logs 
                        WHERE user_id = :user_id 
                        AND activity_type = :activity_type
                        ORDER BY created_at DESC 
                        LIMIT 1
                        """,
                        {"user_id": user_id, "activity_type": activity_type.value}
                    )
                    
                    last_time = last_activity.scalar()
                    if last_time:
                        cooldown_until = last_time + timedelta(hours=rule.cooldown_hours)
                        if datetime.utcnow() < cooldown_until:
                            remaining = cooldown_until - datetime.utcnow()
                            remaining_minutes = int(remaining.total_seconds() / 60)
                            raise ValidationError(
                                f"Повторное выполнение будет доступно через {remaining_minutes} минут"
                            )
                
                # Проверяем дневной лимит
                if rule.daily_cap is not None:
                    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                    
                    today_activities = await self.db.execute(
                        """
                        SELECT COUNT(*) 
                        FROM user_activity_logs 
                        WHERE user_id = :user_id 
                        AND activity_type = :activity_type
                        AND created_at >= :today_start
                        """,
                        {
                            "user_id": user_id,
                            "activity_type": activity_type.value,
                            "today_start": today_start
                        }
                    )
                    
                    today_count = today_activities.scalar() or 0
                    if today_count >= rule.daily_cap:
                        raise ValidationError(
                            f"Достигнут дневной лимит начислений за эту активность ({rule.daily_cap} раз в день)"
                        )
                
                # Для гео-проверки проверяем местоположение
                if activity_type == ActivityType.GEO_CHECKIN and location is not None:
                    if not await self._check_location(user_id, location, partner_id):
                        raise ValidationError("Вы находитесь слишком далеко от заведения")
                
                # Начисляем баллы за активность
                description = f"Начисление за активность: {activity_type.value}"
                if partner_id:
                    description += f" (партнер: {partner_id})"
                
                return await self.add_points(
                    user_id=user_id,
                    points=rule.points,
                    transaction_type=LoyaltyTransactionType.ACTIVITY,
                    activity_type=activity_type,
                    reference_id=partner_id,
                    description=description
                )
                
            except Exception as e:
                get_logger(__name__).error(
                    f"Ошибка при обработке активности {activity_type} для пользователя {user_id}: {str(e)}"
                )
                await self.db.rollback()
                raise
    
    async def _check_location(
        self, 
        user_id: UUID, 
        location: Tuple[float, float], 
        partner_id: Optional[UUID] = None
    ) -> bool:
        """
        Проверка местоположения пользователя.
        
        Args:
            user_id: ID пользователя
            location: Кортеж (широта, долгота)
            partner_id: ID партнера для проверки расстояния
            
        Returns:
            bool: True если проверка пройдена
            
        Raises:
            ValidationError: Если проверка не пройдена
        """
        if not partner_id:
            return True
            
        try:
            lat, lon = location
            
            # Получаем местоположение партнера
            partner_location = await self.db.execute(
                """
                SELECT ST_X(location::geometry) as lon, ST_Y(location::geometry) as lat, checkin_radius
                FROM partners
                WHERE id = :partner_id
                """,
                {"partner_id": partner_id}
            )
            
            partner = partner_location.mappings().first()
            if not partner:
                raise ValidationError("Партнер не найден")
                
            # Вычисляем расстояние между точками (в метрах)
            distance = await self.db.execute(
                """
                SELECT ST_Distance(
                    ST_SetSRID(ST_MakePoint(:lon1, :lat1), 4326)::geography,
                    ST_SetSRID(ST_MakePoint(:lon2, :lat2), 4326)::geography
                ) as distance
                """,
                {
                    "lon1": lon,
                    "lat1": lat,
                    "lon2": partner['lon'],
                    "lat2": partner['lat']
                }
            )
            
            distance_meters = distance.scalar()
            max_distance = partner.get('checkin_radius', 100)  # По умолчанию 100 метров
            
            if distance_meters > max_distance:
                get_logger(__name__).info(
                    f"Пользователь {user_id} находится слишком далеко от партнера {partner_id}: "
                    f"{distance_meters:.0f}м > {max_distance}м"
                )
                return False
                
            return True
            
        except Exception as e:
            get_logger(__name__).error(
                f"Ошибка при проверке местоположения пользователя {user_id}: {str(e)}"
            )
            return False
    
    async def get_transaction_history(
        self, 
        user_id: UUID, 
        limit: int = 10, 
        offset: int = 0,
        transaction_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Получение истории транзакций пользователя.
        
        Args:
            user_id: ID пользователя
            limit: Максимальное количество записей
            offset: Смещение для пагинации
            transaction_type: Фильтр по типу транзакции
            start_date: Начальная дата для фильтрации
            end_date: Конечная дата для фильтрации
            
        Returns:
            Dict: Список транзакций и общее количество
        """
        try:
            # Базовый запрос
            query = """
                SELECT 
                    id, 
                    user_id, 
                    points, 
                    transaction_type,
                    activity_type,
                    reference_id,
                    description,
                    created_at,
                    COUNT(*) OVER() as total_count
                FROM loyalty_transactions
                WHERE user_id = :user_id
            """
            
            params = {"user_id": user_id}
            conditions = []
            
            # Добавляем фильтры
            if transaction_type:
                conditions.append("transaction_type = :transaction_type")
                params["transaction_type"] = transaction_type
                
            if start_date:
                conditions.append("created_at >= :start_date")
                params["start_date"] = start_date
                
            if end_date:
                # Добавляем 1 день, чтобы включить все транзакции за указанный день
                end_date = end_date.replace(hour=23, minute=59, second=59)
                conditions.append("created_at <= :end_date")
                params["end_date"] = end_date
            
            # Добавляем условия в запрос
            if conditions:
                query += " AND " + " AND ".join(conditions)
            
            # Добавляем сортировку и пагинацию
            query += """
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """
            
            params["limit"] = limit
            params["offset"] = offset
            
            # Выполняем запрос
            result = await self.db.execute(query, params)
            rows = result.mappings().all()
            
            # Преобразуем результат
            transactions = []
            total_count = 0
            
            for row in rows:
                if total_count == 0 and 'total_count' in row:
                    total_count = row['total_count']
                
                transaction = {
                    "id": row["id"],
                    "points": row["points"],
                    "type": row["transaction_type"],
                    "activity_type": row["activity_type"],
                    "reference_id": row["reference_id"],
                    "description": row["description"],
                    "created_at": row["created_at"]
                }
                
                # Добавляем информацию о партнере, если есть reference_id
                if row["reference_id"] and row["activity_type"] == "geo_checkin":
                    partner_info = await self._get_partner_info(row["reference_id"])
                    if partner_info:
                        transaction["partner"] = partner_info
                
                transactions.append(transaction)
            
            # Получаем сводную статистику
            summary = await self._get_transaction_summary(user_id, transaction_type, start_date, end_date)
            
            return {
                "transactions": transactions,
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "summary": summary
            }
            
        except Exception as e:
            get_logger(__name__).error(
                f"Ошибка при получении истории транзакций пользователя {user_id}: {str(e)}"
            )
            return {
                "transactions": [],
                "total_count": 0,
                "limit": limit,
                "offset": offset,
                "summary": {
                    "total_earned": 0,
                    "total_spent": 0,
                    "by_type": {}
                },
                "error": str(e)
            }
    
    async def _get_transaction_summary(
        self, 
        user_id: UUID, 
        transaction_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Получение сводной статистики по транзакциям."""
        try:
            # Запрос для получения общей суммы начисленных и списанных баллов
            query = """
                SELECT 
                    SUM(CASE WHEN points > 0 THEN points ELSE 0 END) as total_earned,
                    ABS(SUM(CASE WHEN points < 0 THEN points ELSE 0 END)) as total_spent
                FROM loyalty_transactions
                WHERE user_id = :user_id
            """
            
            params = {"user_id": user_id}
            conditions = []
            
            # Добавляем фильтры
            if transaction_type:
                conditions.append("transaction_type = :transaction_type")
                params["transaction_type"] = transaction_type
                
            if start_date:
                conditions.append("created_at >= :start_date")
                params["start_date"] = start_date
                
            if end_date:
                end_date = end_date.replace(hour=23, minute=59, second=59)
                conditions.append("created_at <= :end_date")
                params["end_date"] = end_date
            
            if conditions:
                query += " AND " + " AND ".join(conditions)
            
            result = await self.db.execute(query, params)
            summary = result.mappings().first()
            
            # Запрос для получения статистики по типам транзакций
            type_query = """
                SELECT 
                    transaction_type,
                    COUNT(*) as count,
                    SUM(CASE WHEN points > 0 THEN points ELSE 0 END) as earned,
                    ABS(SUM(CASE WHEN points < 0 THEN points ELSE 0 END)) as spent
                FROM loyalty_transactions
                WHERE user_id = :user_id
            """
            
            if conditions:
                type_query += " AND " + " AND ".join(conditions)
                
            type_query += " GROUP BY transaction_type"
            
            type_result = await self.db.execute(type_query, params)
            by_type = {}
            
            for row in type_result.mappings():
                by_type[row["transaction_type"]] = {
                    "count": row["count"],
                    "earned": row["earned"] or 0,
                    "spent": row["spent"] or 0
                }
            
            return {
                "total_earned": summary["total_earned"] or 0,
                "total_spent": summary["total_spent"] or 0,
                "by_type": by_type
            }
            
        except Exception as e:
            get_logger(__name__).error(
                f"Ошибка при получении сводной статистики для пользователя {user_id}: {str(e)}"
            )
            return {
                "total_earned": 0,
                "total_spent": 0,
                "by_type": {}
            }
    
    async def _get_partner_info(self, partner_id: UUID) -> Optional[Dict[str, Any]]:
        """Получение информации о партнере."""
        try:
            result = await self.db.execute(
                """
                SELECT id, name, description, logo_url
                FROM partners
                WHERE id = :partner_id
                """,
                {"partner_id": partner_id}
            )
            
            partner = result.mappings().first()
            if not partner:
                return None
                
            return {
                "id": partner["id"],
                "name": partner["name"],
                "description": partner.get("description"),
                "logo_url": partner.get("logo_url")
            }
            
        except Exception as e:
            get_logger(__name__).error(
                f"Ошибка при получении информации о партнере {partner_id}: {str(e)}"
            )
            return None
    
    # Реферальная программа
    
    async def generate_referral_code(self, user_id: UUID) -> str:
        """
        Генерация реферального кода для пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            str: Сгенерированный реферальный код
            
        Raises:
            ValidationError: Если не удалось сгенерировать уникальный код
            SQLAlchemyError: При ошибках работы с БД
        """
        # Проверяем, есть ли у пользователя уже реферальный код
        existing_code = await self.get_user_referral_code(user_id)
        if existing_code:
            return existing_code
            
        # Генерируем уникальный код
        max_attempts = 3
        for attempt in range(max_attempts):
            # Создаем код на основе ID пользователя и случайного числа
            random_suffix = str(uuid4().int % 10000).zfill(4)
            code = f"REF{user_id.hex[:4].upper()}{random_suffix}"
            
            # Проверяем уникальность кода
            is_unique = await self._is_referral_code_unique(code)
            if is_unique:
                # Сохраняем код в БД
                try:
                    await self.db.execute(
                        """
                        INSERT INTO referral_links (user_id, referral_code, is_active)
                        VALUES (:user_id, :code, true)
                        ON CONFLICT (user_id) 
                        DO UPDATE SET referral_code = EXCLUDED.referral_code, is_active = true
                        """,
                        {"user_id": user_id, "code": code}
                    )
                    return code
                except Exception as e:
                    get_logger(__name__).error(
                        f"Ошибка при сохранении реферального кода для пользователя {user_id}: {str(e)}"
                    )
                    if attempt == max_attempts - 1:
                        raise ValidationError("Не удалось сгенерировать реферальный код")
        
        # Если не удалось сгенерировать уникальный код
        raise ValidationError("Не удалось сгенерировать реферальный код, попробуйте позже")
    
    async def _is_referral_code_unique(self, code: str) -> bool:
        """Проверка уникальности реферального кода."""
        try:
            result = await self.db.execute(
                "SELECT 1 FROM referral_links WHERE referral_code = :code",
                {"code": code}
            )
            return not bool(result.scalar())
        except Exception as e:
            get_logger(__name__).error(
                f"Ошибка при проверке уникальности кода {code}: {str(e)}"
            )
            return False
    
    async def get_user_referral_code(self, user_id: UUID) -> Optional[str]:
        """
        Получение реферального кода пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Optional[str]: Реферальный код или None, если не найден
        """
        try:
            result = await self.db.execute(
                """
                SELECT referral_code 
                FROM referral_links 
                WHERE user_id = :user_id AND is_active = true
                """,
                {"user_id": user_id}
            )
            return result.scalar()
        except Exception as e:
            get_logger(__name__).error(
                f"Ошибка при получении реферального кода пользователя {user_id}: {str(e)}"
            )
            return None
    
    async def process_referral(
        self,
        referrer_id: UUID,
        referee_id: UUID,
        referral_code: str
    ) -> bool:
        """Обработка реферального приглашения."""
        try:
            # Проверяем, что пользователь не приглашал сам себя
            if referrer_id == referee_id:
                raise ValidationError("Нельзя пригласить самого себя")
            
            # Проверяем, что реферальный код существует и активен
            async with self.db.begin():
                link_query = await self.db.execute(
                    select(ReferralLink)
                    .where(and_(
                        ReferralLink.referral_code == referral_code,
                        ReferralLink.is_active == True
                    ))
                )
                referral_link = link_query.scalar_one_or_none()
                
                if not referral_link:
                    raise ValidationError("Недействительный реферальный код")
                
                if referral_link.user_id != referrer_id:
                    raise ValidationError("Реферальный код принадлежит другому пользователю")
                
                # Проверяем, что реферал еще не зарегистрирован
                existing_query = await self.db.execute(
                    select(Referral.id)
                    .where(Referral.referee_id == referee_id)
                )
                if existing_query.scalar_one_or_none():
                    raise ValidationError("Пользователь уже зарегистрирован по реферальной ссылке")
                
                # Создаем запись о реферале
                referral = Referral(
                    referrer_id=referrer_id,
                    referee_id=referee_id,
                    referral_code=referral_code,
                    referrer_bonus_awarded=False,
                    referee_bonus_awarded=False
                )
                
                self.db.add(referral)
                await self.db.flush()  # Получаем ID
                
                # Начисляем бонусы приглашающему и приглашенному
                referrer_bonus = 100  # Бонус приглашающему
                referee_bonus = 50    # Бонус приглашенному
                
                # Бонус приглашающему
                await self.award_points(
                    user_id=referrer_id,
                    points=referrer_bonus,
                    transaction_type=LoyaltyTransactionType.REFERRAL_BONUS,
                    description=f"Бонус за приглашение пользователя {referee_id}",
                    reference_id=referral.id
                )
                
                # Бонус приглашенному
                await self.award_points(
                    user_id=referee_id,
                    points=referee_bonus,
                    transaction_type=LoyaltyTransactionType.REFERRAL_BONUS,
                    description=f"Бонус за регистрацию по реферальной ссылке",
                    reference_id=referral.id
                )
                
                # Обновляем статус начисления бонусов
                referral.referrer_bonus_awarded = True
                referral.referee_bonus_awarded = True
                referral.bonus_awarded_at = datetime.utcnow()
                
                await self.db.commit()
                
                logger.info(f"Processed referral: {referrer_id} -> {referee_id} (code: {referral_code})")
                return True
                
        except SQLAlchemyError as e:
            logger.error(f"Error processing referral: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing referral: {e}")
            raise
    
    async def process_referral_signup(self, user_id: UUID, referral_code: str) -> Dict[str, Any]:
        """
        Обработка регистрации по реферальной ссылке.
        
        Args:
            user_id: ID нового пользователя (реферала)
            referral_code: Реферальный код
            
        Returns:
            Dict: Информация о реферере и начисленных бонусах
            
        Raises:
            ValidationError: Если код недействителен или уже использован
            SQLAlchemyError: При ошибках работы с БД
        """
        if not referral_code:
            raise ValidationError("Не указан реферальный код")
            
        async with self.db.begin():
            try:
                # Получаем реферера по коду
                referrer_result = await self.db.execute(
                    """
                    SELECT user_id 
                    FROM referral_links 
                    WHERE referral_code = :code AND is_active = true
                    """,
                    {"code": referral_code}
                )
                
                referrer_id = referrer_result.scalar()
                if not referrer_id:
                    raise ValidationError("Недействительный реферальный код")
                
                if referrer_id == user_id:
                    raise ValidationError("Нельзя использовать собственный реферальный код")
                
                # Проверяем, не использовал ли уже пользователь реферальный код
                existing_referral = await self.db.execute(
                    """
                    SELECT 1 
                    FROM referrals 
                    WHERE referee_id = :user_id
                    """,
                    {"user_id": user_id}
                )
                
                if existing_referral.scalar():
                    raise ValidationError("Вы уже использовали реферальный код")
                
                # Записываем факт использования реферального кода
                await self.db.execute(
                    """
                    INSERT INTO referrals 
                        (referrer_id, referee_id, referral_code)
                    VALUES 
                        (:referrer_id, :referee_id, :referral_code)
                    """,
                    {
                        "referrer_id": referrer_id,
                        "referee_id": user_id,
                        "referral_code": referral_code
                    }
                )
                
                # Получаем настройки реферальной программы
                program = self.referral_program
                
                # Начисляем бонусы рефереру
                if program.referrer_bonus > 0:
                    await self.add_points(
                        user_id=referrer_id,
                        points=program.referrer_bonus,
                        transaction_type=LoyaltyTransactionType.REFERRAL_BONUS,
                        activity_type=ActivityType.REFERRAL_SIGNUP,
                        reference_id=user_id,
                        description=f"Бонус за приглашение пользователя {user_id}"
                    )
                
                # Начисляем бонусы рефералу
                if program.referee_bonus > 0:
                    await self.add_points(
                        user_id=user_id,
                        points=program.referee_bonus,
                        transaction_type=LoyaltyTransactionType.REFERRAL_BONUS,
                        activity_type=ActivityType.REFERRAL_SIGNUP,
                        reference_id=referrer_id,
                        description=f"Бонус за регистрацию по приглашению от {referrer_id}"
                    )
                
                # Обновляем статус начисления бонусов
                await self.db.execute(
                    """
                    UPDATE referrals
                    SET 
                        referrer_bonus_awarded = :ref_bonus_given,
                        referee_bonus_awarded = :referee_bonus_given,
                        bonus_awarded_at = NOW()
                    WHERE referee_id = :user_id
                    """,
                    {
                        "user_id": user_id,
                        "ref_bonus_given": program.referrer_bonus > 0,
                        "referee_bonus_given": program.referee_bonus > 0
                    }
                )
                
                # Получаем информацию о реферере для возврата
                referrer_info = await self._get_user_info(referrer_id)
                
                return {
                    "referrer_id": referrer_id,
                    "referrer_name": referrer_info.get("name", "Пользователь"),
                    "referral_code": referral_code,
                    "referrer_bonus": program.referrer_bonus,
                    "referee_bonus": program.referee_bonus
                }
                
            except Exception as e:
                get_logger(__name__).error(
                    f"Ошибка при обработке реферальной регистрации пользователя {user_id}: {str(e)}"
                )
                await self.db.rollback()
                raise
    
    async def _get_user_info(self, user_id: UUID) -> Dict[str, Any]:
        """Получение информации о пользователе."""
        try:
            result = await self.db.execute(
                """
                SELECT id, first_name, last_name, username
                FROM users
                WHERE id = :user_id
                """,
                {"user_id": user_id}
            )
            
            row = result.mappings().first()
            if not row:
                return {}
                
            return {
                "id": row["id"],
                "name": f"{row.get('first_name', '')} {row.get('last_name', '')}".strip() or row.get('username', 'Пользователь')
            }
            
        except Exception as e:
            get_logger(__name__).error(
                f"Ошибка при получении информации о пользователе {user_id}: {str(e)}"
            )
            return {}
    
    async def get_referral_stats(self, user_id: UUID) -> Dict[str, Any]:
        """
        Получение полной статистики по реферальной программе.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Dict: Статистика реферальной программы
        """
        try:
            # Получаем реферальный код пользователя
            referral_code = await self.get_user_referral_code(user_id)
            
            # Если у пользователя еще нет кода, генерируем его
            if not referral_code:
                referral_code = await self.generate_referral_code(user_id)
            
            # Получаем общее количество рефералов
            total_referrals_result = await self.db.execute(
                """
                SELECT COUNT(*) 
                FROM referrals 
                WHERE referrer_id = :user_id
                """,
                {"user_id": user_id}
            )
            
            # Получаем количество активных рефералов (которые выполнили условия)
            active_referrals_result = await self.db.execute(
                """
                SELECT COUNT(DISTINCT r.referee_id)
                FROM referrals r
                JOIN loyalty_transactions t ON t.user_id = r.referee_id
                WHERE r.referrer_id = :user_id
                AND t.transaction_type = 'activity'
                """,
                {"user_id": user_id}
            )
            
            # Получаем общее количество заработанных бонусов
            earned_bonuses_result = await self.db.execute(
                """
                SELECT COALESCE(SUM(points), 0)
                FROM loyalty_transactions
                WHERE user_id = :user_id
                AND transaction_type = 'referral_bonus'
                """,
                {"user_id": user_id}
            )
            
            # Получаем количество бонусов по типам
            bonus_by_type_result = await self.db.execute(
                """
                SELECT 
                    CASE 
                        WHEN description LIKE '%приглашение%' THEN 'referrer_bonus'
                        WHEN description LIKE '%регистрацию по приглашению%' THEN 'referee_bonus'
                        ELSE 'other'
                    END as bonus_type,
                    COUNT(*) as count,
                    SUM(points) as total_points
                FROM loyalty_transactions
                WHERE user_id = :user_id
                AND transaction_type = 'referral_bonus'
                GROUP BY bonus_type
                """,
                {"user_id": user_id}
            )
            
            # Получаем список последних рефералов с их активностью
            recent_referrals = await self.db.execute(
                """
                SELECT 
                    r.referee_id as user_id,
                    u.first_name,
                    u.last_name,
                    u.username,
                    u.photo_url,
                    r.created_at as joined_at,
                    (SELECT COUNT(*) > 0 FROM loyalty_transactions 
                     WHERE user_id = r.referee_id 
                     AND transaction_type = 'activity' 
                     LIMIT 1) as is_active,
                    (SELECT COALESCE(SUM(points), 0) FROM loyalty_transactions 
                     WHERE user_id = r.referee_id) as total_points
                FROM referrals r
                LEFT JOIN users u ON r.referee_id = u.id
                WHERE r.referrer_id = :user_id
                ORDER BY r.created_at DESC
                LIMIT 10
                """,
                {"user_id": user_id}
            )
            
            # Форматируем результат
            referrals_list = []
            for row in recent_referrals.mappings():
                name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
                if not name:
                    name = row.get('username', 'Пользователь')
                
                referrals_list.append({
                    "user_id": row["user_id"],
                    "name": name,
                    "photo_url": row.get("photo_url"),
                    "joined_at": row["joined_at"],
                    "is_active": bool(row["is_active"] if row["is_active"] is not None else False),
                    "total_points": row["total_points"] or 0
                })
            
            # Форматируем бонусы по типам
            bonus_by_type = {}
            for row in bonus_by_type_result.mappings():
                bonus_by_type[row["bonus_type"]] = {
                    "count": row["count"],
                    "total_points": row["total_points"] or 0
                }
            
            # Получаем настройки реферальной программы
            program = self.referral_program
            
            return {
                "total_referrals": total_referrals_result.scalar() or 0,
                "active_referrals": active_referrals_result.scalar() or 0,
                "total_bonus_earned": earned_bonuses_result.scalar() or 0,
                "referral_code": referral_code,
                "referral_link": f"https://t.me/your_bot?start=ref{referral_code}",
                "recent_referrals": referrals_list,
                "bonus_by_type": bonus_by_type,
                "referral_bonus": program.referrer_bonus,
                "referee_bonus": program.referee_bonus,
                "min_withdrawal": program.min_withdrawal,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            get_logger(__name__).error(
                f"Ошибка при получении статистики рефералов для пользователя {user_id}: {str(e)}"
            )
            return {
                "total_referrals": 0,
                "active_referrals": 0,
                "total_bonus_earned": 0,
                "referral_code": "",
                "referral_link": "",
                "recent_referrals": [],
                "bonus_by_type": {},
                "error": str(e)
            }
