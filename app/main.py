from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.core.security import hash_password
from app.models import User
from app.routes import auth, dashboard, generation


app = FastAPI(title="Agentes IA Studio", version="0.1.0")
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.state.admin_email = "admin@agentesia.com"

BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(generation.router)


@app.on_event("startup")
def on_startup() -> None:
    from app.core.database import SessionLocal

    Base.metadata.create_all(bind=engine)

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

    db = SessionLocal()
    try:
        admin_email = app.state.admin_email
        existing_admin = (
            db.query(User)
            .filter(User.email == admin_email)
            .first()
        )
        if not existing_admin:
            db.add(
                User(
                    email=admin_email,
                    hashed_password=hash_password("admin123"),
                    is_admin=True,
                    credits=999,
                )
            )
            db.commit()
    finally:
        db.close()
