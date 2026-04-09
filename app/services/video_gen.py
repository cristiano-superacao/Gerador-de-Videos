import hashlib
import importlib
import logging
from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)

VIDEO_PROVIDER_SHOTSTACK = "shotstack"
VIDEO_PROVIDER_VEO = "veo"
SUPPORTED_VIDEO_PROVIDERS = {
    VIDEO_PROVIDER_SHOTSTACK,
    VIDEO_PROVIDER_VEO,
}
GENERATED_MEDIA_DIR = (
    Path(__file__).resolve().parents[2] / "static" / "generated"
)


def get_active_video_provider() -> str:
    provider = settings.video_provider.strip().lower()
    if provider in SUPPORTED_VIDEO_PROVIDERS:
        return provider
    return VIDEO_PROVIDER_SHOTSTACK


def get_video_provider_display_name(provider: str | None = None) -> str:
    resolved_provider = provider or get_active_video_provider()
    if resolved_provider == VIDEO_PROVIDER_VEO:
        return "Veo"
    return "Shotstack"


def _load_veo_runtime():
    try:
        genai_module = importlib.import_module("google.genai")
        types_module = importlib.import_module("google.genai.types")
        pil_image_module = importlib.import_module("PIL.Image")
    except ImportError:
        return None, None, None

    return genai_module, types_module, pil_image_module


def get_video_provider_runtime_issue(provider: str | None = None) -> str:
    resolved_provider = provider or get_active_video_provider()
    if resolved_provider != VIDEO_PROVIDER_VEO:
        return ""

    genai_module, _, pil_image_module = _load_veo_runtime()
    if genai_module and pil_image_module:
        return ""

    return (
        "Instale google-genai e pillow para habilitar render real via Veo."
    )


def get_missing_video_provider_settings() -> list[str]:
    provider = get_active_video_provider()
    missing_settings = []

    if provider == VIDEO_PROVIDER_VEO:
        if not settings.gemini_api_key:
            missing_settings.append("GEMINI_API_KEY")
        return missing_settings

    if not settings.shotstack_api_key:
        missing_settings.append("SHOTSTACK_API_KEY")

    return missing_settings


def is_video_render_configured() -> bool:
    return (
        not get_missing_video_provider_settings()
        and not get_video_provider_runtime_issue()
    )


def get_video_generation_alert_message() -> str:
    provider = get_active_video_provider()
    missing_settings = get_missing_video_provider_settings()
    runtime_issue = get_video_provider_runtime_issue(provider)

    if runtime_issue:
        return runtime_issue

    if not missing_settings:
        return ""

    missing_settings_label = ", ".join(missing_settings)

    if provider == VIDEO_PROVIDER_VEO:
        return (
            "Configure "
            f"{missing_settings_label} para render real com Veo. "
            "No modo demonstração, o sistema gera os roteiros, "
            "mas não publica a imagem-guia nem o vídeo final."
        )

    return (
        "Configure "
        f"{missing_settings_label} para render real. "
        "No modo demonstração, o sistema gera os roteiros, "
        "mas não publica um link externo de vídeo."
    )


def get_video_provider_error_message(
    status_code: int | None = None,
    provider: str | None = None,
) -> str:
    resolved_provider = provider or get_active_video_provider()

    if resolved_provider == VIDEO_PROVIDER_VEO:
        if status_code in {401, 403}:
            return (
                "A Gemini API recusou a credencial configurada. "
                "Revise GEMINI_API_KEY. Enquanto isso, o sistema "
                "permanece em modo demonstração sem publicar mídia final."
            )

        if status_code == 429:
            return (
                "A Gemini API recusou a geração por limite de uso ou "
                "quota esgotada. Revise o plano e o faturamento da conta "
                "no Google AI Studio antes de tentar novo render. "
                "Enquanto isso, o sistema permanece em modo demonstração "
                "sem publicar mídia final."
            )

        if status_code is not None:
            return (
                "A Gemini API retornou erro ao iniciar a geração com Veo "
                f"(HTTP {status_code}). O sistema permanece em modo "
                "demonstração sem publicar mídia final."
            )

        return (
            "Não foi possível iniciar a geração no Veo. O sistema "
            "permanece em modo demonstração sem publicar mídia final."
        )

    if status_code in {401, 403}:
        return (
            "Shotstack recusou a credencial configurada. "
            "Revise SHOTSTACK_API_KEY. Enquanto isso, o sistema "
            "permanece em modo demonstração sem publicar link externo."
        )

    if status_code is not None:
        return (
            "Shotstack retornou erro ao iniciar o render "
            f"(HTTP {status_code}). O sistema permanece em modo "
            "demonstração sem publicar link externo."
        )

    return (
        "Não foi possível iniciar o render no Shotstack. O sistema "
        "permanece em modo demonstração sem publicar link externo."
    )


def _ensure_generated_media_dir() -> Path:
    GENERATED_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    return GENERATED_MEDIA_DIR


def _build_generated_media_name(render_id: str, suffix: str) -> str:
    digest = hashlib.sha1(render_id.encode("utf-8")).hexdigest()[:16]
    return f"{digest}{suffix}"


def _build_guide_image_prompt(title: str, script: str) -> str:
    condensed_script = " ".join(script.split())[:900]
    return (
        "Crie um frame vertical 9:16 para um vídeo curto de redes sociais. "
        f"Tema: {title}. "
        f"Roteiro base: {condensed_script}. "
        "Direção de arte: cinematográfica, profissional, realista, "
        "com composição limpa, iluminação premium, assunto principal claro, "
        "sem texto sobreposto, sem logotipos e sem marca d'água."
    )


def _build_veo_prompt(title: str, script: str) -> str:
    condensed_script = " ".join(script.split())[:900]
    return (
        "Crie um vídeo vertical profissional para Reels ou TikTok, "
        "com 8 segundos, "
        "visual premium, ritmo claro e linguagem cinematográfica. "
        f"Título de produção: {title}. "
        f"Use este roteiro como guia narrativo: {condensed_script}. "
        "Mantenha movimento de câmera suave, ação coerente com o roteiro, "
        "boa legibilidade visual em telas móveis, sem legendas queimadas, "
        "sem texto em tela e sem marca d'água."
    )


def _build_demo_payload(
    provider: str,
    message: str,
    preview_image_url: str = "",
) -> dict[str, Any]:
    return {
        "status": "simulado",
        "provider": provider,
        "render_id": "mock-render-id",
        "output_url": "",
        "preview_image_url": preview_image_url,
        "message": message,
    }


def _is_shotstack_fallback_available() -> bool:
    return bool(settings.shotstack_api_key)


def get_shotstack_base_url() -> str:
    resolved_env = settings.shotstack_env.strip().lower()
    if resolved_env in {"production", "prod", "live"}:
        return "https://api.shotstack.io/v1"
    return "https://api.shotstack.io/stage"


def _is_veo_quota_payload(payload: dict[str, Any]) -> bool:
    return payload.get("provider") == VIDEO_PROVIDER_VEO and (
        payload.get("error_code") == 429
        or "quota esgotada" in payload.get("message", "").lower()
        or "limite de uso" in payload.get("message", "").lower()
    )


def _build_veo_fallback_message(
    veo_message: str,
    shotstack_message: str,
) -> str:
    prefix = (
        "Veo indisponível por limite de uso ou quota esgotada. "
        "O render foi reenviado automaticamente ao Shotstack."
    )
    if shotstack_message:
        return f"{prefix} {shotstack_message}"
    if veo_message:
        return f"{prefix} Motivo original do Veo: {veo_message}"
    return prefix


class VideoGenerator:
    async def render_script(self, script: str, title: str) -> dict[str, Any]:
        provider = get_active_video_provider()
        if provider == VIDEO_PROVIDER_VEO:
            veo_result = self._render_with_veo(script=script, title=title)
            if not _is_veo_quota_payload(veo_result):
                return veo_result

            if not _is_shotstack_fallback_available():
                veo_result["message"] = (
                    f"{veo_result['message']} "
                    "O fallback automático para Shotstack está "
                    "indisponível porque SHOTSTACK_API_KEY não foi "
                    "configurada."
                )
                return veo_result

            shotstack_result = await self._render_with_shotstack(
                script=script,
                title=title,
            )
            if shotstack_result.get("status") == "simulado":
                veo_result["message"] = (
                    f"{veo_result['message']} "
                    "O fallback automático para Shotstack também falhou. "
                    f"{shotstack_result.get('message', '')}"
                ).strip()
                return veo_result

            shotstack_result["requested_provider"] = VIDEO_PROVIDER_VEO
            shotstack_result["message"] = _build_veo_fallback_message(
                veo_message=veo_result.get("message", ""),
                shotstack_message=shotstack_result.get("message", ""),
            )
            fallback_preview_image_url = veo_result.get("preview_image_url")
            if fallback_preview_image_url and not shotstack_result.get(
                "preview_image_url"
            ):
                shotstack_result["preview_image_url"] = (
                    fallback_preview_image_url
                )
            return shotstack_result

        return await self._render_with_shotstack(script=script, title=title)

    async def _render_with_shotstack(
        self,
        script: str,
        title: str,
    ) -> dict[str, Any]:
        if (
            get_active_video_provider() == VIDEO_PROVIDER_SHOTSTACK
            and not is_video_render_configured()
        ):
            return _build_demo_payload(
                provider=VIDEO_PROVIDER_SHOTSTACK,
                message=get_video_generation_alert_message(),
            )

        headers = {
            "x-api-key": settings.shotstack_api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "timeline": {
                "tracks": [
                    {
                        "clips": [
                            {
                                "asset": {
                                    "type": "title",
                                    "text": title,
                                    "style": "minimal",
                                },
                                "start": 0,
                                "length": 6,
                            },
                            {
                                "asset": {
                                    "type": "title",
                                    "text": script,
                                    "style": "blockbuster",
                                },
                                "start": 6,
                                "length": 14,
                            },
                        ]
                    }
                ]
            },
            "output": {"format": "mp4", "resolution": "hd", "fps": 30},
        }

        if settings.shotstack_owner_id:
            payload["merge"] = [
                {
                    "find": "OWNER_ID",
                    "replace": settings.shotstack_owner_id,
                }
            ]

        try:
            async with httpx.AsyncClient(timeout=45) as client:
                response = await client.post(
                    f"{get_shotstack_base_url()}/render",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json().get("response", {})
        except httpx.HTTPStatusError as exc:
            return _build_demo_payload(
                provider=VIDEO_PROVIDER_SHOTSTACK,
                message=get_video_provider_error_message(
                    exc.response.status_code,
                    provider=VIDEO_PROVIDER_SHOTSTACK,
                ),
            )
        except httpx.HTTPError:
            return _build_demo_payload(
                provider=VIDEO_PROVIDER_SHOTSTACK,
                message=get_video_provider_error_message(
                    provider=VIDEO_PROVIDER_SHOTSTACK
                ),
            )

        return {
            "status": "queued",
            "provider": VIDEO_PROVIDER_SHOTSTACK,
            "render_id": data.get("id", ""),
            "output_url": "",
            "preview_image_url": "",
            "message": "Render enviado com sucesso.",
        }

    def _render_with_veo(self, script: str, title: str) -> dict[str, Any]:
        if not is_video_render_configured():
            return _build_demo_payload(
                provider=VIDEO_PROVIDER_VEO,
                message=get_video_generation_alert_message(),
            )

        genai_module, types_module, pil_image_module = _load_veo_runtime()
        if not genai_module or not types_module or not pil_image_module:
            return _build_demo_payload(
                provider=VIDEO_PROVIDER_VEO,
                message=get_video_generation_alert_message(),
            )

        try:
            client = genai_module.Client(api_key=settings.gemini_api_key)
            try:
                preview_image_url = self._generate_guide_image(
                    client=client,
                    types_module=types_module,
                    title=title,
                    script=script,
                )
            except Exception as exc:  # pragma: no cover - runtime externo
                logger.warning("veo guide image fallback", exc_info=exc)
                preview_image_url = ""

            video_prompt = _build_veo_prompt(title=title, script=script)
            veo_config = types_module.GenerateVideosConfig(
                aspect_ratio=settings.veo_aspect_ratio,
                duration_seconds=settings.veo_duration_seconds,
            )

            image_path = None
            if preview_image_url:
                image_path = (
                    _ensure_generated_media_dir()
                    / Path(preview_image_url).name
                )

            if image_path and image_path.exists():
                with pil_image_module.open(image_path):
                    guide_image = types_module.Image(
                        image_bytes=image_path.read_bytes(),
                        mime_type="image/png",
                    )

                operation = client.models.generate_videos(
                    model=settings.veo_model,
                    prompt=video_prompt,
                    image=guide_image,
                    config=veo_config,
                )
            else:
                operation = client.models.generate_videos(
                    model=settings.veo_model,
                    prompt=video_prompt,
                    config=veo_config,
                )
        except httpx.HTTPStatusError as exc:
            fallback_preview_image_url = (
                preview_image_url if "preview_image_url" in locals() else ""
            )
            return _build_demo_payload(
                provider=VIDEO_PROVIDER_VEO,
                message=get_video_provider_error_message(
                    exc.response.status_code,
                    provider=VIDEO_PROVIDER_VEO,
                ),
                preview_image_url=fallback_preview_image_url,
            ) | {"error_code": exc.response.status_code}
        except Exception as exc:  # pragma: no cover - defesa em runtime real
            logger.warning("veo render fallback", exc_info=exc)
            fallback_preview_image_url = (
                preview_image_url if "preview_image_url" in locals() else ""
            )
            status_code = (
                getattr(exc, "status_code", None)
                or getattr(exc, "code", None)
            )
            return _build_demo_payload(
                provider=VIDEO_PROVIDER_VEO,
                message=get_video_provider_error_message(
                    status_code=status_code,
                    provider=VIDEO_PROVIDER_VEO,
                ),
                preview_image_url=fallback_preview_image_url,
            ) | {"error_code": status_code}

        return {
            "status": "queued",
            "provider": VIDEO_PROVIDER_VEO,
            "render_id": getattr(operation, "name", "") or "",
            "output_url": "",
            "preview_image_url": preview_image_url,
            "message": (
                "Geração enviada ao Veo com imagem-guia criada "
                "a partir do roteiro."
                if preview_image_url
                else "Geração enviada ao Veo com prompt textual do roteiro."
            ),
        }

    def _generate_guide_image(
        self,
        client,
        types_module,
        title: str,
        script: str,
    ) -> str:
        prompt = _build_guide_image_prompt(title=title, script=script)
        response = client.models.generate_images(
            model=settings.gemini_image_model,
            prompt=prompt,
            config=types_module.GenerateImagesConfig(
                aspect_ratio=settings.veo_aspect_ratio,
            ),
        )

        image_dir = _ensure_generated_media_dir()
        image_name = _build_generated_media_name(
            render_id=f"{title}-{script}",
            suffix=".png",
        )
        image_path = image_dir / image_name

        generated_images = getattr(response, "generated_images", None) or []
        for generated_image in generated_images:
            image = getattr(generated_image, "image", None)
            raw_data = getattr(image, "image_bytes", None)
            if raw_data:
                image_path.write_bytes(raw_data)
                return f"/static/generated/{image_name}"

        return ""

    async def get_render_status(
        self,
        render_id: str,
        provider: str | None = None,
    ) -> dict[str, str | None]:
        resolved_provider = provider or get_active_video_provider()

        if resolved_provider == VIDEO_PROVIDER_VEO:
            return self._get_veo_status(render_id=render_id)

        if not render_id:
            return {"status": "queued", "output_url": ""}

        if (
            not is_video_render_configured()
            or render_id == "mock-render-id"
        ):
            # Mantém o output_url existente no banco para modo simulado
            return {"status": "simulado", "output_url": None}

        headers = {"x-api-key": settings.shotstack_api_key}
        url = f"{get_shotstack_base_url()}/render/{render_id}"

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json().get("response", {})
        except Exception:
            return {"status": "queued", "output_url": ""}

        return {
            "status": data.get("status", "queued"),
            "output_url": data.get("url") or "",
        }

    def _get_veo_status(self, render_id: str) -> dict[str, str | None]:
        if not render_id:
            return {"status": "queued", "output_url": ""}

        if not is_video_render_configured() or render_id == "mock-render-id":
            return {"status": "simulado", "output_url": None}

        genai_module, types_module, _ = _load_veo_runtime()
        if not genai_module or not types_module:
            return {"status": "queued", "output_url": ""}

        try:
            client = genai_module.Client(api_key=settings.gemini_api_key)
            output_name = _build_generated_media_name(render_id, ".mp4")
            local_path = _ensure_generated_media_dir() / output_name
            public_url = f"/static/generated/{output_name}"

            if local_path.exists():
                return {"status": "done", "output_url": public_url}

            operation_ref = render_id
            operation_class = getattr(
                types_module,
                "GenerateVideosOperation",
                None,
            )
            if operation_class is not None:
                operation_ref = operation_class(name=render_id)

            operation = client.operations.get(operation_ref)
            if not getattr(operation, "done", False):
                return {"status": "queued", "output_url": ""}

            response = getattr(operation, "response", None)
            generated_videos = (
                getattr(response, "generated_videos", None) or []
            )
            if not generated_videos:
                return {"status": "failed", "output_url": ""}

            generated_video = generated_videos[0]
            video_file = getattr(generated_video, "video", None)
            if not video_file:
                return {"status": "failed", "output_url": ""}

            client.files.download(file=video_file)
            save_method = getattr(video_file, "save", None)
            if callable(save_method):
                save_method(local_path)
            else:
                return {"status": "failed", "output_url": ""}

            return {"status": "done", "output_url": public_url}
        except Exception as exc:  # pragma: no cover - defesa para SDK/runtime
            logger.warning("veo status polling fallback", exc_info=exc)
            return {"status": "queued", "output_url": ""}
