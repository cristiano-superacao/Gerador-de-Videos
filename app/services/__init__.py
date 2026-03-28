from typing import TYPE_CHECKING


__all__ = ["ContentEngine", "VideoGenerator"]


if TYPE_CHECKING:
    from app.services.ai_engine import ContentEngine
    from app.services.video_gen import VideoGenerator


def __getattr__(name: str):
    if name == "ContentEngine":
        from app.services.ai_engine import ContentEngine

        return ContentEngine
    if name == "VideoGenerator":
        from app.services.video_gen import VideoGenerator

        return VideoGenerator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
