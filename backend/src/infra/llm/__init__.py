"""LLM Provider 模块入口.

使用示例:

```python
from src.infra.llm import (
    get_default_text_provider,
    create_text_provider,
    create_image_provider,
    get_provider_factory,
    ProviderType,
    ChatMessage,
    TextGenerationRequest,
)

# 使用默认文本 Provider (阿里百炼)
text_provider = get_default_text_provider()
response = await text_provider.generate_text(
    TextGenerationRequest(
        messages=[
            ChatMessage(role="system", content="You are a helpful assistant."),
            ChatMessage(role="user", content="Hello!"),
        ]
    )
)

# 使用指定模型
response2 = await text_provider.generate_text(
    TextGenerationRequest(
        model="qwen3-max",
        messages=[...],
    )
)

# 使用 DeepSeek
deepseek_provider = create_text_provider(ProviderType.DEEPSEEK)

# 使用 Kie 生成图像
from src.infra.llm import ImageGenerationRequest

image_provider = create_image_provider(ProviderType.KIE)
task = await image_provider.create_image_task(
    ImageGenerationRequest(
        prompt="A beautiful landscape",
        aspect_ratio="16:9",
    )
)

# 流式响应
async for chunk in text_provider.generate_text_stream(
    TextGenerationRequest(messages=[...])
):
    print(chunk.choices[0].delta.content)
```
"""

# 类型导出
from .types import (
    AspectRatio,
    ChatMessage,
    ImageGenerationRequest,
    ImageGenerationResponse,
    ImageOutputFormat,
    ImageResolution,
    ImageResult,
    ImageStatus,
    ImageTaskStatusResponse,
    LLMError,
    LLMErrorCode,
    MessageRole,
    ModelType,
    ProviderConfig,
    ProviderType,
    StreamChoice,
    StreamDelta,
    TextGenerationChoice,
    TextGenerationRequest,
    TextGenerationResponse,
    TextStreamChunk,
    TextUsage,
)

# 基类导出
from .base import BaseImageProvider, BaseProvider, BaseTextProvider

# Provider 导出
from .providers import (
    ALIBABA_BASE_URL,
    ALIBABA_DEFAULT_MODEL,
    ALIBABA_MODELS,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_DEFAULT_MODEL,
    DEEPSEEK_MODELS,
    KIE_BASE_URL,
    KIE_DEFAULT_MODEL,
    KIE_MODELS,
    AlibabaProvider,
    DeepSeekProvider,
    KieProvider,
    create_alibaba_provider,
    create_deepseek_provider,
    create_kie_provider,
)

# 工厂导出
from .factory import (
    LLMProviderFactory,
    create_image_provider,
    create_text_provider,
    get_default_image_provider,
    get_default_text_provider,
    get_provider_factory,
)

__all__ = [
    # Types
    "ProviderType",
    "ModelType",
    "MessageRole",
    "ChatMessage",
    "TextGenerationRequest",
    "TextGenerationChoice",
    "TextUsage",
    "TextGenerationResponse",
    "StreamDelta",
    "StreamChoice",
    "TextStreamChunk",
    "AspectRatio",
    "ImageResolution",
    "ImageOutputFormat",
    "ImageGenerationRequest",
    "ImageResult",
    "ImageStatus",
    "ImageGenerationResponse",
    "ImageTaskStatusResponse",
    "ProviderConfig",
    "LLMErrorCode",
    "LLMError",
    # Base classes
    "BaseProvider",
    "BaseTextProvider",
    "BaseImageProvider",
    # Providers
    "AlibabaProvider",
    "create_alibaba_provider",
    "ALIBABA_MODELS",
    "ALIBABA_DEFAULT_MODEL",
    "ALIBABA_BASE_URL",
    "DeepSeekProvider",
    "create_deepseek_provider",
    "DEEPSEEK_MODELS",
    "DEEPSEEK_DEFAULT_MODEL",
    "DEEPSEEK_BASE_URL",
    "KieProvider",
    "create_kie_provider",
    "KIE_MODELS",
    "KIE_DEFAULT_MODEL",
    "KIE_BASE_URL",
    # Factory
    "LLMProviderFactory",
    "get_default_text_provider",
    "get_default_image_provider",
    "create_text_provider",
    "create_image_provider",
    "get_provider_factory",
]
