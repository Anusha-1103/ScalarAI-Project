from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(ApplicationError, application_error_handler)  # type: ignore[arg-type]
app.include_router(meeting_router, prefix=settings.api_prefix)


@app.get("/api/v1/health", response_model=ApiResponse[dict[str, str]], tags=["Health"])
async def health() -> ApiResponse[dict[str, str]]:
    return ApiResponse(data={"status": "healthy", "service": "echonote-api"})
