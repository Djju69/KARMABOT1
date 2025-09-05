"""
Модуль для работы с админ-панелью и дашбордом.
"""
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from core.database import Database, get_db
from core.security.deps import require_admin, get_current_user
from core.security.roles import Role, get_user_role
from core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

# Инициализация шаблонов
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Подключение статических файлов
def setup_static_files(app):
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Моковые данные для демонстрации (заменить на реальные запросы к БД)
MOCK_STATS = {
    "total_users": 1245,
    "active_users": 842,
    "new_users_today": 24,
    "total_partners": 67,
    "active_partners": 42,
    "pending_partners": 5,
    "total_transactions": 12567,
    "today_transactions": 243,
    "total_revenue": 1245678.90,
    "today_revenue": 24567.89,
    "avg_order_value": 1250.75,
    "conversion_rate": 3.2,
    "active_sessions": 87,
    "avg_session_duration": "4:32"
}

MOCK_ALERTS = [
    {
        "id": 1, 
        "type": "warning", 
        "message": "Высокая нагрузка на сервер: CPU 95%", 
        "time": "10 минут назад",
        "details": "Рекомендуется масштабировать сервис или оптимизировать запросы."
    },
    {
        "id": 2, 
        "type": "error", 
        "message": "Ошибка при обработке платежа #12345", 
        "time": "25 минут назад",
        "details": "Платежный шлюз вернул ошибку авторизации. Требуется проверка настроек интеграции."
    },
    {
        "id": 3, 
        "type": "info", 
        "message": "Завершено резервное копирование базы данных", 
        "time": "2 часа назад",
        "details": "Резервная копия успешно создана и загружена в облачное хранилище."
    },
    {
        "id": 4,
        "type": "warning",
        "message": "Обнаружено 5 необработанных заявок на регистрацию",
        "time": "3 часа назад",
        "details": "Требуется модерация новых заявок в разделе 'Партнеры' -> 'На модерации'."
    },
    {
        "id": 5,
        "type": "error",
        "message": "Сервис email-рассылки недоступен",
        "time": "5 часов назад",
        "details": "Не удается подключиться к серверу SMTP. Проверьте настройки и доступность сервиса."
    }
]

MOCK_QUICK_ACTIONS = [
    {
        "id": "add_partner", 
        "title": "Добавить партнёра", 
        "icon": "fas fa-store", 
        "url": "/admin/partners/add"
    },
    {
        "id": "create_campaign", 
        "title": "Создать кампанию", 
        "icon": "fas fa-bullhorn", 
        "url": "/admin/campaigns/new"
    },
    {
        "id": "view_reports", 
        "title": "Отчёты", 
        "icon": "fas fa-chart-bar", 
        "url": "/admin/reports"
    },
    {
        "id": "moderate_content", 
        "title": "Модерация", 
        "icon": "fas fa-shield-alt", 
        "url": "/admin/moderation"
    },
    {
        "id": "manage_users",
        "title": "Управление пользователями",
        "icon": "fas fa-users",
        "url": "/admin/users"
    },
    {
        "id": "system_settings",
        "title": "Настройки системы",
        "icon": "fas fa-cog",
        "url": "/admin/settings"
    },
    {
        "id": "audit_log",
        "title": "Журнал аудита",
        "icon": "fas fa-clipboard-list",
        "url": "/admin/audit-log"
    },
    {
        "id": "help_center",
        "title": "Центр помощи",
        "icon": "fas fa-question-circle",
        "url": "/admin/help"
    }
]

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Отображение главной страницы админ-панели.
    """
    # Получаем данные для дашборда
    dashboard_data = await get_dashboard_data(request, current_user)
    
    # Добавляем информацию о пользователе
    dashboard_data["user"] = {
        "name": current_user.get("name", "Администратор"),
        "email": current_user.get("email", "admin@example.com"),
        "role": current_user.get("role", "admin"),
        "avatar": current_user.get("avatar") or ""
    }
    
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request, "data": dashboard_data}
    )

@router.get("/dashboard/api", response_class=JSONResponse)
async def get_dashboard_data(
    request: Request,
    admin_claims: Dict[str, Any] = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Получение данных для дашборда администратора (API).
    
    Возвращает статистику, алерты и быстрые действия в формате JSON.
    """
    # TODO: Заменить на реальные запросы к БД
    user_role = await get_user_role(admin_claims.get("sub"))
    
    # Фильтруем быстрые действия по роли
    available_actions = MOCK_QUICK_ACTIONS.copy()
    if user_role not in [Role.ADMIN, Role.SUPER_ADMIN]:
        available_actions = [a for a in available_actions if a["id"] != "add_partner"]
    
    return {
        "status": "success",
        "data": {
            "stats": MOCK_STATS,
            "alerts": MOCK_ALERTS,
            "quick_actions": available_actions,
            "last_updated": datetime.utcnow().isoformat()
        }
    }

@router.get("/alerts")
async def get_alerts(
    request: Request,
    limit: int = 10,
    offset: int = 0,
    admin_claims: Dict[str, Any] = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Получение списка алертов.
    
    Args:
        limit: Количество возвращаемых записей
        offset: Смещение для пагинации
        
    Returns:
        Список алертов
    """
    # TODO: Заменить на реальный запрос к БД
    return {
        "items": MOCK_ALERTS[offset:offset+limit],
        "total": len(MOCK_ALERTS),
        "limit": limit,
        "offset": offset
    }

@router.get("/stats")
async def get_statistics(
    request: Request,
    period: str = "day",  # day, week, month, year
    admin_claims: Dict[str, Any] = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Получение статистики за выбранный период.
    
    Args:
        period: Период для статистики (day, week, month, year)
        
    Returns:
        Статистические данные
    """
    # TODO: Заменить на реальные запросы к БД
    now = datetime.utcnow()
    
    # Генерация моковых данных для графика
    if period == "day":
        points = 24
        delta = timedelta(hours=1)
    elif period == "week":
        points = 7
        delta = timedelta(days=1)
    elif period == "month":
        points = 30
        delta = timedelta(days=1)
    else:  # year
        points = 12
        delta = timedelta(days=30)
    
    labels = []
    values = []
    current = now - (delta * points)
    
    for i in range(points):
        current += delta
        labels.append(current.strftime("%Y-%m-%d %H:%M"))
        values.append({
            "users": 100 + (i * 10) + (i % 3 * 5),
            "transactions": 50 + (i * 5) + (i % 2 * 3),
            "revenue": 1000 + (i * 100) + (i % 4 * 50)
        })
    
    return {
        "period": period,
        "labels": labels,
        "datasets": [
            {"label": "Пользователи", "data": [d["users"] for d in values], "borderColor": "#3b82f6"},
            {"label": "Транзакции", "data": [d["transactions"] for d in values], "borderColor": "#10b981"},
            {"label": "Доход", "data": [d["revenue"] for d in values], "borderColor": "#8b5cf6"}
        ]
    }

@router.get("/quick-actions")
async def get_quick_actions(
    request: Request,
    admin_claims: Dict[str, Any] = Depends(require_admin)
):
    """
    Получение списка быстрых действий для текущего пользователя.
    
    Returns:
        Список быстрых действий, доступных пользователю
    """
    user_role = await get_user_role(admin_claims.get("sub"))
    
    # Фильтруем действия по роли
    available_actions = MOCK_QUICK_ACTIONS.copy()
    if user_role not in [Role.ADMIN, Role.SUPER_ADMIN]:
        available_actions = [a for a in available_actions if a["id"] != "add_partner"]
    
    return available_actions

# ===== БОЕВЫЕ ЭНДПОИНТЫ =====

@router.get("/top-places")
async def get_top_places(
    request: Request,
    limit: int = 10,
    period: str = "month",  # day, week, month, year
    admin_claims: Dict[str, Any] = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Получение топа заведений по популярности и активности.
    
    Args:
        limit: Количество заведений в топе
        period: Период для анализа (day, week, month, year)
        
    Returns:
        Список топ заведений с метриками
    """
    try:
        # Определяем период для фильтрации
        now = datetime.utcnow()
        if period == "day":
            since = now - timedelta(days=1)
        elif period == "week":
            since = now - timedelta(weeks=1)
        elif period == "month":
            since = now - timedelta(days=30)
        elif period == "year":
            since = now - timedelta(days=365)
        else:
            since = now - timedelta(days=30)
        
        # Запрос к БД для получения топа заведений
        query = """
            SELECT 
                p.id,
                p.name,
                p.address,
                p.rating,
                p.reviews_count,
                p.is_active,
                p.is_verified,
                COUNT(DISTINCT r.id) as total_reviews,
                COUNT(DISTINCT CASE WHEN r.created_at >= %s THEN r.id END) as recent_reviews,
                AVG(r.rating) as avg_rating,
                COUNT(DISTINCT pc.id) as checkins_count
            FROM places p
            LEFT JOIN reviews r ON p.id = r.place_id
            LEFT JOIN place_checkins pc ON p.id = pc.place_id AND pc.created_at >= %s
            WHERE p.is_active = true
            GROUP BY p.id, p.name, p.address, p.rating, p.reviews_count, p.is_active, p.is_verified
            ORDER BY 
                (COUNT(DISTINCT CASE WHEN r.created_at >= %s THEN r.id END) * 2 + 
                 COUNT(DISTINCT pc.id) + 
                 p.rating * 0.5) DESC
            LIMIT %s
        """
        
        result = await db.fetch_all(
            query, 
            [since, since, since, limit]
        )
        
        top_places = []
        for row in result:
            top_places.append({
                "id": row["id"],
                "name": row["name"],
                "address": row["address"],
                "rating": float(row["avg_rating"]) if row["avg_rating"] else float(row["rating"]),
                "reviews_count": row["total_reviews"],
                "recent_reviews": row["recent_reviews"],
                "checkins_count": row["checkins_count"],
                "is_verified": row["is_verified"],
                "popularity_score": (
                    (row["recent_reviews"] or 0) * 2 + 
                    (row["checkins_count"] or 0) + 
                    (row["rating"] or 0) * 0.5
                )
            })
        
        return {
            "status": "success",
            "data": {
                "top_places": top_places,
                "period": period,
                "total_count": len(top_places),
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting top places: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении топа заведений"
        )

@router.get("/referrals-stats")
async def get_referrals_stats(
    request: Request,
    period: str = "month",  # day, week, month, year
    admin_claims: Dict[str, Any] = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Получение статистики реферальной программы.
    
    Args:
        period: Период для анализа (day, week, month, year)
        
    Returns:
        Статистика рефералов и доходов
    """
    try:
        # Определяем период для фильтрации
        now = datetime.utcnow()
        if period == "day":
            since = now - timedelta(days=1)
        elif period == "week":
            since = now - timedelta(weeks=1)
        elif period == "month":
            since = now - timedelta(days=30)
        elif period == "year":
            since = now - timedelta(days=365)
        else:
            since = now - timedelta(days=30)
        
        # Общая статистика рефералов
        total_referrals_query = """
            SELECT 
                COUNT(*) as total_referrals,
                COUNT(DISTINCT referrer_id) as active_referrers,
                COUNT(CASE WHEN created_at >= %s THEN 1 END) as recent_referrals
            FROM referrals
        """
        
        total_stats = await db.fetch_one(total_referrals_query, [since])
        
        # Топ рефереров
        top_referrers_query = """
            SELECT 
                r.referrer_id,
                u.username,
                u.first_name,
                COUNT(*) as referrals_count,
                SUM(lt.points) as total_earnings
            FROM referrals r
            LEFT JOIN users u ON r.referrer_id = u.id
            LEFT JOIN loyalty_transactions lt ON lt.user_id = r.referrer_id 
                AND lt.transaction_type = 'referral_bonus'
                AND lt.reference_id = r.id
            WHERE r.created_at >= %s
            GROUP BY r.referrer_id, u.username, u.first_name
            ORDER BY referrals_count DESC
            LIMIT 10
        """
        
        top_referrers = await db.fetch_all(top_referrers_query, [since])
        
        # Статистика по дням для графика
        daily_stats_query = """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as referrals_count,
                COUNT(DISTINCT referrer_id) as unique_referrers
            FROM referrals
            WHERE created_at >= %s
            GROUP BY DATE(created_at)
            ORDER BY date
        """
        
        daily_stats = await db.fetch_all(daily_stats_query, [since])
        
        # Общие доходы от рефералов
        total_earnings_query = """
            SELECT 
                COALESCE(SUM(lt.points), 0) as total_earnings,
                COUNT(DISTINCT lt.user_id) as users_with_earnings
            FROM loyalty_transactions lt
            WHERE lt.transaction_type = 'referral_bonus'
                AND lt.created_at >= %s
        """
        
        earnings_stats = await db.fetch_one(total_earnings_query, [since])
        
        return {
            "status": "success",
            "data": {
                "period": period,
                "total_referrals": total_stats["total_referrals"],
                "active_referrers": total_stats["active_referrers"],
                "recent_referrals": total_stats["recent_referrals"],
                "total_earnings": earnings_stats["total_earnings"],
                "users_with_earnings": earnings_stats["users_with_earnings"],
                "top_referrers": [
                    {
                        "user_id": row["referrer_id"],
                        "username": row["username"],
                        "first_name": row["first_name"],
                        "referrals_count": row["referrals_count"],
                        "total_earnings": row["total_earnings"] or 0
                    }
                    for row in top_referrers
                ],
                "daily_stats": [
                    {
                        "date": row["date"].isoformat(),
                        "referrals_count": row["referrals_count"],
                        "unique_referrers": row["unique_referrers"]
                    }
                    for row in daily_stats
                ],
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting referrals stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении статистики рефералов"
        )

@router.get("/user-activity")
async def get_user_activity(
    request: Request,
    period: str = "week",  # day, week, month, year
    limit: int = 50,
    admin_claims: Dict[str, Any] = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Получение активности пользователей за период.
    
    Args:
        period: Период для анализа (day, week, month, year)
        limit: Количество записей для возврата
        
    Returns:
        Статистика активности пользователей
    """
    try:
        # Определяем период для фильтрации
        now = datetime.utcnow()
        if period == "day":
            since = now - timedelta(days=1)
        elif period == "week":
            since = now - timedelta(weeks=1)
        elif period == "month":
            since = now - timedelta(days=30)
        elif period == "year":
            since = now - timedelta(days=365)
        else:
            since = now - timedelta(weeks=1)
        
        # Общая статистика активности
        activity_stats_query = """
            SELECT 
                COUNT(DISTINCT user_id) as active_users,
                COUNT(*) as total_activities,
                COUNT(DISTINCT DATE(created_at)) as active_days
            FROM user_activity_logs
            WHERE created_at >= %s
        """
        
        activity_stats = await db.fetch_one(activity_stats_query, [since])
        
        # Топ активных пользователей
        top_users_query = """
            SELECT 
                ual.user_id,
                u.username,
                u.first_name,
                u.last_name,
                COUNT(*) as activities_count,
                MAX(ual.created_at) as last_activity,
                SUM(ual.points_awarded) as total_points
            FROM user_activity_logs ual
            LEFT JOIN users u ON ual.user_id = u.id
            WHERE ual.created_at >= %s
            GROUP BY ual.user_id, u.username, u.first_name, u.last_name
            ORDER BY activities_count DESC
            LIMIT %s
        """
        
        top_users = await db.fetch_all(top_users_query, [since, limit])
        
        # Статистика по типам активности
        activity_types_query = """
            SELECT 
                activity_type,
                COUNT(*) as count,
                COUNT(DISTINCT user_id) as unique_users,
                AVG(points_awarded) as avg_points
            FROM user_activity_logs
            WHERE created_at >= %s
            GROUP BY activity_type
            ORDER BY count DESC
        """
        
        activity_types = await db.fetch_all(activity_types_query, [since])
        
        # Активность по дням
        daily_activity_query = """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as activities_count,
                COUNT(DISTINCT user_id) as unique_users
            FROM user_activity_logs
            WHERE created_at >= %s
            GROUP BY DATE(created_at)
            ORDER BY date
        """
        
        daily_activity = await db.fetch_all(daily_activity_query, [since])
        
        return {
            "status": "success",
            "data": {
                "period": period,
                "active_users": activity_stats["active_users"],
                "total_activities": activity_stats["total_activities"],
                "active_days": activity_stats["active_days"],
                "top_users": [
                    {
                        "user_id": row["user_id"],
                        "username": row["username"],
                        "first_name": row["first_name"],
                        "last_name": row["last_name"],
                        "activities_count": row["activities_count"],
                        "last_activity": row["last_activity"].isoformat() if row["last_activity"] else None,
                        "total_points": row["total_points"] or 0
                    }
                    for row in top_users
                ],
                "activity_types": [
                    {
                        "type": row["activity_type"],
                        "count": row["count"],
                        "unique_users": row["unique_users"],
                        "avg_points": float(row["avg_points"]) if row["avg_points"] else 0
                    }
                    for row in activity_types
                ],
                "daily_activity": [
                    {
                        "date": row["date"].isoformat(),
                        "activities_count": row["activities_count"],
                        "unique_users": row["unique_users"]
                    }
                    for row in daily_activity
                ],
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении статистики активности пользователей"
        )
