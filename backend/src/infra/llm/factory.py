"""LLM Provider 工厂.

使用工厂模式创建和管理 LLM Provider 实例
"""

from functools import lru_cache

from src.core.config import settings

from .base import BaseImageProvider, BaseTextProvider
from .providers import (
    ALIBABA_MODELS,
    DEEPSEEK_MODELS,
    KIE_MODELS,
    AlibabaProvider,
    DeepSeekProvider,
    KieProvider,
)
from .types import LLMError, LLMErrorCode, ProviderType


class LLMProviderFactory:
    """LLM Provider 工厂类."""

    _instance: "LLMProviderFactory | None" = None
    _text_provider_cache: dict[str, BaseTextProvider]
    _image_provider_cache: dict[str, BaseImageProvider]

    def __new__(cls) -> "LLMProviderFactory":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._text_provider_cache = {}
            cls._instance._image_provider_cache = {}
        return cls._instance

    @classmethod
    def get_instance(cls) -> "LLMProviderFactory":
        """获取工厂单例."""
        return cls()

    def _get_api_key(self, provider: ProviderType) -> str:
        """获取 API Key."""
        key_map = {
            ProviderType.ALIBABA: settings.alibaba_api_key,
            ProviderType.DEEPSEEK: settings.deepseek_api_key,
            ProviderType.KIE: settings.kie_api_key,
        }

        api_key = key_map.get(provider)
        if not api_key:
            env_var_map = {
                ProviderType.ALIBABA: "ALIBABA_API_KEY",
                ProviderType.DEEPSEEK: "DEEPSEEK_API_KEY",
                ProviderType.KIE: "KIE_API_KEY",
            }
            raise LLMError(
                LLMErrorCode.INVALID_API_KEY,
                f"API key not configured for {provider.value}. "
                f"Please set {env_var_map[provider]} in your environment variables.",
                provider,
            )

        return api_key

    def create_text_provider(self, provider: ProviderType) -> BaseTextProvider:
        """创建文本 Provider."""
        if provider == ProviderType.KIE:
            raise LLMError(
                LLMErrorCode.INVALID_REQUEST,
                f"Provider {provider.value} does not support text generation",
                provider,
            )

        cache_key = provider.value
        if cache_key in self._text_provider_cache:
            return self._text_provider_cache[cache_key]

        api_key = self._get_api_key(provider)

        provider_map = {
            ProviderType.ALIBABA: AlibabaProvider,
            ProviderType.DEEPSEEK: DeepSeekProvider,
        }

        provider_class = provider_map.get(provider)
        if not provider_class:
            raise LLMError(
                LLMErrorCode.PROVIDER_NOT_FOUND,
                f"Unknown provider: {provider.value}",
                provider,
            )

        instance = provider_class(api_key)
        self._text_provider_cache[cache_key] = instance
        return instance

    def create_image_provider(self, provider: ProviderType) -> BaseImageProvider:
        """创建图像 Provider."""
        if provider != ProviderType.KIE:
            raise LLMError(
                LLMErrorCode.INVALID_REQUEST,
                f"Provider {provider.value} does not support image generation",
                provider,
            )

        cache_key = provider.value
        if cache_key in self._image_provider_cache:
            return self._image_provider_cache[cache_key]

        api_key = self._get_api_key(provider)
        instance = KieProvider(api_key)
        self._image_provider_cache[cache_key] = instance
        return instance

    def get_available_text_providers(self) -> list[ProviderType]:
        """获取可用的文本 Provider 列表."""
        return [ProviderType.ALIBABA, ProviderType.DEEPSEEK]

    def get_available_image_providers(self) -> list[ProviderType]:
        """获取可用的图像 Provider 列表."""
        return [ProviderType.KIE]

    def get_available_providers(self) -> list[ProviderType]:
        """获取所有可用的 Provider 列表."""
        return list(ProviderType)

    def get_provider_models(self, provider: ProviderType) -> list[str]:
        """获取 Provider 支持的模型列表."""
        model_map = {
            ProviderType.ALIBABA: ALIBABA_MODELS,
            ProviderType.DEEPSEEK: DEEPSEEK_MODELS,
            ProviderType.KIE: KIE_MODELS,
        }

        models = model_map.get(provider)
        if models is None:
            raise LLMError(
                LLMErrorCode.PROVIDER_NOT_FOUND,
                f"Unknown provider: {provider.value}",
                provider,
            )

        return list(models)

    def get_provider_type(self, provider: ProviderType) -> str:
        """获取 Provider 类型 (text 或 image)."""
        if provider == ProviderType.KIE:
            return "image"
        return "text"

    def clear_cache(self) -> None:
        """清除缓存的 Provider 实例."""
        self._text_provider_cache.clear()
        self._image_provider_cache.clear()


# ==================== 便捷函数 ====================


@lru_cache
def get_provider_factory() -> LLMProviderFactory:
    """获取工厂实例."""
    return LLMProviderFactory.get_instance()


def get_default_text_provider() -> BaseTextProvider:
    """获取默认的文本 Provider (阿里百炼)."""
    return get_provider_factory().create_text_provider(ProviderType.ALIBABA)


def get_default_image_provider() -> BaseImageProvider:
    """获取默认的图像 Provider (Kie)."""
    return get_provider_factory().create_image_provider(ProviderType.KIE)


def create_text_provider(provider: ProviderType) -> BaseTextProvider:
    """创建指定的文本 Provider."""
    return get_provider_factory().create_text_provider(provider)


def create_image_provider(provider: ProviderType) -> BaseImageProvider:
    """创建指定的图像 Provider."""
    return get_provider_factory().create_image_provider(provider)
