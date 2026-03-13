from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import engine, Base
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
    RequestLoggingMiddleware,
)
from app.core.logging import logger
from app.api.v1.router import api_router


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Uygulama başlatılıyor — %s v%s", settings.APP_NAME, settings.APP_VERSION)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Veritabanı tabloları kontrol edildi / oluşturuldu")

    yield

    await engine.dispose()
    logger.info("Uygulama kapatılıyor")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Yapay zeka destekli yemek tarifi chatbot API'si. "
                "Tarifler arasında akıllı arama yapın ve yemek önerileri alın.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.include_router(api_router)


@app.get("/", tags=["Sağlık Kontrolü"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "çalışıyor",
    }


@app.get("/health", tags=["Sağlık Kontrolü"])
async def health_check():
    return {"status": "sağlıklı"}
