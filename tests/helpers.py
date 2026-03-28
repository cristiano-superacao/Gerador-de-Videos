from app.models.user import User


def login(client, email: str, password: str):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def register(client, email: str, password: str):
    return client.post(
        "/register",
        data={"email": email, "password": password},
        follow_redirects=False,
    )


def get_user(db_session, email: str) -> User | None:
    return db_session.query(User).filter_by(email=email).first()
