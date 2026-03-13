import traceback

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.logging import logger
from app.core.exceptions.base import AppException


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Uygulama exception'larını yakalar ve uygun HTTP yanıtı döner."""
    logger.warning(
        "AppException | %s %s | %d: %s",
        request.method,
        request.url.path,
        exc.status_code,
        exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Beklenmeyen exception'ları yakalar ve 500 hatası döner."""
    logger.error(
        "Beklenmeyen hata | %s %s | %s\n%s",
        request.method,
        request.url.path,
        str(exc),
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Sunucu hatası oluştu. Lütfen daha sonra tekrar deneyin."},
    )
