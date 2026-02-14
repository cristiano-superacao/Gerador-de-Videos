from typing import Dict

import httpx

from app.core.config import settings


async def deep_search(topic: str) -> str:
    if settings.tavily_api_key:
        return await _search_with_tavily(topic)

    if settings.perplexity_api_key:
        return await _search_with_perplexity(topic)

    return (
        "Pesquisa externa indisponível no momento. "
        f"Use o tema original como base: {topic}"
    )


async def _search_with_tavily(topic: str) -> str:
    payload: Dict[str, str | int | bool] = {
        "api_key": settings.tavily_api_key,
        "query": topic,
        "max_results": 5,
        "include_answer": True,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.tavily.com/search",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    answer = data.get("answer") or ""
    snippets = "\n".join(
        item.get("content", "") for item in data.get("results", [])
    )
    return f"Resumo: {answer}\n\nFontes: {snippets}".strip()


async def _search_with_perplexity(topic: str) -> str:
    headers = {
        "Authorization": f"Bearer {settings.perplexity_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": "Faça uma pesquisa profunda e objetiva.",
            },
            {"role": "user", "content": topic},
        ],
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    return data["choices"][0]["message"]["content"]
