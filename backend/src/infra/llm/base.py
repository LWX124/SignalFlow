"""LLM Provider 基类."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, NoReturn

import httpx

from .types import (
    ImageGenerationRequest,
    ImageGenerationResponse,
    ImageTaskStatusResponse,
    LLMError,
    LLMErrorCode,
    ModelType,
    ProviderType,
    TextGenerationRequest,
    TextGenerationResponse,
    TextStreamChunk,
)


class BaseProvider(ABC):
    """Provider 公共基类."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        default_model: str,
        supported_models: list[str],
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._default_model = default_model
        self._supported_models = supported_models
        self._client = httpx.AsyncClient(timeout=60.0)

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """获取供应商类型."""
        ...

    @property
    @abstractmethod
    def model_type(self) -> ModelType:
        """获取模型类型."""
        ...

    def get_supported_models(self) -> list[str]:
        """获取支持的模型列表."""
        return self._supported_models.copy()

    def get_default_model(self) -> str:
        """获取默认模型."""
        return self._default_model

    def _validate_model(self, model: str) -> None:
        """验证模型是否支持."""
        if model not in self._supported_models:
            raise LLMError(
                LLMErrorCode.MODEL_NOT_FOUND,
                f'Model "{model}" is not supported by {self.provider_type.value}. '
                f'Supported models: {", ".join(self._supported_models)}',
                self.provider_type,
            )

    async def _handle_response_error(self, response: httpx.Response) -> NoReturn:
        """处理 HTTP 响应错误."""
        status = response.status_code
        try:
            error_data = response.json()
            error_message = (
                error_data.get("error", {}).get("message")
                or error_data.get("message")
                or f"HTTP {status}"
            )
        except Exception:
            error_message = response.text or f"HTTP {status}"

        if status == 401:
            raise LLMError(
                LLMErrorCode.INVALID_API_KEY,
                f"Invalid API key for {self.provider_type.value}",
                self.provider_type,
                status,
            )

        if status == 429:
            raise LLMError(
                LLMErrorCode.RATE_LIMIT_EXCEEDED,
                f"Rate limit exceeded for {self.provider_type.value}",
                self.provider_type,
                status,
            )

        raise LLMError(
            LLMErrorCode.INTERNAL_ERROR,
            error_message,
            self.provider_type,
            status,
        )

    async def close(self) -> None:
        """关闭 HTTP 客户端."""
        await self._client.aclose()

    async def __aenter__(self) -> "BaseProvider":
        """异步上下文管理器入口."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器退出."""
        await self.close()


class BaseTextProvider(BaseProvider):
    """文本 Provider 抽象基类."""

    @property
    def model_type(self) -> ModelType:
        return ModelType.TEXT

    @abstractmethod
    async def generate_text(
        self, request: TextGenerationRequest
    ) -> TextGenerationResponse:
        """生成文本响应 (非流式)."""
        ...

    @abstractmethod
    async def generate_text_stream(
        self, request: TextGenerationRequest
    ) -> AsyncGenerator[TextStreamChunk, None]:
        """生成文本响应 (流式)."""
        ...

    def _get_model(self, request: TextGenerationRequest) -> str:
        """获取请求使用的模型."""
        model = request.model or self._default_model
        self._validate_model(model)
        return model


class BaseImageProvider(BaseProvider):
    """图像 Provider 抽象基类."""

    @property
    def model_type(self) -> ModelType:
        return ModelType.IMAGE

    @abstractmethod
    async def create_image_task(
        self, request: ImageGenerationRequest
    ) -> ImageGenerationResponse:
        """创建图像生成任务."""
        ...

    @abstractmethod
    async def get_task_status(self, task_id: str) -> ImageTaskStatusResponse:
        """查询任务状态."""
        ...

    def _get_model(self, request: ImageGenerationRequest) -> str:
        """获取请求使用的模型."""
        model = request.model or self._default_model
        self._validate_model(model)
        return model
