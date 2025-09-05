#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebApp routes for KARMABOT1
Main web interface routes
"""

from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Any, Optional
import logging

from core.security import get_current_user, get_current_claims
from core.database import get_db
from core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/webapp", tags=["webapp"])
templates = Jinja2Templates(directory="web/templates")


@router.get("/", response_class=HTMLResponse)
async def webapp_home(request: Request):
    """
    Main WebApp home page
    """
    try:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "title": "KARMABOT1 - Система лояльности и скидок"
        })
    except Exception as e:
        logger.error(f"Error rendering home page: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error loading home page"
        )


@router.get("/qr-codes", response_class=HTMLResponse)
async def webapp_qr_codes(request: Request):
    """
    QR codes page
    """
    try:
        return templates.TemplateResponse("qr-codes.html", {
            "request": request,
            "title": "QR-коды - KARMABOT1"
        })
    except Exception as e:
        logger.error(f"Error rendering QR codes page: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error loading QR codes page"
        )


@router.get("/profile", response_class=HTMLResponse)
async def webapp_profile(request: Request):
    """
    User profile page
    """
    try:
        return templates.TemplateResponse("profile.html", {
            "request": request,
            "title": "Профиль - KARMABOT1"
        })
    except Exception as e:
        logger.error(f"Error rendering profile page: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error loading profile page"
        )


@router.get("/referrals", response_class=HTMLResponse)
async def webapp_referrals(request: Request):
    """
    Referrals page
    """
    try:
        return templates.TemplateResponse("referrals.html", {
            "request": request,
            "title": "Рефералы - KARMABOT1"
        })
    except Exception as e:
        logger.error(f"Error rendering referrals page: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error loading referrals page"
        )


@router.get("/catalog", response_class=HTMLResponse)
async def webapp_catalog(request: Request):
    """
    Catalog page
    """
    try:
        return templates.TemplateResponse("catalog.html", {
            "request": request,
            "title": "Каталог - KARMABOT1"
        })
    except Exception as e:
        logger.error(f"Error rendering catalog page: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error loading catalog page"
        )


@router.get("/settings", response_class=HTMLResponse)
async def webapp_settings(request: Request):
    """
    Settings page
    """
    try:
        return templates.TemplateResponse("settings.html", {
            "request": request,
            "title": "Настройки - KARMABOT1"
        })
    except Exception as e:
        logger.error(f"Error rendering settings page: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error loading settings page"
        )


@router.get("/login", response_class=HTMLResponse)
async def webapp_login(request: Request):
    """
    Login page
    """
    try:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "title": "Вход - KARMABOT1"
        })
    except Exception as e:
        logger.error(f"Error rendering login page: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error loading login page"
        )


@router.get("/register", response_class=HTMLResponse)
async def webapp_register(request: Request):
    """
    Registration page
    """
    try:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "title": "Регистрация - KARMABOT1"
        })
    except Exception as e:
        logger.error(f"Error rendering register page: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error loading register page"
        )


@router.get("/logout")
async def webapp_logout():
    """
    Logout and redirect to home
    """
    return RedirectResponse(url="/webapp/", status_code=status.HTTP_302_FOUND)


@router.get("/health")
async def webapp_health():
    """
    WebApp health check
    """
    return {
        "status": "healthy",
        "service": "webapp",
        "version": "1.0.0"
    }
