from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.models.user import User
from app.models.video import VideoJob
from app.services.generation_rules import get_allowed_media_extensions
from app.services.generation_rules import get_allowed_media_extensions_label
from app.services.generation_rules import MAX_UPLOAD_SIZE_BYTES
from app.services.job_service import serialize_job


templates = Jinja2Templates(directory="app/templates")


def render_jobs_rows(jobs: list[VideoJob]) -> str:
    template = templates.env.get_template("components/jobs_rows.html")
    return template.render(jobs=jobs)


def render_auth_page(
    request: Request,
    heading: str,
    action_url: str,
    submit_label: str,
    error: str | None = None,
    password_minlength: int | None = None,
    helper_text: str | None = None,
    status_code: int = 200,
):
    return templates.TemplateResponse(
        request=request,
        name="auth_form.html",
        context={
            "request": request,
            "heading": heading,
            "action_url": action_url,
            "submit_label": submit_label,
            "error": error,
            "password_minlength": password_minlength,
            "helper_text": helper_text,
        },
        status_code=status_code,
    )


def build_dashboard_context(
    request: Request,
    user: User,
    jobs: list[VideoJob],
    error: str | None = None,
) -> dict:
    context = {
        "request": request,
        "user": user,
        "jobs": jobs,
        "error": error,
        "serialized_jobs": [serialize_job(job) for job in jobs],
        "has_demo_mode": any(job.status == "simulado" for job in jobs),
        "allowed_media_extensions": get_allowed_media_extensions(),
        "allowed_media_extensions_label": get_allowed_media_extensions_label(),
        "max_upload_size_bytes": MAX_UPLOAD_SIZE_BYTES,
        "dashboard_config": {
            "maxUploadBytes": MAX_UPLOAD_SIZE_BYTES,
            "allowedExtensions": get_allowed_media_extensions(),
            "invalidExtensionMessage": (
                "Formato inválido. Use "
                f"{get_allowed_media_extensions_label()}."
            ),
            "uploadTooLargeMessage": (
                "Arquivo excede "
                f"{MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB. "
                "Reduza o tamanho e tente novamente."
            ),
            "missingFileMessage": (
                "Selecione um arquivo de vídeo/áudio para continuar."
            ),
            "submitProcessingLabel": "Processando...",
            "submitDefaultLabel": "Gerar 3 roteiros e vídeos",
            "uploadStatusLabel": "Enviando arquivo...",
            "finalizingStatusLabel": "Finalizando geração...",
            "uploadFailureMessage": (
                "Falha no envio. Tente novamente em instantes."
            ),
            "uploadNetworkErrorMessage": (
                "Erro de rede durante o upload. Tente novamente."
            ),
            "pollUrl": "/dashboard/jobs/live",
            "pollIntervalMs": 8000,
        },
    }
    return context


def render_dashboard(
    request: Request,
    user: User,
    jobs: list[VideoJob],
    error: str | None = None,
    status_code: int = 200,
):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context=build_dashboard_context(
            request=request,
            user=user,
            jobs=jobs,
            error=error,
        ),
        status_code=status_code,
    )
