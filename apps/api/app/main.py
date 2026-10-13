"""Validate explicit startup settings without creating any database resources."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from app.core.config import Settings, load_settings
from app.core.errors import RequestSafetyMiddleware, http_error_handler, validation_error_handler

from app.system.router import router as system_router

def create_app(settings: Settings | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application: FastAPI):
        application.state.settings = settings if settings is not None else load_settings()
        yield

    application = FastAPI(title="CompanyOS API", version="0.1.0", lifespan=lifespan)
    application.state.session_factory = None
    application.add_middleware(RequestSafetyMiddleware)
    application.add_exception_handler(RequestValidationError, validation_error_handler)
    application.add_exception_handler(HTTPException, http_error_handler)
    application.include_router(system_router, prefix="/api/v1")
    return application


app = create_app()
