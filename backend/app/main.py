import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings, validate_settings
from app.database import SessionLocal, check_connection, run_migrations
from app.exception_handlers import register_exception_handlers
from app.middleware.activity_log import ActivityLogMiddleware
from app.routes import health_router, logs_router, orders_router
from app.services import activity_log_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_settings()
    check_connection()
    run_migrations()
    db = SessionLocal()
    try:
        deleted = activity_log_service.prune_activity_logs(
            db,
            max_entries=settings.activity_log_max_entries,
        )
        if deleted:
            logger.info("Pruned %d activity log entries", deleted)
    except Exception:
        logger.exception("Failed to prune activity logs on startup")
    finally:
        db.close()
    logger.info("Application startup complete")
    yield


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ActivityLogMiddleware)

app.include_router(health_router)
app.include_router(orders_router)
app.include_router(logs_router)
