import asyncio
from pathlib import Path

import httpx

from app.services.video_gen import get_shotstack_base_url
from app.services.video_gen import get_missing_video_provider_settings
from app.services.video_gen import VideoGenerator


class FailingShotstackClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, headers=None, json=None):
        request = httpx.Request("POST", url, headers=headers, json=json)
        response = httpx.Response(403, request=request)
        raise httpx.HTTPStatusError(
            "403 Forbidden",
            request=request,
            response=response,
        )


def test_render_script_falls_back_to_demo_when_shotstack_rejects_key(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.video_gen.settings.shotstack_api_key",
        "fake-key",
    )
    monkeypatch.setattr(
        "app.services.video_gen.settings.shotstack_owner_id",
        "",
    )
    monkeypatch.setattr(
        "app.services.video_gen.httpx.AsyncClient",
        lambda timeout: FailingShotstackClient(),
    )

    result = asyncio.run(
        VideoGenerator().render_script(
            script="Teste de falha no provider",
            title="Teste",
        )
    )

    assert result["status"] == "simulado"
    assert result["render_id"] == "mock-render-id"
    assert "Shotstack recusou a credencial configurada" in result["message"]


class FakeSavedImage:
    def save(self, path):
        Path(path).write_bytes(b"fake-image")


class FakeImagePart:
    def as_image(self):
        return FakeSavedImage()


class FakeImageResponse:
    parts = [FakeImagePart()]


class FakeOperation:
    name = "operations/veo-123"


class FakeModels:
    def generate_images(self, model, prompt, config):
        return type(
            "FakeGenerateImagesResponse",
            (),
            {
                "generated_images": [
                    type(
                        "FakeGeneratedImage",
                        (),
                        {
                            "image": type(
                                "FakeSdkImage",
                                (),
                                {"image_bytes": b"fake-image"},
                            )()
                        },
                    )()
                ]
            },
        )()

    def generate_videos(self, model, prompt, config, image=None):
        return FakeOperation()


class FakeClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.models = FakeModels()


class FakeGenaiModule:
    Client = FakeClient


class FakeTypesModule:
    class Image:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class GenerateImagesConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class GenerateVideosConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs


class FakeOpenedImage:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakePilImageModule:
    @staticmethod
    def open(path):
        return FakeOpenedImage()


def test_veo_requires_gemini_key(monkeypatch):
    monkeypatch.setattr(
        "app.services.video_gen.settings.video_provider",
        "veo",
    )
    monkeypatch.setattr("app.services.video_gen.settings.gemini_api_key", "")

    assert get_missing_video_provider_settings() == ["GEMINI_API_KEY"]


def test_get_shotstack_base_url_uses_live_for_production(monkeypatch):
    monkeypatch.setattr(
        "app.services.video_gen.settings.shotstack_env",
        "production",
    )

    assert get_shotstack_base_url() == "https://api.shotstack.io/v1"


def test_get_shotstack_base_url_uses_stage_by_default(monkeypatch):
    monkeypatch.setattr(
        "app.services.video_gen.settings.shotstack_env",
        "stage",
    )

    assert get_shotstack_base_url() == "https://api.shotstack.io/stage"


def test_render_script_queues_veo_job_with_guide_image(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(
        "app.services.video_gen.settings.video_provider",
        "veo",
    )
    monkeypatch.setattr(
        "app.services.video_gen.settings.gemini_api_key",
        "gemini-key",
    )
    monkeypatch.setattr(
        "app.services.video_gen._load_veo_runtime",
        lambda: (FakeGenaiModule, FakeTypesModule, FakePilImageModule),
    )
    monkeypatch.setattr("app.services.video_gen.GENERATED_MEDIA_DIR", tmp_path)

    result = asyncio.run(
        VideoGenerator().render_script(
            script="Roteiro com abertura forte, desenvolvimento e CTA.",
            title="Teste Veo",
        )
    )

    assert result["status"] == "queued"
    assert result["provider"] == "veo"
    assert result["render_id"] == "operations/veo-123"
    assert result["preview_image_url"].startswith("/static/generated/")
    assert "imagem-guia" in result["message"]


def test_render_script_falls_back_to_shotstack_when_veo_quota_is_exhausted(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services.video_gen.settings.video_provider",
        "veo",
    )
    monkeypatch.setattr(
        "app.services.video_gen.settings.shotstack_api_key",
        "shotstack-key",
    )

    def fake_render_with_veo(self, script, title):
        return {
            "status": "simulado",
            "provider": "veo",
            "render_id": "mock-render-id",
            "output_url": "",
            "preview_image_url": "",
            "message": (
                "A Gemini API recusou a geração por limite de uso ou "
                "quota esgotada."
            ),
            "error_code": 429,
        }

    async def fake_render_with_shotstack(self, script, title):
        return {
            "status": "queued",
            "provider": "shotstack",
            "render_id": "shotstack-render-123",
            "output_url": "",
            "preview_image_url": "",
            "message": "Render enviado com sucesso.",
        }

    monkeypatch.setattr(
        VideoGenerator,
        "_render_with_veo",
        fake_render_with_veo,
    )
    monkeypatch.setattr(
        VideoGenerator,
        "_render_with_shotstack",
        fake_render_with_shotstack,
    )

    result = asyncio.run(
        VideoGenerator().render_script(
            script="Roteiro curto para fallback.",
            title="Fallback Veo",
        )
    )

    assert result["status"] == "queued"
    assert result["provider"] == "shotstack"
    assert result["requested_provider"] == "veo"
    assert result["render_id"] == "shotstack-render-123"
    assert "reenviado automaticamente ao Shotstack" in result["message"]
