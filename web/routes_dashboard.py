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
