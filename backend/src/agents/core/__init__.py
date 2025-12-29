"""Agent 核心模块."""

from .base import BaseAgent, PlanAndExecuteAgent, ReActAgent
from .factory import (
    AgentFactory,
    AgentRegistry,
    agent_registry,
    create_default_factory,
    register_agent,
    register_default_agents,
)
from .llm_adapter import (
    LLMProviderAdapter,
    create_chat_model,
    create_chat_model_from_factory,
)
from .types import (
    AgentConfig,
    AgentError,
    AgentErrorCode,
    AgentInput,
    AgentOutput,
    AgentState,
    AgentStatus,
    AgentType,
    ConfidenceLevel,
    Decision,
    DecisionType,
    ToolCall,
)

__all__ = [
    # 基类
    "BaseAgent",
    "ReActAgent",
    "PlanAndExecuteAgent",
    # 类型
    "AgentType",
    "AgentStatus",
    "AgentState",
    "AgentConfig",
    "AgentInput",
    "AgentOutput",
    "Decision",
    "DecisionType",
    "ConfidenceLevel",
    "ToolCall",
    # 错误
    "AgentError",
    "AgentErrorCode",
    # 工厂和注册表
    "AgentFactory",
    "AgentRegistry",
    "agent_registry",
    "register_agent",
    "register_default_agents",
    "create_default_factory",
    # LLM 适配器
    "LLMProviderAdapter",
    "create_chat_model",
    "create_chat_model_from_factory",
]
