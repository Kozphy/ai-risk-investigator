from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import engine
from app.core.logging import configure_logging, get_logger
from app.core.telemetry import setup_telemetry

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])


@asynccontextmanager
async def lifespan(_: FastAPI):
    for path in (settings.upload_dir, settings.knowledge_dir, settings.report_dir):
        Path(path).mkdir(parents=True, exist_ok=True)
    # Ensure pgvector extension when connected to Postgres (skip in unit-test runs)
    if settings.app_env != "test":
        try:
            async with engine.begin() as conn:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        except Exception as exc:
            logger.warning("pgvector_extension_skipped", error=str(exc))
    logger.info("app_started", env=settings.app_env)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Production AI Risk Investigator SaaS API",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
setup_telemetry(app)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
@limiter.limit("120/minute")
async def health(request: Request) -> dict:
    return {"status": "ok", "service": settings.app_name, "env": settings.app_env}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_error", path=str(request.url.path), error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
