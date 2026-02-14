from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.video import VideoJob
from app.routes.deps import get_admin_user, get_current_user
from app.services.job_service import get_recent_jobs
from app.services.video_gen import VideoGenerator


router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")


def _serialize_job(job: VideoJob) -> dict:
    return {
        "id": job.id,
        "script_variant": job.script_variant,
        "status": job.status,
        "provider": job.provider,
        "output_url": job.output_url or "",
        "created_at": job.created_at.strftime("%d/%m/%Y %H:%M"),
    }


@router.get("/dashboard")
def dashboard(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    jobs = get_recent_jobs(db=db, user_id=current_user.id)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": current_user, "jobs": jobs},
    )


@router.get("/como-usar")
def how_to_use(request: Request):
    return templates.TemplateResponse(
        "how_to_use.html",
        {"request": request},
    )


@router.get("/dashboard/jobs/live")
async def dashboard_jobs_live(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    jobs = get_recent_jobs(db=db, user_id=current_user.id)

    generator = VideoGenerator()
    pending_statuses = {"queued", "fetching", "rendering"}
    updated = False

    for job in jobs:
        if job.provider != "shotstack":
            continue
        if not job.render_id:
            continue
        if job.status not in pending_statuses:
            continue

        status_payload = await generator.get_render_status(job.render_id)
        new_status = status_payload.get("status") or job.status
        new_output_url = status_payload.get("output_url") or job.output_url

        if (
            new_status != job.status
            or new_output_url != (job.output_url or "")
        ):
            job.status = new_status
            job.output_url = new_output_url
            updated = True

    if updated:
        db.commit()

    return JSONResponse(
        {"jobs": [_serialize_job(job) for job in jobs]}
    )


@router.get("/admin/users")
def admin_users(
    request: Request,
    _: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.id.desc()).all()
    return templates.TemplateResponse(
        "admin_users.html",
        {"request": request, "users": users},
    )


@router.post("/admin/users/{user_id}/credits")
def update_credits(
    user_id: int,
    credits: int = Form(...),
    _: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.credits = max(0, credits)
        db.commit()
    return RedirectResponse(url="/admin/users", status_code=302)
