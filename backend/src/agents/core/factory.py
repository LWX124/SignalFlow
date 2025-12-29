"""Agent 工厂和注册表."""

from typing import Awaitable, Callable, TypeVar, Union

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from .base import BaseAgent
from .types import AgentConfig, AgentError, AgentErrorCode, AgentType


AgentClass = TypeVar("AgentClass", bound=BaseAgent)

# LLM 工厂类型：支持同步和异步两种
LLMFactory = Callable[[str], Union[BaseChatModel, Awaitable[BaseChatModel]]]
ToolFactory = Callable[[list[str]], list[BaseTool]]


class AgentRegistry:
    """Agent 注册表.

    单例模式，用于管理所有可用的 Agent 类型。
    """

    _instance: "AgentRegistry | None" = None
    _agents: dict[AgentType, type[BaseAgent]]
    _agent_configs: dict[str, AgentConfig]

    def __new__(cls) -> "AgentRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._agents = {}
            cls._instance._agent_configs = {}
        return cls._instance

    def register(
        self,
        agent_type: AgentType,
        agent_class: type[BaseAgent],
    ) -> None:
        """注册 Agent 类.

        Args:
            agent_type: Agent 类型
            agent_class: Agent 类
        """
        self._agents[agent_type] = agent_class

    def register_config(self, agent_id: str, config: AgentConfig) -> None:
        """注册 Agent 配置.

        Args:
            agent_id: Agent ID
            config: Agent 配置
        """
        self._agent_configs[agent_id] = config

    def get_class(self, agent_type: AgentType) -> type[BaseAgent] | None:
        """获取 Agent 类.

        Args:
            agent_type: Agent 类型

        Returns:
            Agent 类，如果未注册则返回 None
        """
        return self._agents.get(agent_type)

    def get_config(self, agent_id: str) -> AgentConfig | None:
        """获取 Agent 配置.

        Args:
            agent_id: Agent ID

        Returns:
            Agent 配置，如果不存在则返回 None
        """
        return self._agent_configs.get(agent_id)

    def get_all_types(self) -> list[AgentType]:
        """获取所有已注册的 Agent 类型."""
        return list(self._agents.keys())

    def get_all_configs(self) -> dict[str, AgentConfig]:
        """获取所有 Agent 配置."""
        return self._agent_configs.copy()

    def unregister(self, agent_type: AgentType) -> None:
        """取消注册 Agent 类."""
        self._agents.pop(agent_type, None)

    def clear(self) -> None:
        """清空所有注册."""
        self._agents.clear()
        self._agent_configs.clear()


# 全局注册表实例
agent_registry = AgentRegistry()


def register_agent(
    agent_type: AgentType,
) -> Callable[[type[AgentClass]], type[AgentClass]]:
    """Agent 注册装饰器.

    使用此装饰器可以自动将 Agent 类注册到全局注册表。

    Example:
        @register_agent(AgentType.STRATEGY_ANALYZER)
        class StrategyAnalyzerAgent(BaseAgent):
            ...
    """

    def decorator(cls: type[AgentClass]) -> type[AgentClass]:
        agent_registry.register(agent_type, cls)
        return cls

    return decorator


class AgentFactory:
    """Agent 工厂.

    用于创建 Agent 实例。
    """

    def __init__(
        self,
        llm_factory: LLMFactory | None = None,
        tool_factory: ToolFactory | None = None,
    ) -> None:
        """初始化 Agent 工厂.

        Args:
            llm_factory: LLM 工厂函数，接收模型名称，返回 LLM 实例 (支持同步/异步)
            tool_factory: 工具工厂函数，接收工具名称列表，返回工具实例列表
        """
        self._llm_factory = llm_factory
        self._tool_factory = tool_factory
        self._instances: dict[str, BaseAgent] = {}

    def create(
        self,
        agent_type: AgentType,
        config: AgentConfig,
        llm: BaseChatModel | None = None,
        tools: list[BaseTool] | None = None,
    ) -> BaseAgent:
        """创建 Agent 实例.

        Args:
            agent_type: Agent 类型
            config: Agent 配置
            llm: LLM 实例（可选，如果不提供则使用工厂创建）
            tools: 工具列表（可选，如果不提供则使用工厂创建）

        Returns:
            Agent 实例

        Raises:
            AgentError: 如果 Agent 类型未注册或创建失败
        """
        # 获取 Agent 类
        agent_class = agent_registry.get_class(agent_type)
        if agent_class is None:
            raise AgentError(
                AgentErrorCode.AGENT_NOT_FOUND,
                f"Agent type '{agent_type.value}' is not registered",
                agent_type=agent_type,
            )

        # 创建 LLM
        if llm is None:
            if self._llm_factory is None:
                raise AgentError(
                    AgentErrorCode.AGENT_INITIALIZATION_FAILED,
                    "No LLM instance or factory provided",
                    agent_type=agent_type,
                )
            llm = self._llm_factory(config.model_name)

        # 创建工具
        if tools is None and config.allowed_tools:
            if self._tool_factory:
                tools = self._tool_factory(config.allowed_tools)
            else:
                tools = []

        # 创建 Agent 实例
        try:
            agent = agent_class(config=config, llm=llm, tools=tools)
            return agent
        except Exception as e:
            raise AgentError(
                AgentErrorCode.AGENT_INITIALIZATION_FAILED,
                f"Failed to create agent: {e}",
                agent_type=agent_type,
            ) from e

    def create_from_id(
        self,
        agent_id: str,
        llm: BaseChatModel | None = None,
        tools: list[BaseTool] | None = None,
    ) -> BaseAgent:
        """根据 Agent ID 创建实例.

        需要事先在注册表中注册配置。

        Args:
            agent_id: Agent ID
            llm: LLM 实例
            tools: 工具列表

        Returns:
            Agent 实例
        """
        config = agent_registry.get_config(agent_id)
        if config is None:
            raise AgentError(
                AgentErrorCode.AGENT_NOT_FOUND,
                f"Agent config for '{agent_id}' not found",
            )

        return self.create(config.agent_type, config, llm, tools)

    def get_or_create(
        self,
        agent_type: AgentType,
        config: AgentConfig,
        llm: BaseChatModel | None = None,
        tools: list[BaseTool] | None = None,
    ) -> BaseAgent:
        """获取或创建 Agent 实例（缓存模式）.

        Args:
            agent_type: Agent 类型
            config: Agent 配置
            llm: LLM 实例
            tools: 工具列表

        Returns:
            Agent 实例
        """
        if config.agent_id in self._instances:
            return self._instances[config.agent_id]

        agent = self.create(agent_type, config, llm, tools)
        self._instances[config.agent_id] = agent
        return agent

    def clear_cache(self) -> None:
        """清空实例缓存."""
        self._instances.clear()


def register_default_agents() -> None:
    """注册默认的 Agent 类型.

    在应用启动时调用此函数以注册所有内置 Agent。
    """
    from ..implementations import (
        FundamentalAnalystAgent,
        OrchestratorAgent,
        RiskAssessorAgent,
        SentimentAnalystAgent,
        SignalGeneratorAgent,
        StrategyAnalyzerAgent,
        SupervisorAgent,
        TechnicalAnalystAgent,
    )

    agent_registry.register(AgentType.STRATEGY_ANALYZER, StrategyAnalyzerAgent)
    agent_registry.register(AgentType.RISK_ASSESSOR, RiskAssessorAgent)
    agent_registry.register(AgentType.SIGNAL_GENERATOR, SignalGeneratorAgent)
    agent_registry.register(AgentType.TECHNICAL_ANALYST, TechnicalAnalystAgent)
    agent_registry.register(AgentType.FUNDAMENTAL_ANALYST, FundamentalAnalystAgent)
    agent_registry.register(AgentType.SENTIMENT_ANALYST, SentimentAnalystAgent)
    agent_registry.register(AgentType.ORCHESTRATOR, OrchestratorAgent)
    agent_registry.register(AgentType.SUPERVISOR, SupervisorAgent)


def create_default_factory(
    default_model: str = "qwen3-max",
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> AgentFactory:
    """创建默认的 Agent 工厂.

    此工厂使用项目现有的 LLM Provider 系统。

    Args:
        default_model: 默认模型名称
        temperature: 温度参数
        max_tokens: 最大 token 数

    Returns:
        配置好的 AgentFactory 实例
    """
    from .llm_adapter import LLMProviderAdapter

    def create_llm(model_name: str) -> BaseChatModel:
        """创建 LLM 实例 (同步版本)."""
        from src.infra.llm.factory import get_default_text_provider

        provider = get_default_text_provider()
        return LLMProviderAdapter(
            provider=provider,
            model_name=model_name or default_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def create_tools(tool_names: list[str]) -> list[BaseTool]:
        """从注册表获取工具."""
        from ..tools import tool_registry

        tools = []
        for name in tool_names:
            tool = tool_registry.get(name)
            if tool:
                tools.append(tool)
        return tools

    # 注册默认 Agent
    register_default_agents()

    # 创建工厂
    return AgentFactory(llm_factory=create_llm, tool_factory=create_tools)
