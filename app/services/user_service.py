from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User


def upsert_user(
    db: Session,
    email: str,
    password: str,
    credits: int,
    is_admin: bool,
) -> User:
    normalized_email = email.lower().strip()
    user = db.query(User).filter(User.email == normalized_email).first()

    if user:
        user.hashed_password = hash_password(password)
        user.credits = credits
        user.is_admin = is_admin
        return user

    user = User(
        email=normalized_email,
        hashed_password=hash_password(password),
        credits=credits,
        is_admin=is_admin,
    )
    db.add(user)
    return user


def ensure_admin_user(db: Session, admin_email: str, password: str) -> User:
    return upsert_user(
        db=db,
        email=admin_email,
        password=password,
        credits=999,
        is_admin=True,
    )
