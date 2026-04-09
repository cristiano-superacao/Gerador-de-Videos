from sqlalchemy.orm import Session

from app.models.video import VideoJob


DEMO_OUTPUT_URL_FRAGMENT = "example.com/video-preview.mp4"
SUSPENDED_DEMO_OUTPUT_FRAGMENTS = {
    "8a85ba4a-58dc-4981-91ca-5289d9ae6d5e.mp4",
    "e8077f59-f17a-4e37-b703-6c8a16d7f49e.mp4",
    "3b36b6b5-3d3e-4c5e-8e0e-9c8f6a0b5d3e.mp4",
}


def get_recent_jobs(
    db: Session,
    user_id: int,
    limit: int = 20,
) -> list[VideoJob]:
    jobs = (
        db.query(VideoJob)
        .filter(VideoJob.user_id == user_id)
        .order_by(VideoJob.created_at.desc())
        .limit(limit)
        .all()
    )
    for job in jobs:
        job.output_url = normalize_output_url(job.output_url)
    return jobs


def normalize_output_url(url: str | None) -> str:
    if not url:
        return ""
    if DEMO_OUTPUT_URL_FRAGMENT in url:
        return ""
    if any(fragment in url for fragment in SUSPENDED_DEMO_OUTPUT_FRAGMENTS):
        return ""
    return url


def has_output_media(url: str | None) -> bool:
    return bool(normalize_output_url(url))


def serialize_job(job: VideoJob) -> dict:
    return {
        "id": job.id,
        "script_variant": job.script_variant,
        "status": job.status,
        "provider": job.provider,
        "requested_provider": job.requested_provider or job.provider,
        "output_url": normalize_output_url(job.output_url),
        "status_message": job.status_message or "",
        "created_at": job.created_at.strftime("%d/%m/%Y %H:%M"),
    }
