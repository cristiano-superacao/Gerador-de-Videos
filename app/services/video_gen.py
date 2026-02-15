from typing import Dict

import httpx

from app.core.config import settings


class VideoGenerator:
    async def render_script(self, script: str, title: str) -> Dict[str, str]:
        if not settings.shotstack_api_key or not settings.shotstack_owner_id:
            # URLs de demonstração do Shotstack para modo simulado
            demo_videos = [
                "https://cdn.shotstack.io/au/v1/msgtwx8iw6/8a85ba4a-58dc-4981-91ca-5289d9ae6d5e.mp4",
                "https://cdn.shotstack.io/au/v1/msgtwx8iw6/e8077f59-f17a-4e37-b703-6c8a16d7f49e.mp4",
                "https://cdn.shotstack.io/au/v1/msgtwx8iw6/3b36b6b5-3d3e-4c5e-8e0e-9c8f6a0b5d3e.mp4",
            ]
            import hashlib
            # Seleciona um vídeo de demo baseado no hash do título
            video_index = int(hashlib.md5(title.encode()).hexdigest(), 16) % len(demo_videos)
            
            return {
                "status": "simulado",
                "provider": "shotstack",
                "render_id": "mock-render-id",
                "output_url": demo_videos[video_index],
                "message": (
                    "Configure SHOTSTACK_API_KEY e SHOTSTACK_OWNER_ID "
                    "para render real."
                ),
            }

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
            "merge": [
                {
                    "find": "OWNER_ID",
                    "replace": settings.shotstack_owner_id,
                }
            ],
        }

        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                "https://api.shotstack.io/stage/render",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json().get("response", {})

        return {
            "status": "queued",
            "provider": "shotstack",
            "render_id": data.get("id", ""),
            "output_url": "",
            "message": "Render enviado com sucesso.",
        }

    async def get_render_status(self, render_id: str) -> Dict[str, str]:
        if not render_id:
            return {"status": "queued", "output_url": ""}

        if not settings.shotstack_api_key or render_id == "mock-render-id":
            # Mantém o output_url existente no banco para modo simulado
            return {"status": "simulado", "output_url": None}

        headers = {"x-api-key": settings.shotstack_api_key}
        url = f"https://api.shotstack.io/stage/render/{render_id}"

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
