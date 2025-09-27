"""
Расширенная система достижений с геймификацией
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime

class AchievementType(Enum):
    """Типы достижений"""
    # Базовые достижения
    LEVEL_UP = "level_up"
    KARMA_MILESTONE = "karma_milestone"
    
    # Новые достижения для геймификации
    DAILY_STREAK = "daily_streak"  # Ежедневные входы подряд
    REFERRAL_MASTER = "referral_master"  # Мастер рефералов
    CARD_COLLECTOR = "card_collector"  # Коллекционер карт
    EXPLORER = "explorer"  # Исследователь (посещение разных мест)
    SOCIAL_BUTTERFLY = "social_butterfly"  # Социальная бабочка
    LOYALTY_CHAMPION = "loyalty_champion"  # Чемпион лояльности
    SPEED_DEMON = "speed_demon"  # Скоростной демон
    PERFECTIONIST = "perfectionist"  # Перфекционист
    EARLY_BIRD = "early_bird"  # Ранняя пташка
    NIGHT_OWL = "night_owl"  # Ночная сова
    WEEKEND_WARRIOR = "weekend_warrior"  # Воин выходных
    MONTHLY_CHALLENGER = "monthly_challenger"  # Месячный вызов
    YEARLY_LEGEND = "yearly_legend"  # Годовая легенда

class AchievementRarity(Enum):
    """Редкость достижений"""
    COMMON = "common"  # Обычное
    RARE = "rare"  # Редкое
    EPIC = "epic"  # Эпическое
    LEGENDARY = "legendary"  # Легендарное

@dataclass
class Achievement:
    """Модель достижения"""
    id: Optional[int]
    achievement_type: AchievementType
    name: str
    description: str
    icon: str
    rarity: AchievementRarity
    points_reward: int
    requirements: Dict[str, Any]
    is_active: bool = True
    created_at: Optional[datetime] = None

@dataclass
class UserAchievement:
    """Достижение пользователя"""
    id: Optional[int]
    user_id: int
    achievement_type: AchievementType
    achievement_data: Dict[str, Any]
    earned_at: datetime
    is_notified: bool = False

# Предустановленные достижения
DEFAULT_ACHIEVEMENTS = {
    # Уровневые достижения
    AchievementType.LEVEL_UP: Achievement(
        id=None,
        achievement_type=AchievementType.LEVEL_UP,
        name="Повышение уровня",
        description="Достигните нового уровня",
        icon="📈",
        rarity=AchievementRarity.COMMON,
        points_reward=10,
        requirements={"level": 1}
    ),
    
    # Достижения кармы
    AchievementType.KARMA_MILESTONE: Achievement(
        id=None,
        achievement_type=AchievementType.KARMA_MILESTONE,
        name="Мастер кармы",
        description="Накопите определенное количество кармы",
        icon="💎",
        rarity=AchievementRarity.RARE,
        points_reward=50,
        requirements={"karma": 1000}
    ),
    
    # Ежедневные достижения
    AchievementType.DAILY_STREAK: Achievement(
        id=None,
        achievement_type=AchievementType.DAILY_STREAK,
        name="Ежедневный воин",
        description="Входите в систему каждый день подряд",
        icon="🔥",
        rarity=AchievementRarity.COMMON,
        points_reward=25,
        requirements={"days": 7}
    ),
    
    # Реферальные достижения
    AchievementType.REFERRAL_MASTER: Achievement(
        id=None,
        achievement_type=AchievementType.REFERRAL_MASTER,
        name="Мастер рефералов",
        description="Пригласите определенное количество друзей",
        icon="👥",
        rarity=AchievementRarity.EPIC,
        points_reward=100,
        requirements={"referrals": 10}
    ),
    
    # Достижения карт
    AchievementType.CARD_COLLECTOR: Achievement(
        id=None,
        achievement_type=AchievementType.CARD_COLLECTOR,
        name="Коллекционер карт",
        description="Добавьте определенное количество карт",
        icon="💳",
        rarity=AchievementRarity.RARE,
        points_reward=75,
        requirements={"cards": 5}
    ),
    
    # Достижения исследования
    AchievementType.EXPLORER: Achievement(
        id=None,
        achievement_type=AchievementType.EXPLORER,
        name="Исследователь",
        description="Посетите разные места",
        icon="🗺️",
        rarity=AchievementRarity.RARE,
        points_reward=60,
        requirements={"places": 10}
    ),
    
    # Социальные достижения
    AchievementType.SOCIAL_BUTTERFLY: Achievement(
        id=None,
        achievement_type=AchievementType.SOCIAL_BUTTERFLY,
        name="Социальная бабочка",
        description="Активно взаимодействуйте с системой",
        icon="🦋",
        rarity=AchievementRarity.EPIC,
        points_reward=80,
        requirements={"interactions": 100}
    ),
    
    # Достижения лояльности
    AchievementType.LOYALTY_CHAMPION: Achievement(
        id=None,
        achievement_type=AchievementType.LOYALTY_CHAMPION,
        name="Чемпион лояльности",
        description="Накопите определенное количество баллов лояльности",
        icon="🏆",
        rarity=AchievementRarity.LEGENDARY,
        points_reward=200,
        requirements={"loyalty_points": 5000}
    ),
    
    # Временные достижения
    AchievementType.EARLY_BIRD: Achievement(
        id=None,
        achievement_type=AchievementType.EARLY_BIRD,
        name="Ранняя пташка",
        description="Входите в систему рано утром",
        icon="🌅",
        rarity=AchievementRarity.COMMON,
        points_reward=15,
        requirements={"time_range": "06:00-09:00", "days": 5}
    ),
    
    AchievementType.NIGHT_OWL: Achievement(
        id=None,
        achievement_type=AchievementType.NIGHT_OWL,
        name="Ночная сова",
        description="Входите в систему поздно вечером",
        icon="🦉",
        rarity=AchievementRarity.COMMON,
        points_reward=15,
        requirements={"time_range": "22:00-02:00", "days": 5}
    ),
    
    # Недельные достижения
    AchievementType.WEEKEND_WARRIOR: Achievement(
        id=None,
        achievement_type=AchievementType.WEEKEND_WARRIOR,
        name="Воин выходных",
        description="Активны в выходные дни",
        icon="⚔️",
        rarity=AchievementRarity.RARE,
        points_reward=40,
        requirements={"weekend_days": 4}
    ),
    
    # Месячные достижения
    AchievementType.MONTHLY_CHALLENGER: Achievement(
        id=None,
        achievement_type=AchievementType.MONTHLY_CHALLENGER,
        name="Месячный вызов",
        description="Активны весь месяц",
        icon="📅",
        rarity=AchievementRarity.EPIC,
        points_reward=150,
        requirements={"days_in_month": 25}
    ),
    
    # Годовые достижения
    AchievementType.YEARLY_LEGEND: Achievement(
        id=None,
        achievement_type=AchievementType.YEARLY_LEGEND,
        name="Годовая легенда",
        description="Активны весь год",
        icon="👑",
        rarity=AchievementRarity.LEGENDARY,
        points_reward=500,
        requirements={"days_in_year": 300}
    )
}

# Цвета для разных редкостей
RARITY_COLORS = {
    AchievementRarity.COMMON: "⚪",  # Белый
    AchievementRarity.RARE: "🔵",    # Синий
    AchievementRarity.EPIC: "🟣",    # Фиолетовый
    AchievementRarity.LEGENDARY: "🟡"  # Золотой
}

# Прогресс-бары для достижений
def get_progress_bar(current: int, target: int, length: int = 10) -> str:
    """Создать прогресс-бар для достижения"""
    if target <= 0:
        return "🟩" * length
    
    progress = min(current / target, 1.0)
    filled = int(progress * length)
    empty = length - filled
    
    return "🟩" * filled + "⬜" * empty

def format_achievement_progress(achievement: Achievement, current: int, target: int) -> str:
    """Форматировать прогресс достижения"""
    progress_bar = get_progress_bar(current, target)
    percentage = min(int((current / target) * 100), 100) if target > 0 else 100
    
    return f"{achievement.icon} {achievement.name}\n{progress_bar} {current}/{target} ({percentage}%)"
