from contextlib import asynccontextmanager
import logging
from pathlib import Path
from time import sleep

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.models import User
from app.routes import auth, dashboard, generation
from app.services.user_service import ensure_admin_user


logger = logging.getLogger(__name__)


def initialize_application_state(app: FastAPI) -> None:
    from app.core.database import SessionLocal

    initialize_database_schema()

    inspector = inspect(engine)
    if "video_jobs" in inspector.get_table_names():
        columns = {
            col["name"]
            for col in inspector.get_columns("video_jobs")
        }
        if "render_id" not in columns:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE video_jobs "
                        "ADD COLUMN render_id VARCHAR(120)"
                    )
                )
        if "requested_provider" not in columns:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE video_jobs "
                        "ADD COLUMN requested_provider VARCHAR(50)"
                    )
                )
        if "status_message" not in columns:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE video_jobs "
                        "ADD COLUMN status_message TEXT"
                    )
                )

    db = SessionLocal()
    try:
        admin_email = app.state.admin_email
        existing_admin = (
            db.query(User)
            .filter(User.email == admin_email)
            .first()
        )
        if not existing_admin:
            ensure_admin_user(
                db=db,
                admin_email=admin_email,
                password="admin123",
            )
            db.commit()
    finally:
        db.close()


def initialize_database_schema() -> None:
    last_error: OperationalError | None = None

    for attempt in range(1, 6):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except OperationalError as exc:
            last_error = exc
            logger.warning(
                "database startup attempt %s failed; retrying",
                attempt,
            )
            sleep(3)

    if last_error is not None:
        raise last_error


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_application_state(app)
    yield


app = FastAPI(
    title="Agentes IA Studio",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.state.admin_email = "admin@agentesia.com"

BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> RedirectResponse:
    return RedirectResponse(url="/static/favicon.svg", status_code=307)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(generation.router)
