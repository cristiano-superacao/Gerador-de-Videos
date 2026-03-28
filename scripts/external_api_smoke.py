import asyncio
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.ai_engine import ContentEngine  # noqa: E402
from app.services.research_api import deep_search  # noqa: E402
from app.services.video_gen import VideoGenerator  # noqa: E402


def is_enabled(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


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


async def validate_shotstack_api() -> None:
    if not (
        os.getenv("SHOTSTACK_API_KEY") and os.getenv("SHOTSTACK_OWNER_ID")
    ):
        print("shotstack:skipped:no-key")
        return

    if not is_enabled(os.getenv("EXTERNAL_API_SMOKE_ALLOW_SHOTSTACK_RENDER")):
        print("shotstack:skipped:render-disabled")
        return

    generator = VideoGenerator()
    result = await generator.render_script(
        script="Teste curto de integração controlada.",
        title="Smoke Test",
    )
    if not result.get("render_id"):
        raise RuntimeError("shotstack:missing-render-id")

    print(f"shotstack:ok:render_id={result['render_id']}")


async def main() -> int:
    if not is_enabled(os.getenv("RUN_EXTERNAL_API_SMOKE")):
        print("external-api-smoke:skipped:disabled")
        return 0

    await validate_research_api()
    await validate_openai_api()
    await validate_shotstack_api()

    print("external-api-smoke:ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
