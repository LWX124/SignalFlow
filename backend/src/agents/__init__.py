"""SignalFlow 多 Agent 架构模块.

基于 LangGraph + LangChain 实现的多 Agent 协作系统，
用于策略分析、风险评估和信号生成等任务。

主要组件:
- core: 核心模块，包含基类、类型定义、工厂等
- tools: 工具模块，包含各类可供 Agent 使用的工具
- workflows: 工作流模块，包含预置的工作流模板
- implementations: 具体的 Agent 实现

使用示例:

    from src.agents import (
        AgentFactory,
        AgentConfig,
        AgentType,
        create_chat_model_from_factory,
        register_default_agents,
        StrategyAnalyzerAgent,
    )

    # 注册默认 Agent
    register_default_agents()

    # 创建 LLM
    llm = await create_chat_model_from_factory()

    # 创建 Agent 配置
    config = AgentConfig(
        agent_id="strategy_analyzer_1",
        agent_type=AgentType.STRATEGY_ANALYZER,
        name="策略分析师",
    )

    # 创建 Agent
    factory = AgentFactory()
    agent = factory.create(AgentType.STRATEGY_ANALYZER, config, llm=llm)

    # 运行 Agent
    from src.agents import AgentInput
    result = await agent.run(AgentInput(
        task_id="task_1",
        task_type="strategy_analysis",
        content={"symbol": "600519", "market_data": {...}},
    ))

工作流使用示例:

    from src.agents.workflows import TechnicalAnalysisWorkflow

    # 创建技术分析工作流
    workflow = TechnicalAnalysisWorkflow()
    workflow.setup(symbol="600519", analyze_func=None)
    workflow.compile()

    # 运行工作流
    result = await workflow.run(initial_state)
"""

# 核心模块
from .core import (
    # 基类
    BaseAgent,
    PlanAndExecuteAgent,
    ReActAgent,
    # 类型
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
    # 工厂
    AgentFactory,
    AgentRegistry,
    agent_registry,
    create_default_factory,
    register_agent,
    register_default_agents,
    # LLM 适配器
    LLMProviderAdapter,
    create_chat_model,
    create_chat_model_from_factory,
)

# 工具模块
from .tools import (
    BaseAgentTool,
    ToolCategory,
    ToolMetadata,
    ToolRegistry,
    register_market_tools,
    register_tool,
    tool_registry,
)

# 工作流模块
from .workflows import (
    MultiAgentWorkflow,
    ResearchWorkflow,
    StrategyDecisionWorkflow,
    TechnicalAnalysisWorkflow,
    WorkflowEngine,
    create_should_continue,
)

# Agent 实现
from .implementations import (
    FundamentalAnalystAgent,
    OrchestratorAgent,
    RiskAssessorAgent,
    SentimentAnalystAgent,
    SignalGeneratorAgent,
    StrategyAnalyzerAgent,
    SupervisorAgent,
    TechnicalAnalystAgent,
)

__all__ = [
    # ===== 核心 =====
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
    # ===== 工具 =====
    "BaseAgentTool",
    "ToolCategory",
    "ToolMetadata",
    "ToolRegistry",
    "tool_registry",
    "register_tool",
    "register_market_tools",
    # ===== 工作流 =====
    "WorkflowEngine",
    "MultiAgentWorkflow",
    "StrategyDecisionWorkflow",
    "TechnicalAnalysisWorkflow",
    "ResearchWorkflow",
    "create_should_continue",
    # ===== Agent 实现 =====
    "StrategyAnalyzerAgent",
    "RiskAssessorAgent",
    "SignalGeneratorAgent",
    "TechnicalAnalystAgent",
    "FundamentalAnalystAgent",
    "SentimentAnalystAgent",
    "OrchestratorAgent",
    "SupervisorAgent",
]

__version__ = "0.1.0"
