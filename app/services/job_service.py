from sqlalchemy.orm import Session

from app.models.video import VideoJob


def get_recent_jobs(
    db: Session,
    user_id: int,
    limit: int = 20,
) -> list[VideoJob]:
    return (
        db.query(VideoJob)
        .filter(VideoJob.user_id == user_id)
        .order_by(VideoJob.created_at.desc())
        .limit(limit)
        .all()
    )
