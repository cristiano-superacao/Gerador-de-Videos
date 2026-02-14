import importlib
import io
from typing import Any, Dict, List

from app.core.config import settings
from app.services.research_api import deep_search


class ContentEngine:
    def __init__(self) -> None:
        self.client = None
        if settings.openai_api_key:
            try:
                openai_module = importlib.import_module("openai")
                openai_client = getattr(openai_module, "OpenAI")
                self.client = openai_client(api_key=settings.openai_api_key)
            except ImportError:
                self.client = None

    async def process_input(
        self,
        data_type: str,
        content: str,
        video_bytes: bytes | None = None,
        video_filename: str | None = None,
    ) -> str:
        if data_type == "video":
            if not video_bytes:
                return "Arquivo de vídeo/áudio não enviado."

            if not self.client:
                base_name = video_filename or "arquivo"
                return (
                    "Transcrição simulada para desenvolvimento "
                    "sem OPENAI_API_KEY. "
                    f"Arquivo recebido: {base_name}."
                )

            try:
                audio_stream = io.BytesIO(video_bytes)
                audio_stream.name = video_filename or "upload.mp4"

                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_stream,
                )
                return transcript.text
            except Exception:
                return (
                    "Falha ao transcrever com Whisper. "
                    "Use texto ou link enquanto valida as chaves."
                )

        return content

    async def generate_social_content(self, raw_text: str) -> List[str]:
        context = await deep_search(raw_text)

        if not self.client:
            return [
                (
                    "Roteiro 1: Gancho + problema + solução sobre: "
                    f"{context[:220]}"
                ),
                (
                    "Roteiro 2: História pessoal + insight + CTA sobre: "
                    f"{context[:220]}"
                ),
                (
                    "Roteiro 3: Lista prática de passos acionáveis "
                    f"sobre: {context[:220]}"
                ),
            ]

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Crie 3 roteiros curtos e distintos para "
                        "Reels/TikTok, com gancho forte, "
                        "desenvolvimento em bullets e chamada final para ação."
                    ),
                },
                {"role": "user", "content": context},
            ],
            temperature=0.7,
        )

        content = response.choices[0].message.content or ""
        chunks = [
            item.strip() for item in content.split("\n\n") if item.strip()
        ]
        return chunks[:3] if len(chunks) >= 3 else [content]

    async def build_story_package(
        self,
        source_type: str,
        source_content: str,
        video_bytes: bytes | None = None,
        video_filename: str | None = None,
    ) -> Dict[str, Any]:
        raw_text = await self.process_input(
            data_type=source_type,
            content=source_content,
            video_bytes=video_bytes,
            video_filename=video_filename,
        )
        scripts = await self.generate_social_content(raw_text)
        return {
            "source_type": source_type,
            "source_content": source_content,
            "scripts": scripts,
        }
