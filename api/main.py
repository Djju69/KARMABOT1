from fastapi import FastAPI, Depends, HTTPException, status, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.security import OAuth2PasswordBearer
from fastapi.routing import APIRouter
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import os
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any

from core.config import settings
from core.database import init_db, get_db, SessionLocal
from core.schemas import ErrorResponse
from core.schemas.auth import UserInDB
from core.services.telegram_bot_service import TelegramBotService

# Импортируем роутеры API
from api.routers import categories, places
from api.routes import auth as auth_routes
from api.routes import telegram as telegram_routes

# Импортируем WebSocket роутер
from api.websockets.telegram import router as websocket_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="KarmaSystem Catalog API",
    description="API for managing catalog of places and categories",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(categories.router, prefix="/api/v1")
app.include_router(places.router, prefix="/api/v1")
app.include_router(auth_routes.router, prefix="/api/v1")
app.include_router(telegram_routes.router, prefix="/api/v1")

# Include WebSocket router
app.include_router(websocket_router)

# Create necessary directories if they don't exist
base_dir = Path("media")
base_dir.mkdir(exist_ok=True)

# Create subdirectories
for subdir in ["places", "avatars", "uploads"]:
    (base_dir / subdir).mkdir(exist_ok=True, parents=True)

# Mount static files
app.mount("/media", StaticFiles(directory="media"), name="media")

# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder({
            "detail": exc.detail,
            "code": getattr(exc, "code", None)
        })
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({
            "detail": "Validation error",
            "errors": exc.errors()
        })
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

# Middleware for request timing and logging
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log request details
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.4f}s"
    )
    
    return response

# Dependency to get current active user
async def get_current_user(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False))
) -> Optional[UserInDB]:
    if not token:
        return None
    
    from jose import JWTError, jwt
    from core.services.auth_service import AuthService
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.auth.secret_key, 
            algorithms=[settings.auth.algorithm]
        )
        
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "access":
            raise credentials_exception
            
        async with SessionLocal() as db:
            auth_repo = AuthRepository(db)
            user = await auth_repo.get_user_by_id(int(user_id))
            if user is None:
                raise credentials_exception
                
            return UserInDB.from_orm(user)
            
    except JWTError:
        raise credentials_exception

# Add current_user to request state
@app.middleware("http")
async def add_current_user(request: Request, call_next):
    auth_header = request.headers.get("Authorization")
    token = None
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    
    if token:
        try:
            user = await get_current_user(token)
            request.state.user = user
        except HTTPException:
            request.state.user = None
    else:
        request.state.user = None
    
    response = await call_next(request)
    return response

# Startup event
@app.on_event("startup")
async def startup_event():
    # Initialize database
    await init_db()
    logger.info("Application startup complete")

# Health check endpoint
@app.get("/api/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    """Корневая страница с информацией о API"""
    return """
    <html>
        <head>
            <title>KarmaSystem API</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    line-height: 1.6; 
                    max-width: 800px; 
                    margin: 0 auto; 
                    padding: 20px;
                }
                .container { 
                    background-color: #f5f5f5; 
                    padding: 20px; 
                    border-radius: 5px; 
                    margin-top: 20px;
                }
                .endpoint { 
                    background: white; 
                    padding: 10px; 
                    margin: 10px 0; 
                    border-left: 4px solid #4CAF50;
                }
                h1 { color: #333; }
                a { color: #4CAF50; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h1>Добро пожаловать в KarmaSystem API</h1>
            <p>Версия: 1.0.0</p>
            
            <div class="container">
                <h2>Доступные эндпоинты:</h2>
                
                <div class="endpoint">
                    <strong>API Документация:</strong>
                    <ul>
                        <li><a href="/api/docs">Swagger UI</a> - Интерактивная документация API</li>
                        <li><a href="/api/redoc">ReDoc</a> - Альтернативная документация</li>
                        <li><a href="/api/openapi.json">OpenAPI Schema</a> - Схема API в формате JSON</li>
                    </ul>
                </div>
                
                <div class="endpoint">
                    <strong>WebSocket:</strong>
                    <ul>
                        <li><code>ws://ваш-домен/ws/telegram/{client_id}</code> - WebSocket для Telegram бота</li>
                    </ul>
                </div>
                
                <div class="endpoint">
                    <strong>Статус системы:</strong>
                    <ul>
                        <li><a href="/api/health">/api/health</a> - Проверка работоспособности API</li>
                    </ul>
                </div>
            </div>
            
            <p>Для получения дополнительной информации обратитесь к <a href="/api/docs">документации API</a>.</p>
        </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
