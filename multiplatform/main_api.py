# АВТОНОМНЫЙ ФАЙЛ - НЕ ИМПОРТИРУЕТ ИЗ CORE/

from fastapi import FastAPI
from api.platform_endpoints import main_router

app = FastAPI(title="Multi-Platform System")

app.include_router(main_router, prefix="/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("multiplatform.main_api:app", host="0.0.0.0", port=8001, reload=True)
