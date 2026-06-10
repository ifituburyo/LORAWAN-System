"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1 import account, admin, auth, billing, devices
from app.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown hooks."""
    logger.info("Starting %s (environment=%s)", settings.app_name, settings.environment)
    yield
    logger.info("Shutting down")


# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Customer portal API for Norani LoRaWAN network",
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    openapi_url="/api/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


# Global exception handler for validation errors — return cleaner messages
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = " → ".join(str(x) for x in err.get("loc", []) if x != "body")
        errors.append({
            "field": loc,
            "message": err.get("msg", ""),
            "type": err.get("type", ""),
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation failed", "errors": errors},
    )


# ============ Routers ============

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(devices.router, prefix="/api/v1/devices", tags=["devices"])
app.include_router(account.router, prefix="/api/v1/account", tags=["account"])
app.include_router(billing.router, prefix="/api/v1/billing", tags=["billing"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])


# ============ Health & root ============

@app.get("/api/v1/health", tags=["health"])
async def health_check() -> dict:
    """Liveness probe."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": app.version,
        "environment": settings.environment,
    }


@app.get("/", include_in_schema=False)
async def root() -> dict:
    """Root endpoint — direct users to the API docs."""
    return {
        "message": "Norani Portal API",
        "docs": "/api/docs" if settings.debug else "Contact admin for API documentation",
    }
