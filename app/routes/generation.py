from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.video import VideoJob
from app.routes.deps import get_current_user
from app.services.ai_engine import ContentEngine
from app.services.generation_rules import ALLOWED_MEDIA_EXTENSIONS
from app.services.generation_rules import MAX_UPLOAD_SIZE_BYTES
from app.services.generation_rules import get_allowed_media_extensions_label
from app.services.job_service import get_recent_jobs
from app.services.video_gen import get_active_video_provider
from app.services.video_gen import VideoGenerator
from app.web import build_video_render_state
from app.web import render_dashboard, templates


router = APIRouter(prefix="/generation", tags=["generation"])


def _dashboard_error(
    request: Request,
    user: User,
    jobs: list[VideoJob],
    message: str,
):
    return render_dashboard(
        request=request,
        user=user,
        jobs=jobs,
        error=message,
        status_code=400,
    )


@router.post("/create")
async def create_generation(
    request: Request,
    source_type: str = Form(...),
    source_content: str = Form(""),
    source_file: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    jobs = get_recent_jobs(db=db, user_id=current_user.id)

    if current_user.credits < 1:
        return _dashboard_error(
            request=request,
            user=current_user,
            jobs=jobs,
            message="Créditos insuficientes para gerar novos vídeos.",
        )

    clean_content = source_content.strip()
    if source_type in ["text", "link"] and not clean_content:
        return _dashboard_error(
            request=request,
            user=current_user,
            jobs=jobs,
            message="Informe um conteúdo base para texto ou link.",
        )

    if source_type == "video" and not source_file:
        return _dashboard_error(
            request=request,
            user=current_user,
            jobs=jobs,
            message="Envie um arquivo de vídeo/áudio para transcrição.",
        )

    if source_type == "video" and source_file:
        file_name = (source_file.filename or "").strip()
        extension = ""
        if "." in file_name:
            extension = f".{file_name.rsplit('.', 1)[1].lower()}"

        if extension not in ALLOWED_MEDIA_EXTENSIONS:
            return _dashboard_error(
                request=request,
                user=current_user,
                jobs=jobs,
                message=(
                    "Formato não permitido. Use "
                    f"{get_allowed_media_extensions_label()}."
                ),
            )

    content_engine = ContentEngine()
    video_generator = VideoGenerator()

    uploaded_bytes = await source_file.read() if source_file else None
    uploaded_name = source_file.filename if source_file else None

    if source_type == "video" and uploaded_bytes:
        if len(uploaded_bytes) > MAX_UPLOAD_SIZE_BYTES:
            return _dashboard_error(
                request=request,
                user=current_user,
                jobs=jobs,
                message=(
                    "Arquivo excede "
                    f"{MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB. "
                    "Reduza o tamanho e tente novamente."
                ),
            )

    persisted_source = clean_content
    if source_type == "video":
        persisted_source = uploaded_name or "upload_video"

    package = await content_engine.build_story_package(
        source_type=source_type,
        source_content=clean_content,
        video_bytes=uploaded_bytes,
        video_filename=uploaded_name,
    )
    scripts = package["scripts"][:3]

    created_jobs = []
    for index, script in enumerate(scripts, start=1):
        render = await video_generator.render_script(
            script=script,
            title=f"Vídeo {index}",
        )

        job = VideoJob(
            user_id=current_user.id,
            source_type=source_type,
            source_content=persisted_source,
            script_variant=index,
            status=render.get("status", "queued"),
            provider=render.get("provider", "shotstack"),
            requested_provider=(
                render.get("requested_provider")
                or get_active_video_provider()
            ),
            render_id=render.get("render_id") or None,
            output_url=render.get("output_url") or "",
            status_message=render.get("message") or "",
        )
        db.add(job)
        created_jobs.append(
            {
                "script_variant": index,
                "script": script,
                "status": job.status,
                "provider": job.provider,
                "requested_provider": job.requested_provider,
                "output_url": job.output_url,
                "preview_image_url": render.get("preview_image_url", ""),
                "message": render.get("message", ""),
            }
        )

    current_user.credits -= 1
    db.commit()

    render_state = build_video_render_state(items=created_jobs)

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "request": request,
            "user": current_user,
            "created_jobs": created_jobs,
            **render_state,
            "veo_auto_fallback_notice": render_state[
                "veo_shotstack_fallback_notice"
            ],
            "veo_quota_notice": render_state["veo_quota_warning"],
        },
    )


@router.get("/new")
def new_generation(_: User = Depends(get_current_user)):
    return RedirectResponse(url="/dashboard", status_code=302)
