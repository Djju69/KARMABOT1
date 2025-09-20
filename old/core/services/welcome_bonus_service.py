"""
Welcome Bonus Service - система поэтапных бонусов для новых пользователей
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class WelcomeBonusService:
    """Сервис для управления Welcome бонусами с поэтапной разблокировкой"""
    
    def __init__(self):
        self.stages = {
            0: {"name": "Новый пользователь", "bonus": 51, "description": "Доступно сразу"},
            1: {"name": "Первая покупка", "bonus": 67, "description": "После 1-й покупки"},
            2: {"name": "Вторая покупка", "bonus": 50, "description": "После 2-й покупки"},
            3: {"name": "Третья покупка", "bonus": 50, "description": "После 3-й покупки"}
        }
    
    async def get_welcome_bonus_config(self) -> Dict[str, Any]:
        """Получить конфигурацию Welcome бонусов"""
        try:
            from core.database.db_v2 import get_connection
            
            with get_connection() as conn:
                cursor = conn.execute("""
                    SELECT welcome_bonus_immediate, welcome_unlock_stage_1, 
                           welcome_unlock_stage_2, welcome_unlock_stage_3
                    FROM platform_loyalty_config 
                    ORDER BY id DESC LIMIT 1
                """)
                result = cursor.fetchone()
                
                if result:
                    immediate, stage1, stage2, stage3 = result
                    return {
                        "immediate": immediate,
                        "stage_1": stage1,
                        "stage_2": stage2,
                        "stage_3": stage3,
                        "total": immediate + stage1 + stage2 + stage3
                    }
                else:
                    # Дефолтные значения
                    return {
                        "immediate": 51,
                        "stage_1": 67,
                        "stage_2": 50,
                        "stage_3": 50,
                        "total": 218
                    }
                    
        except Exception as e:
            logger.error(f"Error getting welcome bonus config: {e}")
            return {
                "immediate": 51,
                "stage_1": 67,
                "stage_2": 50,
                "stage_3": 50,
                "total": 218
            }
    
    async def get_user_welcome_status(self, user_id: int) -> Dict[str, Any]:
        """Получить статус Welcome бонусов пользователя"""
        try:
            from core.database.db_v2 import get_connection
            
            with get_connection() as conn:
                # Получаем текущий этап пользователя
                cursor = conn.execute("""
                    SELECT welcome_stage FROM users WHERE telegram_id = ?
                """, (user_id,))
                result = cursor.fetchone()
                
                current_stage = result[0] if result else 0
                
                # Получаем количество покупок
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM transactions 
                    WHERE user_id = ? AND transaction_type = 'purchase'
                """, (user_id,))
                purchase_count = cursor.fetchone()[0] if cursor.fetchone() else 0
                
                # Получаем конфигурацию бонусов
                config = await self.get_welcome_bonus_config()
                
                # Определяем доступные бонусы
                available_bonuses = []
                total_available = 0
                
                # Немедленный бонус (всегда доступен)
                available_bonuses.append({
                    "stage": 0,
                    "name": "Добро пожаловать!",
                    "bonus": config["immediate"],
                    "status": "available",
                    "description": "Доступно сразу"
                })
                total_available += config["immediate"]
                
                # Этап 1 (после 1-й покупки)
                if purchase_count >= 1:
                    available_bonuses.append({
                        "stage": 1,
                        "name": "Первая покупка",
                        "bonus": config["stage_1"],
                        "status": "available",
                        "description": "После 1-й покупки"
                    })
                    total_available += config["stage_1"]
                else:
                    available_bonuses.append({
                        "stage": 1,
                        "name": "Первая покупка",
                        "bonus": config["stage_1"],
                        "status": "locked",
                        "description": f"Нужна 1 покупка (осталось {1 - purchase_count})"
                    })
                
                # Этап 2 (после 2-й покупки)
                if purchase_count >= 2:
                    available_bonuses.append({
                        "stage": 2,
                        "name": "Вторая покупка",
                        "bonus": config["stage_2"],
                        "status": "available",
                        "description": "После 2-й покупки"
                    })
                    total_available += config["stage_2"]
                else:
                    available_bonuses.append({
                        "stage": 2,
                        "name": "Вторая покупка",
                        "bonus": config["stage_2"],
                        "status": "locked",
                        "description": f"Нужно 2 покупки (осталось {2 - purchase_count})"
                    })
                
                # Этап 3 (после 3-й покупки)
                if purchase_count >= 3:
                    available_bonuses.append({
                        "stage": 3,
                        "name": "Третья покупка",
                        "bonus": config["stage_3"],
                        "status": "available",
                        "description": "После 3-й покупки"
                    })
                    total_available += config["stage_3"]
                else:
                    available_bonuses.append({
                        "stage": 3,
                        "name": "Третья покупка",
                        "bonus": config["stage_3"],
                        "status": "locked",
                        "description": f"Нужно 3 покупки (осталось {3 - purchase_count})"
                    })
                
                return {
                    "current_stage": current_stage,
                    "purchase_count": purchase_count,
                    "available_bonuses": available_bonuses,
                    "total_available": total_available,
                    "total_possible": config["total"],
                    "progress_percent": (total_available / config["total"]) * 100
                }
                
        except Exception as e:
            logger.error(f"Error getting user welcome status: {e}")
            return {
                "current_stage": 0,
                "purchase_count": 0,
                "available_bonuses": [],
                "total_available": 0,
                "total_possible": 218,
                "progress_percent": 0
            }
    
    async def process_welcome_bonus(self, user_id: int, purchase_count: int) -> Dict[str, Any]:
        """Обработать Welcome бонус после покупки"""
        try:
            from core.database.db_v2 import get_connection
            
            with get_connection() as conn:
                # Получаем текущий этап пользователя
                cursor = conn.execute("""
                    SELECT welcome_stage FROM users WHERE telegram_id = ?
                """, (user_id,))
                result = cursor.fetchone()
                
                current_stage = result[0] if result else 0
                
                # Определяем новый этап
                new_stage = min(purchase_count, 3)
                
                if new_stage > current_stage:
                    # Получаем конфигурацию бонусов
                    config = await self.get_welcome_bonus_config()
                    
                    # Определяем бонус для нового этапа
                    bonus_amount = 0
                    if new_stage == 1:
                        bonus_amount = config["stage_1"]
                    elif new_stage == 2:
                        bonus_amount = config["stage_2"]
                    elif new_stage == 3:
                        bonus_amount = config["stage_3"]
                    
                    if bonus_amount > 0:
                        # Обновляем этап пользователя
                        conn.execute("""
                            UPDATE users SET welcome_stage = ? WHERE telegram_id = ?
                        """, (new_stage, user_id))
                        
                        # Начисляем бонус
                        conn.execute("""
                            UPDATE users SET points_balance = COALESCE(points_balance, 0) + ? 
                            WHERE telegram_id = ?
                        """, (bonus_amount, user_id))
                        
                        # Записываем в историю
                        conn.execute("""
                            INSERT INTO points_history (user_id, change_amount, reason, transaction_type, created_at)
                            VALUES (?, ?, ?, ?, ?)
                        """, (user_id, bonus_amount, f"Welcome бонус этап {new_stage}", "welcome_bonus", datetime.now().isoformat()))
                        
                        conn.commit()
                        
                        return {
                            "success": True,
                            "new_stage": new_stage,
                            "bonus_amount": bonus_amount,
                            "message": f"🎉 Поздравляем! Разблокирован Welcome бонус этапа {new_stage}: +{bonus_amount} баллов!"
                        }
                
                return {
                    "success": False,
                    "message": "Нет новых Welcome бонусов для разблокировки"
                }
                
        except Exception as e:
            logger.error(f"Error processing welcome bonus: {e}")
            return {
                "success": False,
                "message": "Ошибка при обработке Welcome бонуса"
            }

# Создаем экземпляр сервиса
welcome_bonus_service = WelcomeBonusService()
