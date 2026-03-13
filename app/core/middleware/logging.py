import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """HTTP isteklerini loglar ve süresini ölçer."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        logger.info(">>> %s %s", request.method, request.url.path)

        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(
                "<<< %s %s | HATA: %s",
                request.method,
                request.url.path,
                str(e),
            )
            raise

        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "<<< %s %s | %d | %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        return response
