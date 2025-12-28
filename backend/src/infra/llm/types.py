"""LLM Provider 类型定义."""

from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncGenerator, Literal, Protocol


# ==================== 基础类型 ====================


class ProviderType(str, Enum):
    """供应商类型."""

    ALIBABA = "alibaba"
    DEEPSEEK = "deepseek"
    KIE = "kie"


class ModelType(str, Enum):
    """模型类型."""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


MessageRole = Literal["system", "user", "assistant"]


@dataclass
class ChatMessage:
    """聊天消息."""

    role: MessageRole
    content: str


# ==================== 文本模型类型 ====================


@dataclass
class TextGenerationRequest:
    """文本生成请求参数."""

    messages: list[ChatMessage]
    model: str | None = None
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None


@dataclass
class TextGenerationChoice:
    """文本生成选择."""

    index: int
    message: ChatMessage
    finish_reason: str


@dataclass
class TextUsage:
    """文本生成用量统计."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class TextGenerationResponse:
    """文本生成响应 (非流式)."""

    id: str
    model: str
    choices: list[TextGenerationChoice]
    usage: TextUsage | None = None


@dataclass
class StreamDelta:
    """流式响应增量."""

    role: MessageRole | None = None
    content: str | None = None


@dataclass
class StreamChoice:
    """流式响应选择."""

    index: int
    delta: StreamDelta
    finish_reason: str | None = None


@dataclass
class TextStreamChunk:
    """流式文本响应块."""

    id: str
    model: str
    choices: list[StreamChoice]


# ==================== 图像模型类型 ====================

AspectRatio = Literal["1:1", "16:9", "9:16", "4:3", "3:4", "21:9"]
ImageResolution = Literal["1K", "2K", "4K"]
ImageOutputFormat = Literal["png", "jpg", "webp"]


@dataclass
class ImageGenerationRequest:
    """图像生成请求参数."""

    prompt: str
    model: str | None = None
    aspect_ratio: AspectRatio = "1:1"
    resolution: ImageResolution = "1K"
    output_format: ImageOutputFormat = "png"
    callback_url: str | None = None


@dataclass
class ImageResult:
    """图像结果."""

    url: str
    width: int
    height: int


ImageStatus = Literal["pending", "processing", "completed", "failed"]


@dataclass
class ImageGenerationResponse:
    """图像生成响应."""

    task_id: str
    status: ImageStatus
    result: ImageResult | None = None
    error: str | None = None


@dataclass
class ImageTaskStatusResponse:
    """图像任务状态查询响应."""

    task_id: str
    status: ImageStatus
    progress: float | None = None
    result: ImageResult | None = None
    error: str | None = None


# ==================== 供应商配置类型 ====================


@dataclass
class ProviderConfig:
    """供应商配置."""

    api_key: str
    base_url: str
    default_model: str
    supported_models: list[str] = field(default_factory=list)
    model_type: ModelType = ModelType.TEXT


# ==================== Provider 接口 ====================


class TextProvider(Protocol):
    """文本生成 Provider 接口."""

    @property
    def provider_type(self) -> ProviderType:
        """获取供应商类型."""
        ...

    @property
    def model_type(self) -> ModelType:
        """获取模型类型."""
        ...

    async def generate_text(
        self, request: TextGenerationRequest
    ) -> TextGenerationResponse:
        """生成文本响应 (非流式)."""
        ...

    async def generate_text_stream(
        self, request: TextGenerationRequest
    ) -> AsyncGenerator[TextStreamChunk, None]:
        """生成文本响应 (流式)."""
        ...

    def get_supported_models(self) -> list[str]:
        """获取支持的模型列表."""
        ...

    def get_default_model(self) -> str:
        """获取默认模型."""
        ...


class ImageProvider(Protocol):
    """图像生成 Provider 接口."""

    @property
    def provider_type(self) -> ProviderType:
        """获取供应商类型."""
        ...

    @property
    def model_type(self) -> ModelType:
        """获取模型类型."""
        ...

    async def create_image_task(
        self, request: ImageGenerationRequest
    ) -> ImageGenerationResponse:
        """创建图像生成任务."""
        ...

    async def get_task_status(self, task_id: str) -> ImageTaskStatusResponse:
        """查询任务状态."""
        ...

    def get_supported_models(self) -> list[str]:
        """获取支持的模型列表."""
        ...

    def get_default_model(self) -> str:
        """获取默认模型."""
        ...


# ==================== 错误类型 ====================


class LLMErrorCode(str, Enum):
    """LLM 错误代码."""

    INVALID_API_KEY = "INVALID_API_KEY"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
    PROVIDER_NOT_FOUND = "PROVIDER_NOT_FOUND"
    NETWORK_ERROR = "NETWORK_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class LLMError(Exception):
    """LLM 错误."""

    def __init__(
        self,
        code: LLMErrorCode,
        message: str,
        provider: ProviderType | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.provider = provider
        self.status_code = status_code
