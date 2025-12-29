"""Agent 工具基类和注册系统."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, TypeVar

from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel


class ToolCategory(str, Enum):
    """工具分类."""

    DATA_FETCH = "data_fetch"  # 数据获取
    DATA_ANALYSIS = "data_analysis"  # 数据分析
    CALCULATION = "calculation"  # 计算
    MARKET_DATA = "market_data"  # 市场数据
    NEWS = "news"  # 新闻资讯
    TECHNICAL = "technical"  # 技术分析
    FUNDAMENTAL = "fundamental"  # 基本面
    RISK = "risk"  # 风险评估
    NOTIFICATION = "notification"  # 通知
    UTILITY = "utility"  # 工具类


@dataclass
class ToolMetadata:
    """工具元数据."""

    name: str
    description: str
    category: ToolCategory
    version: str = "1.0.0"
    author: str = ""
    tags: list[str] = field(default_factory=list)
    requires_api_key: bool = False
    rate_limit: int | None = None  # 每分钟调用次数限制


class ToolRegistry:
    """工具注册表.

    单例模式，用于管理所有可用的工具。
    """

    _instance: "ToolRegistry | None" = None
    _tools: dict[str, BaseTool]
    _metadata: dict[str, ToolMetadata]

    def __new__(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
            cls._instance._metadata = {}
        return cls._instance

    def register(
        self,
        tool: BaseTool,
        metadata: ToolMetadata | None = None,
    ) -> None:
        """注册工具.

        Args:
            tool: 工具实例
            metadata: 工具元数据
        """
        self._tools[tool.name] = tool
        if metadata:
            self._metadata[tool.name] = metadata

    def unregister(self, name: str) -> None:
        """取消注册工具."""
        self._tools.pop(name, None)
        self._metadata.pop(name, None)

    def get(self, name: str) -> BaseTool | None:
        """获取工具."""
        return self._tools.get(name)

    def get_metadata(self, name: str) -> ToolMetadata | None:
        """获取工具元数据."""
        return self._metadata.get(name)

    def get_all(self) -> dict[str, BaseTool]:
        """获取所有工具."""
        return self._tools.copy()

    def get_by_category(self, category: ToolCategory) -> list[BaseTool]:
        """按分类获取工具."""
        return [
            tool
            for name, tool in self._tools.items()
            if self._metadata.get(name, ToolMetadata(name, "", category)).category == category
        ]

    def get_names(self) -> list[str]:
        """获取所有工具名称."""
        return list(self._tools.keys())

    def clear(self) -> None:
        """清空所有工具."""
        self._tools.clear()
        self._metadata.clear()


# 全局工具注册表实例
tool_registry = ToolRegistry()


T = TypeVar("T", bound=Callable[..., Any])


def register_tool(
    name: str,
    description: str,
    category: ToolCategory = ToolCategory.UTILITY,
    args_schema: type[BaseModel] | None = None,
    **metadata_kwargs: Any,
) -> Callable[[T], T]:
    """工具注册装饰器.

    使用此装饰器可以将函数注册为 Agent 工具。

    Example:
        @register_tool(
            name="get_stock_price",
            description="获取股票实时价格",
            category=ToolCategory.MARKET_DATA,
        )
        async def get_stock_price(symbol: str) -> dict:
            ...
    """

    def decorator(func: T) -> T:
        is_async = _is_async(func)

        # 创建 StructuredTool
        # 注意: 对于异步函数，只设置 coroutine，不设置 func
        if is_async:
            tool = StructuredTool.from_function(
                coroutine=func,
                name=name,
                description=description,
                args_schema=args_schema,
            )
        else:
            tool = StructuredTool.from_function(
                func=func,
                name=name,
                description=description,
                args_schema=args_schema,
            )

        # 创建元数据
        metadata = ToolMetadata(
            name=name,
            description=description,
            category=category,
            **metadata_kwargs,
        )

        # 注册到全局注册表
        tool_registry.register(tool, metadata)

        return func

    return decorator


def _is_async(func: Callable[..., Any]) -> bool:
    """检查函数是否是异步函数."""
    import asyncio
    import inspect

    return asyncio.iscoroutinefunction(func) or inspect.iscoroutinefunction(func)


class BaseAgentTool(BaseTool, ABC):
    """Agent 工具抽象基类.

    继承此类以创建自定义工具。
    """

    category: ToolCategory = ToolCategory.UTILITY
    version: str = "1.0.0"

    @abstractmethod
    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """同步执行工具."""
        ...

    async def _arun(self, *args: Any, **kwargs: Any) -> Any:
        """异步执行工具.

        默认调用同步方法，子类可以覆盖以提供真正的异步实现。
        """
        return self._run(*args, **kwargs)

    def get_metadata(self) -> ToolMetadata:
        """获取工具元数据."""
        return ToolMetadata(
            name=self.name,
            description=self.description,
            category=self.category,
            version=self.version,
        )

    def register(self) -> None:
        """将工具注册到全局注册表."""
        tool_registry.register(self, self.get_metadata())
