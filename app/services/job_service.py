from sqlalchemy.orm import Session

from app.models.video import VideoJob


DEMO_OUTPUT_URL_FRAGMENT = "example.com/video-preview.mp4"


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


def normalize_output_url(url: str | None) -> str:
    if not url:
        return ""
    if DEMO_OUTPUT_URL_FRAGMENT in url:
        return ""
    return url


def serialize_job(job: VideoJob) -> dict:
    return {
        "id": job.id,
        "script_variant": job.script_variant,
        "status": job.status,
        "provider": job.provider,
        "output_url": normalize_output_url(job.output_url),
        "created_at": job.created_at.strftime("%d/%m/%Y %H:%M"),
    }
