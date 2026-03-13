import time
import traceback

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import logger


class AppException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning(
        "AppException | %s %s | %d: %s",
        request.method, request.url.path, exc.status_code, exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Beklenmeyen hata | %s %s | %s\n%s",
        request.method, request.url.path, str(exc), traceback.format_exc(),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Sunucu hatası oluştu. Lütfen daha sonra tekrar deneyin."},
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        logger.info(">>> %s %s", request.method, request.url.path)

        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(
                "<<< %s %s | HATA: %s",
                request.method, request.url.path, str(e),
            )
            raise

        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "<<< %s %s | %d | %.1fms",
            request.method, request.url.path, response.status_code, duration_ms,
        )

        return response
