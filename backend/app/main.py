from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.common.api_schemas import ApiResponse
from app.common.database import create_database_schema, engine
from app.common.exceptions import ApplicationError, application_error_handler
from app.common.settings_config import get_settings
from app.modules.meetings import meeting_models  # noqa: F401
from app.modules.meetings.meeting_controller import router as meeting_router
from app.seed_data import seed_database

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await create_database_schema()
    await seed_database()
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Meeting library, synchronized transcripts, summaries, and action items.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_middleware(GZipMiddleware, minimum_size=1_000, compresslevel=5)
app.add_exception_handler(ApplicationError, application_error_handler)  # type: ignore[arg-type]
app.include_router(meeting_router, prefix=settings.api_prefix)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    if request.url.path in {"/docs", "/redoc"}:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com; frame-ancestors 'none'"
        )
    else:
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    if settings.environment.casefold() == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.get("/api/v1/health", response_model=ApiResponse[dict[str, str]], tags=["Health"])
async def health() -> ApiResponse[dict[str, str]]:
    return ApiResponse(data={"status": "healthy", "service": "echonote-api"})
