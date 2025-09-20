"""
FastAPI роуты для WebApp интеграции
"""
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
import os
import time
import hashlib
import hmac
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="web/templates")

# Импорт сервиса интеграции
try:
    from core.services.webapp_integration import webapp_integration
except ImportError:
    logger.warning("WebApp integration service not available")
    webapp_integration = None


@router.get("/webapp", response_class=HTMLResponse)
async def webapp_page(
    request: Request, 
    user_id: Optional[int] = Query(None), 
    username: Optional[str] = Query(None),
    first_name: Optional[str] = Query(None),
    odoo_available: Optional[bool] = Query(False),
    # Старые параметры для обратной совместимости
    tg_user_id: Optional[str] = Query(None),
    tg_role: Optional[str] = Query(None),
    tg_timestamp: Optional[str] = Query(None),
    tg_signature: Optional[str] = Query(None)
):
    """WebApp с динамической поддержкой Odoo"""
    
    # Определить источник данных
    if user_id:
        # Новые параметры из команды /webapp
        telegram_id = str(user_id)
        role = 'user'  # По умолчанию
        name = first_name or username or f"User {user_id}"
    elif tg_user_id:
        # Старые параметры для обратной совместимости
        telegram_id = tg_user_id
        role = tg_role or 'user'
        name = f"Пользователь {tg_user_id}"
    else:
        return templates.TemplateResponse("webapp.html", {
            "request": request,
            "error": "Отсутствуют параметры авторизации"
        })
    
    user_data = {
        'id': user_id or int(tg_user_id) if tg_user_id else 0,
        'username': username or 'Unknown',
        'first_name': first_name or 'User',
        'role': role,
        'points': 150  # Заглушка
    }
    
    # Если Odoo доступен, попробовать получить реальные данные
    if odoo_available:
        try:
            from core.services.odoo_api import OdooAPI
            odoo = OdooAPI()
            if odoo.connect():
                # Получить данные пользователя из Odoo
                odoo_user = odoo.get_user_by_telegram(telegram_id)
                if odoo_user:
                    user_data.update(odoo_user)
        except Exception as e:
            print(f"Ошибка получения данных из Odoo: {e}")
            odoo_available = False
    
    return templates.TemplateResponse("webapp.html", {
        "request": request,
        "user": user_data,
        "odoo_available": odoo_available,
        "odoo_url": "https://odoo-crm-production.up.railway.app"
    })


@router.get("/webapp/partner")
async def partner_webapp(
    request: Request,
    tg_user_id: Optional[str] = Query(None),
    tg_role: Optional[str] = Query(None),
    tg_timestamp: Optional[str] = Query(None),
    tg_signature: Optional[str] = Query(None),
    partner_id: Optional[str] = Query(None)
):
    """Партнерский WebApp"""
    try:
        # Валидировать параметры
        params = {
            'tg_user_id': tg_user_id,
            'tg_role': tg_role,
            'tg_timestamp': int(tg_timestamp) if tg_timestamp else 0,
            'tg_signature': tg_signature
        }
        
        if not webapp_integration or not webapp_integration.validate_webapp_params(params):
            raise HTTPException(status_code=401, detail="Invalid authentication")
        
        # Проверить роль
        if tg_role != 'partner':
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Создать URL для Odoo партнерского кабинета
        odoo_url = webapp_integration.create_partner_webapp_url(
            telegram_id=int(tg_user_id),
            partner_id=int(partner_id) if partner_id else None
        )
        
        # Перенаправить в Odoo
        return RedirectResponse(url=odoo_url)
        
    except Exception as e:
        logger.error(f"Error in partner_webapp: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/webapp/admin")
async def admin_webapp(
    request: Request,
    tg_user_id: Optional[str] = Query(None),
    tg_role: Optional[str] = Query(None),
    tg_timestamp: Optional[str] = Query(None),
    tg_signature: Optional[str] = Query(None),
    admin_level: Optional[str] = Query('admin')
):
    """Админский WebApp"""
    try:
        # Валидировать параметры
        params = {
            'tg_user_id': tg_user_id,
            'tg_role': tg_role,
            'tg_timestamp': int(tg_timestamp) if tg_timestamp else 0,
            'tg_signature': tg_signature
        }
        
        if not webapp_integration or not webapp_integration.validate_webapp_params(params):
            raise HTTPException(status_code=401, detail="Invalid authentication")
        
        # Проверить роль
        if tg_role not in ['admin', 'super_admin']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Создать URL для Odoo админского кабинета
        odoo_url = webapp_integration.create_admin_webapp_url(
            telegram_id=int(tg_user_id),
            admin_level=tg_role
        )
        
        # Перенаправить в Odoo
        return RedirectResponse(url=odoo_url)
        
    except Exception as e:
        logger.error(f"Error in admin_webapp: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/webapp/user")
async def user_webapp(
    request: Request,
    tg_user_id: Optional[str] = Query(None),
    tg_role: Optional[str] = Query(None),
    tg_timestamp: Optional[str] = Query(None),
    tg_signature: Optional[str] = Query(None)
):
    """Пользовательский WebApp"""
    try:
        # Валидировать параметры
        params = {
            'tg_user_id': tg_user_id,
            'tg_role': tg_role,
            'tg_timestamp': int(tg_timestamp) if tg_timestamp else 0,
            'tg_signature': tg_signature
        }
        
        if not webapp_integration or not webapp_integration.validate_webapp_params(params):
            raise HTTPException(status_code=401, detail="Invalid authentication")
        
        # Создать URL для Odoo пользовательского кабинета
        odoo_url = webapp_integration.create_user_webapp_url(
            telegram_id=int(tg_user_id)
        )
        
        # Перенаправить в Odoo
        return RedirectResponse(url=odoo_url)
        
    except Exception as e:
        logger.error(f"Error in user_webapp: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api/webapp/validate")
async def validate_webapp_token(
    tg_user_id: str = Query(...),
    tg_role: str = Query(...),
    tg_timestamp: str = Query(...),
    tg_signature: str = Query(...)
):
    """API для валидации WebApp токена"""
    try:
        params = {
            'tg_user_id': tg_user_id,
            'tg_role': tg_role,
            'tg_timestamp': int(tg_timestamp),
            'tg_signature': tg_signature
        }
        
        if not webapp_integration:
            return {"valid": False, "error": "WebApp integration not available"}
        
        is_valid = webapp_integration.validate_webapp_params(params)
        
        return {
            "valid": is_valid,
            "user_id": tg_user_id,
            "role": tg_role,
            "timestamp": tg_timestamp
        }
        
    except Exception as e:
        logger.error(f"Error validating token: {e}")
        return {"valid": False, "error": str(e)}


@router.get("/api/webapp/cabinet-url")
async def get_cabinet_url(
    tg_user_id: str = Query(...),
    tg_role: str = Query(...),
    tg_timestamp: str = Query(...),
    tg_signature: str = Query(...)
):
    """API для получения URL кабинета"""
    try:
        params = {
            'tg_user_id': tg_user_id,
            'tg_role': tg_role,
            'tg_timestamp': int(tg_timestamp),
            'tg_signature': tg_signature
        }
        
        if not webapp_integration:
            raise HTTPException(status_code=500, detail="WebApp integration not available")
        
        if not webapp_integration.validate_webapp_params(params):
            raise HTTPException(status_code=401, detail="Invalid authentication")
        
        # Создать URL кабинета в зависимости от роли
        telegram_id = int(tg_user_id)
        role = tg_role
        
        if role == 'partner':
            cabinet_url = webapp_integration.create_partner_webapp_url(telegram_id)
        elif role in ['admin', 'super_admin']:
            cabinet_url = webapp_integration.create_admin_webapp_url(telegram_id, role)
        else:
            cabinet_url = webapp_integration.create_user_webapp_url(telegram_id)
        
        return {
            "cabinet_url": cabinet_url,
            "role": role,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error getting cabinet URL: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/webapp/cabinet-url")
async def get_cabinet_url_post(request: Request):
    """API для получения URL кабинета (POST)"""
    try:
        data = await request.json()
        telegram_id = data.get('telegram_id')
        role = data.get('role')
        
        if not telegram_id or not role:
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        # Создать URL кабинета в зависимости от роли
        if role == 'partner':
            cabinet_url = webapp_integration.create_partner_webapp_url(telegram_id)
        elif role in ['admin', 'super_admin']:
            cabinet_url = webapp_integration.create_admin_webapp_url(telegram_id, role)
        else:
            cabinet_url = webapp_integration.create_user_webapp_url(telegram_id)
        
        return {
            "cabinet_url": cabinet_url,
            "role": role,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error getting cabinet URL: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/webapp/odoo-menu-url")
async def get_odoo_menu_url(request: Request):
    """API для получения URL конкретного меню Odoo"""
    try:
        data = await request.json()
        telegram_id = data.get('telegram_id')
        role = data.get('role')
        menu_id = data.get('menu_id')
        
        if not all([telegram_id, role, menu_id]):
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        # Создать URL меню Odoo
        from core.services.webapp_integration import create_odoo_menu_url
        menu_url = create_odoo_menu_url(telegram_id, role, menu_id)
        
        return {
            "menu_url": menu_url,
            "menu_id": menu_id,
            "role": role,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error getting Odoo menu URL: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/webapp/odoo-record-url")
async def get_odoo_record_url(request: Request):
    """API для получения URL конкретной записи Odoo"""
    try:
        data = await request.json()
        telegram_id = data.get('telegram_id')
        role = data.get('role')
        model = data.get('model')
        record_id = data.get('record_id')
        view_type = data.get('view_type', 'form')
        
        if not all([telegram_id, role, model, record_id]):
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        # Создать URL записи Odoo
        from core.services.webapp_integration import create_odoo_record_url
        record_url = create_odoo_record_url(telegram_id, role, model, record_id, view_type)
        
        return {
            "record_url": record_url,
            "model": model,
            "record_id": record_id,
            "view_type": view_type,
            "role": role,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error getting Odoo record URL: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check():
    """Проверка здоровья WebApp"""
    return {
        "status": "healthy",
        "webapp_integration": webapp_integration is not None,
        "timestamp": int(time.time())
    }
