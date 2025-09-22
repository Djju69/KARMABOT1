# Минимальные заглушки для совместимости

from aiogram.fsm.state import State, StatesGroup

class LoyaltySettingsStates(StatesGroup):
    """Состояния для настроек лояльности"""
    waiting_for_choice = State()
    waiting_for_setting_choice = State()
    waiting_for_redeem_rate = State()
    waiting_for_min_purchase = State()
    waiting_for_max_discount = State()
    waiting_for_max_percent_bill = State()
    waiting_for_bonus_points_usage = State()
    waiting_for_confirmation = State()

# Заглушки для функций
async def handle_setting_choice(*args, **kwargs):
    """Заглушка для обработки выбора настроек"""
    pass

async def handle_redeem_rate(*args, **kwargs):
    """Заглушка для обработки ставки погашения"""
    pass

async def handle_min_purchase(*args, **kwargs):
    """Заглушка для обработки минимальной покупки"""
    pass

async def handle_max_discount(*args, **kwargs):
    """Заглушка для обработки максимальной скидки"""
    pass

async def handle_max_percent_bill(*args, **kwargs):
    """Заглушка для обработки границы закрытия чека"""
    pass

async def handle_bonus_points_usage(*args, **kwargs):
    """Заглушка для обработки дополнительной скидки при оплате баллами"""
    pass

async def handle_confirmation(*args, **kwargs):
    """Заглушка для обработки подтверждения"""
    pass
