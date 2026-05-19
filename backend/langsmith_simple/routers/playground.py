import json
from collections.abc import AsyncIterator

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..config import settings
from ..schemas.playground import CompletionRequest, Message

router = APIRouter(tags=["playground"])

AVAILABLE_MODELS = [
    {"name": "gpt-4o", "provider": "openai"},
    {"name": "gpt-4o-mini", "provider": "openai"},
    {"name": "claude-sonnet-4-20250514", "provider": "anthropic"},
    {"name": "claude-haiku-4-5-20251001", "provider": "anthropic"},
    {"name": "deepseek-chat", "provider": "deepseek"},
    {"name": "deepseek-reasoner", "provider": "deepseek"},
    {"name": "qwen-plus", "provider": "qwen"},
]

_PROVIDER_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
}

_PROVIDER_KEYS = {
    "openai": settings.openai_api_key,
    "anthropic": settings.anthropic_api_key,
    "deepseek": settings.deepseek_api_key,
    "qwen": settings.deepseek_api_key,
}


def _build_request(request: CompletionRequest) -> tuple[str, dict, dict]:
    provider = request.provider
    api_key = _PROVIDER_KEYS.get(provider, "")
    if not api_key:
        raise HTTPException(400, f"API key not configured for provider {provider}")

    base_url = _PROVIDER_BASE_URLS[provider]

    if provider == "anthropic":
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        system_msg = None
        messages: list[Message] = []
        for m in request.messages:
            if m.role == "system":
                system_msg = m.content
            else:
                messages.append(m)
        payload: dict = {
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": request.stream,
        }
        if system_msg:
            payload["system"] = system_msg
        url = f"{base_url}/messages"
    else:
        headers = {
            "authorization": f"Bearer {api_key}",
            "content-type": "application/json",
        }
        payload = {
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": request.stream,
        }
        url = f"{base_url}/chat/completions"

    return url, headers, payload


async def _openai_stream(response: httpx.Response) -> AsyncIterator[str]:
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            chunk = line.removeprefix("data: ")
            if chunk == "[DONE]":
                break
            try:
                data = json.loads(chunk)
                delta = data.get("choices", [{}])[0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
            except json.JSONDecodeError:
                continue
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


async def _anthropic_stream(response: httpx.Response) -> AsyncIterator[str]:
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            chunk = line.removeprefix("data: ")
            try:
                data = json.loads(chunk)
                if data.get("type") == "content_block_delta":
                    content = data.get("delta", {}).get("text", "")
                    if content:
                        yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
            except json.JSONDecodeError:
                continue
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


@router.get("/playground/models")
async def list_models():
    providers: dict[str, list[str]] = {}
    for m in AVAILABLE_MODELS:
        providers.setdefault(m["provider"], []).append(m["name"])
    return {"providers": [{"name": k, "models": v} for k, v in providers.items()]}


@router.post("/playground/completion")
async def completion(request: CompletionRequest):
    url, headers, payload = _build_request(request)

    async with httpx.AsyncClient(timeout=120.0) as client:
        if request.stream:
            proxy_response = await client.request(
                "POST", url, headers=headers, json=payload, stream=True
            )
            proxy_response.raise_for_status()

            async def event_generator() -> AsyncIterator[str]:
                if request.provider == "anthropic":
                    async for chunk in _anthropic_stream(proxy_response):
                        yield chunk
                else:
                    async for chunk in _openai_stream(proxy_response):
                        yield chunk

            return StreamingResponse(event_generator(), media_type="text/event-stream")

        proxy_response = await client.post(url, headers=headers, json=payload)
        proxy_response.raise_for_status()
        return proxy_response.json()
