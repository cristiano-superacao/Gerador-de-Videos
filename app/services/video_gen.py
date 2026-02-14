from typing import Dict

import httpx

from app.core.config import settings


class VideoGenerator:
    async def render_script(self, script: str, title: str) -> Dict[str, str]:
        if not settings.shotstack_api_key or not settings.shotstack_owner_id:
            return {
                "status": "simulado",
                "provider": "shotstack",
                "render_id": "mock-render-id",
                "output_url": "",
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
            return {"status": "simulado", "output_url": ""}

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
