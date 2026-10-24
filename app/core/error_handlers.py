import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError

logger = logging.getLogger(__name__)


def _error_body(code: str, message: str, **extra) -> dict:
    return {"error": {"code": code, "message": message, **extra}}


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        if exc.status_code >= 500:
            logger.exception("Server error on %s", request.url.path)
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.code, exc.message, **exc.extra),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=_error_body(
                "validation_error",
                "Invalid request",
                details=jsonable_encoder(exc.errors()),
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content=_error_body("internal_error", "Internal server error"),
        )