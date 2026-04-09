from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.models.user import User
from app.models.video import VideoJob
from app.services.generation_rules import get_allowed_media_extensions
from app.services.generation_rules import get_allowed_media_extensions_label
from app.services.generation_rules import MAX_UPLOAD_SIZE_BYTES
from app.services.job_service import serialize_job
from app.services.video_gen import get_active_video_provider
from app.services.video_gen import get_missing_video_provider_settings
from app.services.video_gen import get_video_generation_alert_message
from app.services.video_gen import get_video_provider_display_name
from app.services.video_gen import get_video_provider_runtime_issue
from app.services.video_gen import is_video_render_configured


templates = Jinja2Templates(directory="app/templates")


def _read_item_value(item: Any, field: str) -> Any:
    if isinstance(item, dict):
        return item.get(field)
    return getattr(item, field, None)


def build_video_render_state(items: list[Any] | None = None) -> dict[str, Any]:
    resolved_items = items or []
    video_render_configured = is_video_render_configured()
    active_video_provider = get_active_video_provider()
    has_veo_simulated_jobs = any(
        _read_item_value(item, "provider") == "veo"
        and _read_item_value(item, "status") == "simulado"
        for item in resolved_items
    )
    has_shotstack_jobs_while_veo_active = (
        active_video_provider == "veo"
        and any(
            _read_item_value(item, "provider") == "shotstack"
            and (
                _read_item_value(item, "requested_provider")
                or active_video_provider
            )
            == "veo"
            for item in resolved_items
        )
    )

    return {
        "video_render_configured": video_render_configured,
        "video_render_missing_settings": get_missing_video_provider_settings(),
        "video_render_alert_message": get_video_generation_alert_message(),
        "video_render_runtime_issue": get_video_provider_runtime_issue(),
        "active_video_provider": active_video_provider,
        "active_video_provider_label": get_video_provider_display_name(),
        "veo_quota_warning": (
            "Uma ou mais gerações recentes não puderam sair do Veo. "
            "Neste ambiente, isso normalmente indica limite de quota "
            "ou faturamento pendente na Gemini API."
            if (
                active_video_provider == "veo"
                and video_render_configured
                and has_veo_simulated_jobs
            )
            else ""
        ),
        "veo_shotstack_fallback_notice": (
            "Algumas gerações recentes podem ter sido reenviadas ao "
            "Shotstack automaticamente quando o Veo ficou indisponível."
            if has_shotstack_jobs_while_veo_active
            else ""
        ),
    }


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
    render_state = build_video_render_state(items=jobs)
    context = {
        "request": request,
        "user": user,
        "jobs": jobs,
        "error": error,
        "serialized_jobs": [serialize_job(job) for job in jobs],
        "has_demo_mode": (
            (not render_state["video_render_configured"])
            or any(job.status == "simulado" for job in jobs)
        ),
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
            "activeVideoProvider": render_state["active_video_provider"],
            "pollUrl": "/dashboard/jobs/live",
            "pollIntervalMs": 8000,
        },
    }
    context.update(render_state)
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
