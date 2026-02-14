from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.video import VideoJob
from app.routes.deps import get_current_user
from app.services.ai_engine import ContentEngine
from app.services.job_service import get_recent_jobs
from app.services.video_gen import VideoGenerator


router = APIRouter(prefix="/generation", tags=["generation"])
templates = Jinja2Templates(directory="app/templates")

ALLOWED_MEDIA_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".mkv",
    ".webm",
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
}
MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024


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
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user": current_user,
                "jobs": jobs,
                "error": "Créditos insuficientes para gerar novos vídeos.",
            },
            status_code=400,
        )

    clean_content = source_content.strip()
    if source_type in ["text", "link"] and not clean_content:
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user": current_user,
                "jobs": jobs,
                "error": "Informe um conteúdo base para texto ou link.",
            },
            status_code=400,
        )

    if source_type == "video" and not source_file:
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user": current_user,
                "jobs": jobs,
                "error": "Envie um arquivo de vídeo/áudio para transcrição.",
            },
            status_code=400,
        )

    if source_type == "video" and source_file:
        file_name = (source_file.filename or "").strip()
        extension = ""
        if "." in file_name:
            extension = f".{file_name.rsplit('.', 1)[1].lower()}"

        if extension not in ALLOWED_MEDIA_EXTENSIONS:
            return templates.TemplateResponse(
                "dashboard.html",
                {
                    "request": request,
                    "user": current_user,
                    "jobs": jobs,
                    "error": (
                        "Formato não permitido. Use mp4, mov, mkv, webm, "
                        "mp3, wav, m4a ou aac."
                    ),
                },
                status_code=400,
            )

    content_engine = ContentEngine()
    video_generator = VideoGenerator()

    uploaded_bytes = await source_file.read() if source_file else None
    uploaded_name = source_file.filename if source_file else None

    if source_type == "video" and uploaded_bytes:
        if len(uploaded_bytes) > MAX_UPLOAD_SIZE_BYTES:
            return templates.TemplateResponse(
                "dashboard.html",
                {
                    "request": request,
                    "user": current_user,
                    "jobs": jobs,
                    "error": (
                        "Arquivo excede 25MB. "
                        "Reduza o tamanho e tente novamente."
                    ),
                },
                status_code=400,
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
            render_id=render.get("render_id") or None,
            output_url=render.get("output_url") or "",
        )
        db.add(job)
        created_jobs.append(
            {
                "script_variant": index,
                "script": script,
                "status": job.status,
                "provider": job.provider,
                "output_url": job.output_url,
                "message": render.get("message", ""),
            }
        )

    current_user.credits -= 1
    db.commit()

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "user": current_user,
            "created_jobs": created_jobs,
        },
    )


@router.get("/new")
def new_generation(_: User = Depends(get_current_user)):
    return RedirectResponse(url="/dashboard", status_code=302)
