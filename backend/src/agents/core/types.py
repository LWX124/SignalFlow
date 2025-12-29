"""Agent 核心类型定义."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, TypedDict

from langchain_core.messages import BaseMessage


# ==================== Agent 类型枚举 ====================


class AgentType(str, Enum):
    """Agent 类型."""

    # 策略决策类
    STRATEGY_ANALYZER = "strategy_analyzer"  # 策略分析 Agent
    RISK_ASSESSOR = "risk_assessor"  # 风险评估 Agent
    SIGNAL_GENERATOR = "signal_generator"  # 信号生成 Agent

    # 数据处理类
    DATA_COLLECTOR = "data_collector"  # 数据采集 Agent
    DATA_ANALYZER = "data_analyzer"  # 数据分析 Agent

    # 协调类
    ORCHESTRATOR = "orchestrator"  # 编排调度 Agent
    SUPERVISOR = "supervisor"  # 监督 Agent

    # 专业领域类
    TECHNICAL_ANALYST = "technical_analyst"  # 技术分析 Agent
    FUNDAMENTAL_ANALYST = "fundamental_analyst"  # 基本面分析 Agent
    SENTIMENT_ANALYST = "sentiment_analyst"  # 情绪分析 Agent
    NEWS_ANALYST = "news_analyst"  # 新闻分析 Agent


class AgentStatus(str, Enum):
    """Agent 运行状态."""

    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"  # 等待其他 Agent 或外部资源
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class DecisionType(str, Enum):
    """决策类型."""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    OBSERVE = "observe"  # 观察，不做操作
    ALERT = "alert"  # 发出警告


class ConfidenceLevel(str, Enum):
    """置信度级别."""

    VERY_HIGH = "very_high"  # >= 0.9
    HIGH = "high"  # >= 0.75
    MEDIUM = "medium"  # >= 0.5
    LOW = "low"  # >= 0.25
    VERY_LOW = "very_low"  # < 0.25


# ==================== 状态类型 (用于 LangGraph) ====================


class AgentState(TypedDict, total=False):
    """Agent 执行状态 (LangGraph State)."""

    # 消息历史
    messages: list[BaseMessage]

    # 任务信息
    task_id: str
    task_type: str
    task_input: dict[str, Any]

    # Agent 执行信息
    current_agent: str
    agent_outputs: dict[str, Any]  # {agent_name: output}
    agent_errors: dict[str, str]  # {agent_name: error_message}

    # 工具调用结果
    tool_results: dict[str, Any]

    # 决策相关
    decisions: list[dict[str, Any]]
    final_decision: dict[str, Any] | None

    # 元数据
    metadata: dict[str, Any]
    iteration_count: int
    max_iterations: int

    # 终止标志
    should_end: bool


# ==================== 数据类 ====================


@dataclass
class AgentConfig:
    """Agent 配置."""

    agent_id: str
    agent_type: AgentType
    name: str
    description: str = ""

    # LLM 配置
    model_name: str = "qwen3-max"
    temperature: float = 0.7
    max_tokens: int = 4096

    # 执行配置
    max_retries: int = 3
    timeout_seconds: int = 120
    max_iterations: int = 10

    # 工具配置
    allowed_tools: list[str] = field(default_factory=list)

    # 其他配置
    system_prompt: str = ""
    extra_config: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentInput:
    """Agent 输入."""

    task_id: str
    task_type: str
    content: dict[str, Any]
    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentOutput:
    """Agent 输出."""

    task_id: str
    agent_id: str
    agent_type: AgentType
    status: AgentStatus
    result: dict[str, Any] = field(default_factory=dict)
    decisions: list["Decision"] = field(default_factory=list)
    error: str | None = None
    execution_time_ms: float = 0
    token_usage: dict[str, int] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典."""
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "agent_type": self.agent_type.value,
            "status": self.status.value,
            "result": self.result,
            "decisions": [d.to_dict() for d in self.decisions],
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "token_usage": self.token_usage,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Decision:
    """决策结果."""

    decision_type: DecisionType
    symbol: str
    confidence: float
    reasoning: list[str]
    risk_factors: list[str] = field(default_factory=list)
    supporting_data: dict[str, Any] = field(default_factory=dict)
    recommended_action: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def confidence_level(self) -> ConfidenceLevel:
        """获取置信度级别."""
        if self.confidence >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif self.confidence >= 0.75:
            return ConfidenceLevel.HIGH
        elif self.confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif self.confidence >= 0.25:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def to_dict(self) -> dict[str, Any]:
        """转换为字典."""
        return {
            "decision_type": self.decision_type.value,
            "symbol": self.symbol,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level.value,
            "reasoning": self.reasoning,
            "risk_factors": self.risk_factors,
            "supporting_data": self.supporting_data,
            "recommended_action": self.recommended_action,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ToolCall:
    """工具调用记录."""

    tool_name: str
    arguments: dict[str, Any]
    result: Any = None
    error: str | None = None
    execution_time_ms: float = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ==================== 错误类型 ====================


class AgentErrorCode(str, Enum):
    """Agent 错误代码."""

    AGENT_NOT_FOUND = "AGENT_NOT_FOUND"
    AGENT_INITIALIZATION_FAILED = "AGENT_INITIALIZATION_FAILED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    TOOL_EXECUTION_FAILED = "TOOL_EXECUTION_FAILED"
    LLM_ERROR = "LLM_ERROR"
    TIMEOUT = "TIMEOUT"
    MAX_ITERATIONS_EXCEEDED = "MAX_ITERATIONS_EXCEEDED"
    INVALID_INPUT = "INVALID_INPUT"
    INVALID_OUTPUT = "INVALID_OUTPUT"
    WORKFLOW_ERROR = "WORKFLOW_ERROR"


class AgentError(Exception):
    """Agent 错误."""

    def __init__(
        self,
        code: AgentErrorCode,
        message: str,
        agent_id: str | None = None,
        agent_type: AgentType | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.details = details or {}
