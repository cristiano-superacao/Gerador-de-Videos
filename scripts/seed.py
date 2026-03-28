import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.video import VideoJob  # noqa: E402
from app.services.user_service import upsert_user  # noqa: E402


SEED_MARKER = "[seed-demo]"


def ensure_user(
    email: str,
    password: str,
    credits: int,
    is_admin: bool,
) -> User:
    db = SessionLocal()
    try:
        existing_user = (
            db.query(User)
            .filter(User.email == email.lower().strip())
            .first()
        )
        action = "updated" if existing_user else "created"
        user = upsert_user(
            db=db,
            email=email,
            password=password,
            credits=credits,
            is_admin=is_admin,
        )
        db.commit()
        db.refresh(user)
        print(f"user:{user.email}:{action}")
        return user
    finally:
        db.close()


def reset_seed_jobs(user_id: int) -> None:
    db = SessionLocal()
    try:
        (
            db.query(VideoJob)
            .filter(VideoJob.user_id == user_id)
            .filter(VideoJob.source_content.contains(SEED_MARKER))
            .delete(synchronize_session=False)
        )
        db.commit()
    finally:
        db.close()


def create_seed_jobs(user_id: int) -> None:
    demo_jobs = [
        {
            "source_type": "text",
            "source_content": (
                f"{SEED_MARKER} Tendências de IA aplicada a vendas B2B."
            ),
            "script_variant": 1,
            "status": "simulado",
            "provider": "shotstack",
            "render_id": "mock-render-id",
            "output_url": "",
        },
        {
            "source_type": "link",
            "source_content": (
                f"{SEED_MARKER} https://example.com/relatorio-ia-industria"
            ),
            "script_variant": 2,
            "status": "rendering",
            "provider": "shotstack",
            "render_id": "seed-render-rendering",
            "output_url": "",
        },
        {
            "source_type": "video",
            "source_content": f"{SEED_MARKER} upload_seed_audio.mp3",
            "script_variant": 3,
            "status": "simulado",
            "provider": "shotstack",
            "render_id": "mock-render-id",
            "output_url": "",
        },
        {
            "source_type": "text",
            "source_content": (
                f"{SEED_MARKER} Automação com IA para atendimento."
            ),
            "script_variant": 1,
            "status": "queued",
            "provider": "shotstack",
            "render_id": "seed-render-queued",
            "output_url": "",
        },
    ]

    db = SessionLocal()
    try:
        for job_data in demo_jobs:
            db.add(VideoJob(user_id=user_id, **job_data))
        db.commit()
        print(f"jobs:{user_id}:{len(demo_jobs)}")
    finally:
        db.close()


def main() -> None:
    Base.metadata.create_all(bind=engine)

    app_user_email = os.getenv(
        "SEED_APP_USER_EMAIL",
        "cristiano.s.santos@ba.estudante.senai.br",
    )
    app_user_password = os.getenv("SEED_APP_USER_PASSWORD", "18042016")
    reviewer_email = os.getenv(
        "SEED_REVIEWER_EMAIL",
        "cliente.demo@agentesia.com",
    )
    reviewer_password = os.getenv("SEED_REVIEWER_PASSWORD", "teste123")

    admin_user = ensure_user(
        email="admin@agentesia.com",
        password=os.getenv("SEED_ADMIN_PASSWORD", "admin123"),
        credits=999,
        is_admin=True,
    )
    app_user = ensure_user(
        email=app_user_email,
        password=app_user_password,
        credits=50,
        is_admin=False,
    )
    ensure_user(
        email=reviewer_email,
        password=reviewer_password,
        credits=12,
        is_admin=False,
    )

    reset_seed_jobs(admin_user.id)
    reset_seed_jobs(app_user.id)
    create_seed_jobs(admin_user.id)
    create_seed_jobs(app_user.id)

    print("seed:ok")


if __name__ == "__main__":
    main()
