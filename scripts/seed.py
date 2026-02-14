import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.user import User


def upsert_user(email: str, password: str, credits: int, is_admin: bool) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.hashed_password = hash_password(password)
            user.credits = credits
            user.is_admin = is_admin
            action = "updated"
        else:
            user = User(
                email=email,
                hashed_password=hash_password(password),
                credits=credits,
                is_admin=is_admin,
            )
            db.add(user)
            action = "created"

        db.commit()
        print(f"user:{email}:{action}")
    finally:
        db.close()


def main() -> None:
    Base.metadata.create_all(bind=engine)

    app_user_email = os.getenv(
        "SEED_APP_USER_EMAIL",
        "cristiano.s.santos@ba.estudante.senai.br",
    )
    app_user_password = os.getenv("SEED_APP_USER_PASSWORD", "18042016")

    upsert_user(
        email="admin@agentesia.com",
        password=os.getenv("SEED_ADMIN_PASSWORD", "admin123"),
        credits=999,
        is_admin=True,
    )
    upsert_user(
        email=app_user_email,
        password=app_user_password,
        credits=50,
        is_admin=False,
    )

    print("seed:ok")


if __name__ == "__main__":
    main()
