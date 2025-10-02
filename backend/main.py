from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import time
import logging
import os

from config import settings
from database import engine, Base
from routers import loyalty, certificates, referrals, auth, admin, integrations, bitrix_sso

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Запуск приложения Моя ❤ скидка")
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    logger.info("Остановка приложения")


app = FastAPI(
    title="Моя ❤ скидка API",
    description="Микросервис лояльности, сертификатов и рефералов для медицинского центра",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"https://{settings.DOMAIN}",
        f"http://{settings.DOMAIN}",
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware для логирования и измерения времени запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Логируем входящий запрос
    logger.info(f"Запрос: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    # Логируем время обработки
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"Завершено за {process_time:.3f}s - Статус: {response.status_code}")
    
    return response


# Health check
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Моя ❤ скидка",
        "version": "1.0.0"
    }


# Подключение роутеров
app.include_router(auth.router, prefix="/api/auth", tags=["Авторизация"])
app.include_router(bitrix_sso.router, prefix="/auth/bitrix", tags=["Bitrix SSO"])
app.include_router(loyalty.router, prefix="/api/loyalty", tags=["Лояльность"])
app.include_router(certificates.router, prefix="/api/certificates", tags=["Сертификаты"])
app.include_router(referrals.router, prefix="/api/referrals", tags=["Рефералы"])
app.include_router(admin.router, prefix="/api/admin", tags=["Администрирование"])
app.include_router(integrations.router, prefix="/api/integrations", tags=["Интеграции"])

# Статические файлы (QR-коды и uploads)
qrcode_dir = "/app/qrcodes"
uploads_dir = "/app/uploads"
os.makedirs(qrcode_dir, exist_ok=True)
os.makedirs(uploads_dir, exist_ok=True)

app.mount("/qrcodes", StaticFiles(directory=qrcode_dir), name="qrcodes")
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


# Обработчик ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Необработанная ошибка: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Внутренняя ошибка сервера",
            "error": str(exc) if settings.DEBUG else "Internal Server Error"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
