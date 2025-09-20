from fastapi import APIRouter, HTTPException, Depends, Header, Query
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, EmailStr, validator
from core.database.enhanced_unified_service import enhanced_unified_db
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# === МОДЕЛИ ДАННЫХ ===

class TelegramUserCreate(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    @validator('telegram_id')
    def validate_telegram_id(cls, v):
        if v <= 0 or v > 999999999999:
            raise ValueError('Invalid telegram_id')
        return v

class WebsiteUserCreate(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password_hash: Optional[str] = None
    email_verified: bool = False

class MobileUserCreate(BaseModel):
    device_id: str
    platform: str  # 'ios' или 'android'
    username: Optional[str] = None
    first_name: Optional[str] = None
    app_version: Optional[str] = "1.0.0"
    push_token: Optional[str] = None
    
    @validator('platform')
    def validate_platform(cls, v):
        if v.lower() not in ['ios', 'android']:
            raise ValueError('Platform must be ios or android')
        return v.lower()

class DesktopUserCreate(BaseModel):
    user_id: str
    platform: str  # 'windows', 'mac', 'linux'
    username: Optional[str] = None
    first_name: Optional[str] = None
    app_version: Optional[str] = "1.0.0"
    
    @validator('platform')
    def validate_platform(cls, v):
        if v.lower() not in ['windows', 'mac', 'linux']:
            raise ValueError('Platform must be windows, mac, or linux')
        return v.lower()

class OrderCreate(BaseModel):
    items: List[Dict]
    total_amount: float
    currency: str = "USD"
    payment_method: Optional[str] = None
    delivery_address: Optional[str] = None
    
    @validator('total_amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v

class SyncData(BaseModel):
    data: Dict
    version: Optional[str] = "1.0"
    timestamp: Optional[str] = None

class LinkAccountData(BaseModel):
    telegram_id: Optional[int] = None
    email: Optional[str] = None
    device_id: Optional[str] = None

# === DEPENDENCY FUNCTIONS ===

async def verify_api_key(x_api_key: str = Header(None)):
    """Проверка API ключа для партнерских запросов"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    # Простая проверка API ключа (в реальности - база данных)
    valid_prefixes = ['pk_live_', 'pk_test_', 'api_key_']
    if not any(x_api_key.startswith(prefix) for prefix in valid_prefixes):
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return x_api_key

async def verify_admin_token(authorization: str = Header(None)):
    """Проверка токена администратора"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization token required")
    
    token = authorization.split(" ")[1]
    # В реальности здесь должна быть проверка JWT токена
    if token != "admin_secret_token_2025":
        raise HTTPException(status_code=403, detail="Invalid admin token")
    
    return token

# === РОУТЕРЫ ===

telegram_router = APIRouter(prefix="/telegram", tags=["Telegram Bot"])
website_router = APIRouter(prefix="/website", tags=["Website"])
mobile_router = APIRouter(prefix="/mobile", tags=["Mobile Apps"])
desktop_router = APIRouter(prefix="/desktop", tags=["Desktop Apps"])
universal_router = APIRouter(prefix="/universal", tags=["Cross-Platform"])
admin_router = APIRouter(prefix="/admin", tags=["Administration"])
api_router = APIRouter(prefix="/api", tags=["Partner API"])

# === TELEGRAM ENDPOINTS ===

@telegram_router.post("/users/", response_model=Dict)
async def create_telegram_user(user: TelegramUserCreate):
    """Создать пользователя Telegram"""
    try:
        user_uuid = enhanced_unified_db.create_telegram_user(user.telegram_id, user.dict())
        if user_uuid:
            return {
                "status": "success", 
                "user_uuid": user_uuid,
                "platform": "telegram",
                "created_at": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create user")
    except Exception as e:
        logger.error(f"Error creating Telegram user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@telegram_router.get("/users/{telegram_id}")
async def get_telegram_user(telegram_id: int):
    """Получить информацию о пользователе Telegram"""
    user_info = enhanced_unified_db.get_telegram_user_info(telegram_id)
    if user_info:
        return user_info
    else:
        raise HTTPException(status_code=404, detail="User not found")

@telegram_router.post("/users/{telegram_id}/orders")
async def create_telegram_order(telegram_id: int, order: OrderCreate):
    """Создать заказ от Telegram пользователя"""
    order_id = enhanced_unified_db.create_telegram_order(telegram_id, order.dict())
    if order_id:
        return {
            "status": "success", 
            "order_id": order_id,
            "platform": "telegram",
            "user_id": telegram_id,
            "created_at": datetime.utcnow().isoformat()
        }
    else:
        raise HTTPException(status_code=400, detail="Failed to create order")

@telegram_router.get("/users/{telegram_id}/loyalty")
async def get_telegram_loyalty(telegram_id: int):
    """Получить информацию о лояльности"""
    loyalty_info = enhanced_unified_db.get_telegram_loyalty(telegram_id)
    return loyalty_info

@telegram_router.get("/users/{telegram_id}/orders")
async def get_telegram_orders(telegram_id: int, limit: int = Query(10, ge=1, le=100)):
    """Получить заказы пользователя"""
    orders = enhanced_unified_db.get_telegram_orders(telegram_id, limit)
    return {"orders": orders, "count": len(orders)}

# === WEBSITE ENDPOINTS ===

@website_router.post("/users/")
async def create_website_user(user: WebsiteUserCreate):
    """Создать пользователя сайта"""
    try:
        user_uuid = enhanced_unified_db.create_website_user(user.email, user.dict())
        if user_uuid:
            return {
                "status": "success", 
                "user_uuid": user_uuid,
                "platform": "website",
                "email": user.email,
                "created_at": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create user")
    except Exception as e:
        logger.error(f"Error creating website user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@website_router.get("/users/{email}")
async def get_website_user(email: str):
    """Получить информацию о пользователе сайта"""
    user_info = enhanced_unified_db.get_website_user_info(email)
    if user_info:
        return user_info
    else:
        raise HTTPException(status_code=404, detail="User not found")

@website_router.put("/users/{email}/profile")
async def update_website_profile(email: str, profile_data: Dict):
    """Обновить профиль пользователя"""
    success = enhanced_unified_db.update_website_profile(email, profile_data)
    if success:
        return {
            "status": "success", 
            "message": "Profile updated",
            "updated_at": datetime.utcnow().isoformat()
        }
    else:
        raise HTTPException(status_code=400, detail="Failed to update profile")

@website_router.post("/users/{email}/link-telegram")
async def link_telegram_account(email: str, link_data: LinkAccountData):
    """Связать аккаунт сайта с Telegram"""
    if not link_data.telegram_id:
        raise HTTPException(status_code=400, detail="telegram_id is required")
    
    success = enhanced_unified_db.link_telegram_to_website(email, link_data.telegram_id)
    if success:
        return {
            "status": "success", 
            "message": "Accounts linked successfully",
            "linked_at": datetime.utcnow().isoformat()
        }
    else:
        raise HTTPException(status_code=400, detail="Failed to link accounts")

@website_router.post("/users/{email}/orders")
async def create_website_order(email: str, order: OrderCreate):
    """Создать заказ от веб-пользователя"""
    order_id = enhanced_unified_db.create_website_order(email, order.dict())
    if order_id:
        return {
            "status": "success", 
            "order_id": order_id,
            "platform": "website",
            "user_email": email,
            "created_at": datetime.utcnow().isoformat()
        }
    else:
        raise HTTPException(status_code=400, detail="Failed to create order")

@website_router.get("/users/{email}/loyalty")
async def get_website_loyalty(email: str):
    """Получить информацию о лояльности"""
    return enhanced_unified_db.get_website_loyalty(email)

# === MOBILE ENDPOINTS ===

@mobile_router.post("/users/")
async def create_mobile_user(user: MobileUserCreate):
    """Создать пользователя мобильного приложения"""
    try:
        user_uuid = enhanced_unified_db.create_mobile_user(user.device_id, user.platform, user.dict())
        if user_uuid:
            return {
                "status": "success", 
                "user_uuid": user_uuid,
                "platform": f"mobile_{user.platform}",
                "device_id": user.device_id,
                "created_at": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create user")
    except Exception as e:
        logger.error(f"Error creating mobile user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@mobile_router.get("/users/{device_id}")
async def get_mobile_user(device_id: str, platform: str = Query(..., regex="^(ios|android)$")):
    """Получить информацию о пользователе приложения"""
    user_info = enhanced_unified_db.get_mobile_user_info(device_id, platform)
    if user_info:
        return user_info
    else:
        raise HTTPException(status_code=404, detail="User not found")

@mobile_router.post("/users/{device_id}/sync")
async def sync_mobile_data(device_id: str, platform: str, sync_data: SyncData):
    """Синхронизировать данные мобильного приложения"""
    result = enhanced_unified_db.sync_mobile_data(device_id, platform, sync_data.dict())
    return result

@mobile_router.post("/users/{device_id}/push-token")
async def register_push_token(device_id: str, platform: str, push_data: Dict):
    """Зарегистрировать токен для push уведомлений"""
    push_token = push_data.get('push_token')
    if not push_token:
        raise HTTPException(status_code=400, detail="push_token is required")
    
    success = enhanced_unified_db.register_mobile_push_token(device_id, platform, push_token)
    if success:
        return {
            "status": "success", 
            "message": "Push token registered",
            "registered_at": datetime.utcnow().isoformat()
        }
    else:
        raise HTTPException(status_code=400, detail="Failed to register push token")

@mobile_router.post("/users/{device_id}/link-accounts")
async def link_mobile_accounts(device_id: str, platform: str, link_data: LinkAccountData):
    """Связать мобильный аккаунт с другими платформами"""
    account_data = {}
    if link_data.telegram_id:
        account_data['telegram_id'] = link_data.telegram_id
    if link_data.email:
        account_data['email'] = link_data.email
    
    if not account_data:
        raise HTTPException(status_code=400, detail="At least one account identifier required")
    
    success = enhanced_unified_db.link_mobile_accounts(device_id, platform, account_data)
    if success:
        return {
            "status": "success", 
            "message": "Accounts linked",
            "linked_accounts": list(account_data.keys()),
            "linked_at": datetime.utcnow().isoformat()
        }
    else:
        raise HTTPException(status_code=400, detail="Failed to link accounts")

@mobile_router.post("/users/{device_id}/orders")
async def create_mobile_order(device_id: str, platform: str, order: OrderCreate):
    """Создать заказ от мобильного пользователя"""
    order_id = enhanced_unified_db.create_mobile_order(device_id, platform, order.dict())
    if order_id:
        return {
            "status": "success", 
            "order_id": order_id,
            "platform": f"mobile_{platform}",
            "device_id": device_id,
            "created_at": datetime.utcnow().isoformat()
        }
    else:
        raise HTTPException(status_code=400, detail="Failed to create order")

# === DESKTOP ENDPOINTS ===

@desktop_router.post("/users/")
async def create_desktop_user(user: DesktopUserCreate):
    """Создать пользователя десктопного приложения"""
    try:
        user_uuid = enhanced_unified_db.create_desktop_user(user.user_id, user.platform, user.dict())
        if user_uuid:
            return {
                "status": "success", 
                "user_uuid": user_uuid,
                "platform": f"desktop_{user.platform}",
                "user_id": user.user_id,
                "created_at": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create user")
    except Exception as e:
        logger.error(f"Error creating desktop user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@desktop_router.get("/users/{user_id}")
async def get_desktop_user(user_id: str, platform: str = Query(..., regex="^(windows|mac|linux)$")):
    """Получить информацию о пользователе десктопа"""
    user_info = enhanced_unified_db.get_desktop_user_info(user_id, platform)
    if user_info:
        return user_info
    else:
        raise HTTPException(status_code=404, detail="User not found")

@desktop_router.post("/users/{user_id}/sync-cloud")
async def sync_desktop_cloud(user_id: str, platform: str, cloud_data: SyncData):
    """Синхронизировать десктопные данные с облаком"""
    result = enhanced_unified_db.sync_desktop_with_cloud(user_id, platform, cloud_data.dict())
    return result

# === UNIVERSAL ENDPOINTS ===

@universal_router.post("/users/search")
async def search_user_across_platforms(identifiers: Dict):
    """Найти пользователя по любому идентификатору"""
    user_info = enhanced_unified_db.get_user_across_platforms(identifiers)
    if user_info:
        return user_info
    else:
        raise HTTPException(status_code=404, detail="User not found on any platform")

@universal_router.post("/orders/cross-platform")
async def create_cross_platform_order(order_data: Dict):
    """Создать заказ с поддержкой кросс-платформенности"""
    user_identifiers = order_data.get('user_identifiers', {})
    primary_platform = order_data.get('primary_platform')
    order_details = order_data.get('order_details', {})
    
    if not user_identifiers or not primary_platform:
        raise HTTPException(status_code=400, detail="user_identifiers and primary_platform are required")
    
    order_id = enhanced_unified_db.create_cross_platform_order(user_identifiers, order_details, primary_platform)
    if order_id:
        return {
            "status": "success", 
            "order_id": order_id,
            "primary_platform": primary_platform,
            "created_at": datetime.utcnow().isoformat()
        }
    else:
        raise HTTPException(status_code=400, detail="Failed to create order")

@universal_router.post("/loyalty/unified")
async def get_unified_loyalty(identifiers: Dict):
    """Получить объединенную информацию о лояльности"""
    loyalty_info = enhanced_unified_db.get_unified_loyalty_info(identifiers)
    return loyalty_info

@universal_router.post("/users/sync-platforms")
async def sync_user_across_platforms(sync_request: Dict):
    """Синхронизировать пользователя между всеми связанными платформами"""
    primary_identifier = sync_request.get('primary_identifier')
    primary_platform = sync_request.get('primary_platform')
    sync_data = sync_request.get('sync_data', {})
    
    if not primary_identifier or not primary_platform:
        raise HTTPException(status_code=400, detail="primary_identifier and primary_platform are required")
    
    result = enhanced_unified_db.sync_user_across_platforms(primary_identifier, primary_platform, sync_data)
    return result

@universal_router.get("/statistics/platforms")
async def get_platform_statistics():
    """Получить статистику по всем платформам"""
    return enhanced_unified_db.get_platform_statistics()

# === ADMIN ENDPOINTS ===

@admin_router.get("/status", dependencies=[Depends(verify_admin_token)])
async def get_system_status():
    """Получить статус всей системы"""
    return enhanced_unified_db.get_admin_dashboard_data()

@admin_router.post("/sync", dependencies=[Depends(verify_admin_token)])
async def force_system_sync():
    """Принудительная синхронизация системы"""
    return enhanced_unified_db.force_system_sync()

@admin_router.get("/report", dependencies=[Depends(verify_admin_token)])
async def export_system_report():
    """Экспорт полного отчета о системе"""
    return enhanced_unified_db.export_system_report()

@admin_router.get("/health")
async def health_check():
    """Быстрая проверка здоровья (без авторизации)"""
    status = enhanced_unified_db.health_check()
    return {
        "status": "ok" if status['health']['overall'] else "degraded",
        "mode": status['mode'],
        "timestamp": status['timestamp'],
        "uptime": {
            "postgresql": status['uptime']['postgresql'],
            "supabase": status['uptime']['supabase'],
            "overall": status['uptime']['overall']
        }
    }

# === PARTNER API ENDPOINTS ===

@api_router.post("/orders", dependencies=[Depends(verify_api_key)])
async def create_api_order(order_data: Dict, api_key: str = Depends(verify_api_key)):
    """Создать заказ через партнерский API"""
    external_user_id = order_data.get('external_user_id')
    order_details = order_data.get('order_details', {})
    
    if not external_user_id:
        raise HTTPException(status_code=400, detail="external_user_id is required")
    
    order_id = enhanced_unified_db.create_api_order(api_key, external_user_id, order_details)
    if order_id:
        return {
            "status": "success", 
            "order_id": order_id,
            "external_user_id": external_user_id,
            "created_at": datetime.utcnow().isoformat()
        }
    else:
        raise HTTPException(status_code=400, detail="Failed to create order")

@api_router.get("/users/{external_user_id}", dependencies=[Depends(verify_api_key)])
async def get_api_user(external_user_id: str, api_key: str = Depends(verify_api_key)):
    """Получить информацию о внешнем пользователе"""
    user_info = enhanced_unified_db.get_api_user_info(api_key, external_user_id)
    if user_info:
        return user_info
    else:
        raise HTTPException(status_code=404, detail="User not found")

# === ГЛАВНЫЙ РОУТЕР ===

main_router = APIRouter()
main_router.include_router(telegram_router)
main_router.include_router(website_router)
main_router.include_router(mobile_router)
main_router.include_router(desktop_router)
main_router.include_router(universal_router)
main_router.include_router(admin_router)
main_router.include_router(api_router)

# === ДОПОЛНИТЕЛЬНЫЕ ENDPOINTS ===

@main_router.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "service": "Fault-Tolerant Multi-Platform System",
        "version": "1.0.0",
        "status": "operational",
        "platforms": ["telegram", "website", "mobile", "desktop", "api"],
        "docs": "/docs",
        "dashboard": "/dashboard",
        "health": "/admin/health"
    }

@main_router.get("/platforms")
async def get_supported_platforms():
    """Получить список поддерживаемых платформ"""
    return {
        "platforms": {
            "telegram": {"name": "Telegram Bot", "endpoint": "/telegram"},
            "website": {"name": "Website", "endpoint": "/website"},
            "mobile": {"name": "Mobile Apps", "endpoint": "/mobile", "types": ["ios", "android"]},
            "desktop": {"name": "Desktop Apps", "endpoint": "/desktop", "types": ["windows", "mac", "linux"]},
            "api": {"name": "Partner API", "endpoint": "/api"}
        },
        "universal": {
            "search": "/universal/users/search",
            "cross_platform_orders": "/universal/orders/cross-platform",
            "unified_loyalty": "/universal/loyalty/unified"
        },
        "admin": {
            "status": "/admin/status",
            "health": "/admin/health",
            "sync": "/admin/sync"
        }
    }
