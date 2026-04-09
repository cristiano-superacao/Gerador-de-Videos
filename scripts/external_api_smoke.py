import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from app.services.ai_engine import ContentEngine  # noqa: E402
from app.services.research_api import deep_search  # noqa: E402
from app.services.video_gen import get_active_video_provider  # noqa: E402
from app.services.video_gen import VideoGenerator  # noqa: E402


def is_enabled(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def get_provider_render_flag(provider: str) -> str:
    if provider == "veo":
        return "EXTERNAL_API_SMOKE_ALLOW_VEO_RENDER"
    return "EXTERNAL_API_SMOKE_ALLOW_SHOTSTACK_RENDER"


def get_provider_key(provider: str) -> str:
    if provider == "veo":
        return os.getenv("GEMINI_API_KEY", "")
    return os.getenv("SHOTSTACK_API_KEY", "")


async def wait_for_render_completion(
    generator: VideoGenerator,
    provider: str,
    render_id: str,
) -> str:
    timeout_seconds = int(
        os.getenv("EXTERNAL_API_SMOKE_RENDER_TIMEOUT", "300")
    )
    interval_seconds = int(
        os.getenv("EXTERNAL_API_SMOKE_POLL_INTERVAL", "15")
    )
    deadline = asyncio.get_running_loop().time() + timeout_seconds

    while asyncio.get_running_loop().time() < deadline:
        status_payload = await generator.get_render_status(
            render_id=render_id,
            provider=provider,
        )
        status = status_payload.get("status", "queued")
        output_url = status_payload.get("output_url") or ""

        if status == "done" and output_url:
            print(f"{provider}:done:output={output_url}")
            return output_url

        if status in {"failed", "simulado"}:
            raise RuntimeError(f"{provider}:unexpected-status:{status}")

        print(f"{provider}:poll:status={status}")
        await asyncio.sleep(interval_seconds)

    raise RuntimeError(f"{provider}:timeout:render-not-finished")


async def validate_research_api() -> None:
    if not (os.getenv("TAVILY_API_KEY") or os.getenv("PERPLEXITY_API_KEY")):
        print("research:skipped:no-key")
        return

    result = await deep_search("Panorama de IA generativa para PMEs")
    if not result.strip():
        raise RuntimeError("research:empty-response")

    print("research:ok")


async def validate_openai_api() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print("openai:skipped:no-key")
        return

    engine = ContentEngine()
    scripts = await engine.generate_social_content(
        "Benefícios da IA generativa para pequenas empresas"
    )
    if not scripts or not scripts[0].strip():
        raise RuntimeError("openai:empty-response")

    print(f"openai:ok:scripts={len(scripts)}")


async def validate_active_video_provider() -> None:
    provider = get_active_video_provider()
    provider_key = get_provider_key(provider)
    allow_render_flag = get_provider_render_flag(provider)

    if not provider_key:
        print(f"{provider}:skipped:no-key")
        return

    if not is_enabled(os.getenv(allow_render_flag)):
        print(f"{provider}:skipped:render-disabled")
        return

    generator = VideoGenerator()
    result = await generator.render_script(
        script="Teste curto de integração controlada.",
        title="Smoke Test",
    )

    if result.get("status") == "simulado":
        raise RuntimeError(
            f"{provider}:simulado:{result.get('message', 'sem-detalhes')}"
        )

    if not result.get("render_id"):
        raise RuntimeError(f"{provider}:missing-render-id")

    resolved_provider = result.get("provider") or provider

    preview_image_url = result.get("preview_image_url") or ""
    if preview_image_url:
        print(f"{resolved_provider}:ok:preview={preview_image_url}")

    print(f"{resolved_provider}:ok:render_id={result['render_id']}")
    await wait_for_render_completion(
        generator=generator,
        provider=resolved_provider,
        render_id=result["render_id"],
    )


async def main() -> int:
    if not is_enabled(os.getenv("RUN_EXTERNAL_API_SMOKE")):
        print("external-api-smoke:skipped:disabled")
        return 0

    await validate_research_api()
    await validate_openai_api()
    await validate_active_video_provider()

    print("external-api-smoke:ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
