from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.routes.deps import get_admin_user, get_current_user
from app.services.job_service import get_recent_jobs, serialize_job
from app.services.video_gen import is_video_render_configured
from app.services.video_gen import VideoGenerator
from app.web import render_dashboard, render_jobs_rows, templates


router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    jobs = get_recent_jobs(db=db, user_id=current_user.id)
    return render_dashboard(
        request=request,
        user=current_user,
        jobs=jobs,
    )


@router.get("/como-usar")
def how_to_use(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="how_to_use.html",
        context={"request": request},
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
        if not job.render_id:
            continue
        if job.status not in pending_statuses:
            continue

        try:
            status_payload = await generator.get_render_status(
                job.render_id,
                provider=job.provider,
            )
        except TypeError:
            status_payload = await generator.get_render_status(job.render_id)
        new_status = status_payload.get("status") or job.status
        new_output_url = status_payload.get("output_url")
        new_status_message = status_payload.get("message")

        # Mantém o valor persistido quando o provider não retorna link novo.
        if new_output_url is None:
            new_output_url = job.output_url
        if new_status_message is None:
            new_status_message = job.status_message

        if (
            new_status != job.status
            or new_output_url != (job.output_url or "")
            or new_status_message != (job.status_message or "")
        ):
            job.status = new_status
            job.output_url = new_output_url
            job.status_message = new_status_message
            updated = True

    if updated:
        db.commit()

    return JSONResponse(
        {
            "jobs": [serialize_job(job) for job in jobs],
            "html": render_jobs_rows(jobs),
            "has_demo_mode": (
                (not is_video_render_configured())
                or any(job.status == "simulado" for job in jobs)
            ),
        }
    )


@router.get("/admin/users")
def admin_users(
    request: Request,
    _: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    users = db.query(User).order_by(User.id.desc()).all()
    return templates.TemplateResponse(
        request=request,
        name="admin_users.html",
        context={"request": request, "users": users},
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
