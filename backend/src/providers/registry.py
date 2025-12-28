"""Provider registry."""

from typing import Dict
from src.providers.base import BaseProvider, DataCapability


class ProviderRegistry:
    """Data provider registration center."""

    _providers: Dict[str, BaseProvider] = {}
    _capability_map: Dict[DataCapability, list[str]] = {}

    @classmethod
    def register(cls, provider: BaseProvider) -> None:
        cls._providers[provider.provider_id] = provider
        for cap in provider.capabilities:
            if cap not in cls._capability_map:
                cls._capability_map[cap] = []
            cls._capability_map[cap].append(provider.provider_id)

    @classmethod
    def get(cls, provider_id: str) -> BaseProvider | None:
        return cls._providers.get(provider_id)

    @classmethod
    def get_for_capability(cls, capability: DataCapability) -> list[BaseProvider]:
        provider_ids = cls._capability_map.get(capability, [])
        return [cls._providers[pid] for pid in provider_ids if pid in cls._providers]

    @classmethod
    def list_all(cls) -> list[BaseProvider]:
        return list(cls._providers.values())

    @classmethod
    def unregister(cls, provider_id: str) -> bool:
        if provider_id in cls._providers:
            provider = cls._providers[provider_id]
            for cap in provider.capabilities:
                if cap in cls._capability_map and provider_id in cls._capability_map[cap]:
                    cls._capability_map[cap].remove(provider_id)
            del cls._providers[provider_id]
            return True
        return False
