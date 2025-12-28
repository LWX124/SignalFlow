"""DeepSeek Provider.

支持模型: deepseek-chat
"""

import json
from typing import AsyncGenerator

from ..base import BaseTextProvider
from ..types import (
    ChatMessage,
    ProviderType,
    StreamChoice,
    StreamDelta,
    TextGenerationChoice,
    TextGenerationRequest,
    TextGenerationResponse,
    TextStreamChunk,
    TextUsage,
)

# DeepSeek 支持的模型
DEEPSEEK_MODELS: list[str] = ["deepseek-chat"]

# DeepSeek 默认模型
DEEPSEEK_DEFAULT_MODEL = "deepseek-chat"

# DeepSeek API 基础 URL
DEEPSEEK_BASE_URL = "https://api.deepseek.com"


class DeepSeekProvider(BaseTextProvider):
    """DeepSeek Provider 实现."""

    def __init__(self, api_key: str) -> None:
        super().__init__(
            api_key=api_key,
            base_url=DEEPSEEK_BASE_URL,
            default_model=DEEPSEEK_DEFAULT_MODEL,
            supported_models=DEEPSEEK_MODELS.copy(),
        )

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.DEEPSEEK

    async def generate_text(
        self, request: TextGenerationRequest
    ) -> TextGenerationResponse:
        """生成文本响应 (非流式)."""
        model = self._get_model(request)

        payload = {
            "model": model,
            "messages": [
                {"role": msg.role, "content": msg.content} for msg in request.messages
            ],
            "stream": False,
        }

        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.top_p is not None:
            payload["top_p"] = request.top_p

        response = await self._client.post(
            f"{self._base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

        if response.status_code != 200:
            await self._handle_response_error(response)

        data = response.json()

        return TextGenerationResponse(
            id=data["id"],
            model=data["model"],
            choices=[
                TextGenerationChoice(
                    index=choice["index"],
                    message=ChatMessage(
                        role=choice["message"]["role"],
                        content=choice["message"]["content"],
                    ),
                    finish_reason=choice["finish_reason"],
                )
                for choice in data["choices"]
            ],
            usage=TextUsage(
                prompt_tokens=data["usage"]["prompt_tokens"],
                completion_tokens=data["usage"]["completion_tokens"],
                total_tokens=data["usage"]["total_tokens"],
            )
            if data.get("usage")
            else None,
        )

    async def generate_text_stream(
        self, request: TextGenerationRequest
    ) -> AsyncGenerator[TextStreamChunk, None]:
        """生成文本响应 (流式)."""
        model = self._get_model(request)

        payload = {
            "model": model,
            "messages": [
                {"role": msg.role, "content": msg.content} for msg in request.messages
            ],
            "stream": True,
        }

        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.top_p is not None:
            payload["top_p"] = request.top_p

        async with self._client.stream(
            "POST",
            f"{self._base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        ) as response:
            if response.status_code != 200:
                await response.aread()
                await self._handle_response_error(response)

            buffer = ""
            async for chunk in response.aiter_text():
                buffer += chunk
                lines = buffer.split("\n")
                buffer = lines.pop()

                for line in lines:
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue

                    data = line[6:]
                    if data == "[DONE]":
                        return

                    try:
                        parsed = json.loads(data)
                        yield TextStreamChunk(
                            id=parsed["id"],
                            model=parsed["model"],
                            choices=[
                                StreamChoice(
                                    index=choice["index"],
                                    delta=StreamDelta(
                                        role=choice["delta"].get("role"),
                                        content=choice["delta"].get("content"),
                                    ),
                                    finish_reason=choice.get("finish_reason"),
                                )
                                for choice in parsed["choices"]
                            ],
                        )
                    except json.JSONDecodeError:
                        continue


def create_deepseek_provider(api_key: str) -> DeepSeekProvider:
    """创建 DeepSeek Provider 实例."""
    return DeepSeekProvider(api_key)
