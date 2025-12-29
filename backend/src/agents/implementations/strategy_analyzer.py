"""策略分析 Agent 实现."""

import json
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import BaseTool

from ..core.base import ReActAgent
from ..core.types import (
    AgentConfig,
    AgentInput,
    AgentState,
    AgentType,
    Decision,
    DecisionType,
)


class StrategyAnalyzerAgent(ReActAgent):
    """策略分析 Agent.

    负责分析市场数据并生成策略建议。
    """

    agent_type = AgentType.STRATEGY_ANALYZER
    default_system_prompt = """你是一个专业的股票策略分析师 AI 助手。你的任务是：
1. 分析给定的市场数据和技术指标
2. 识别潜在的交易机会
3. 评估风险因素
4. 给出明确的交易建议

分析时请遵循以下原则：
- 综合考虑多个技术指标
- 考虑市场整体环境
- 识别关键支撑和阻力位
- 评估风险收益比

请以 JSON 格式输出你的分析结果，包含以下字段：
{
    "decision": "buy" | "sell" | "hold" | "observe",
    "confidence": 0.0-1.0,
    "reasoning": ["原因1", "原因2", ...],
    "risk_factors": ["风险1", "风险2", ...],
    "recommended_action": "具体操作建议"
}
"""

    def __init__(
        self,
        config: AgentConfig,
        llm: BaseChatModel,
        tools: list[BaseTool] | None = None,
    ) -> None:
        super().__init__(config, llm, tools)

    async def extract_result(
        self, response: AIMessage, state: AgentState
    ) -> tuple[dict[str, Any], list[Decision]]:
        """从 LLM 响应中提取分析结果和决策."""
        content = response.content
        decisions: list[Decision] = []

        # 尝试解析 JSON
        try:
            # 提取 JSON 部分
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                # 尝试直接解析
                json_str = content

            result = json.loads(json_str.strip())

            # 创建决策对象
            decision_type_map = {
                "buy": DecisionType.BUY,
                "sell": DecisionType.SELL,
                "hold": DecisionType.HOLD,
                "observe": DecisionType.OBSERVE,
            }

            decision = Decision(
                decision_type=decision_type_map.get(
                    result.get("decision", "hold"), DecisionType.HOLD
                ),
                symbol=state.get("task_input", {}).get("symbol", "UNKNOWN"),
                confidence=result.get("confidence", 0.5),
                reasoning=result.get("reasoning", []),
                risk_factors=result.get("risk_factors", []),
                recommended_action=result.get("recommended_action", ""),
                supporting_data=state.get("tool_results", {}),
            )
            decisions.append(decision)

            return result, decisions

        except (json.JSONDecodeError, IndexError, KeyError):
            # 解析失败，返回原始内容
            return {"raw_response": content}, []

    def _format_task_message(self, agent_input: AgentInput) -> str:
        """格式化任务消息."""
        content = agent_input.content
        context = agent_input.context

        message_parts = [f"请分析以下股票策略数据：\n"]

        if "symbol" in content:
            message_parts.append(f"股票代码: {content['symbol']}")

        if "market_data" in content:
            message_parts.append(f"\n市场数据:\n{json.dumps(content['market_data'], indent=2, ensure_ascii=False)}")

        if "indicators" in content:
            message_parts.append(f"\n技术指标:\n{json.dumps(content['indicators'], indent=2, ensure_ascii=False)}")

        if context:
            message_parts.append(f"\n上下文信息:\n{json.dumps(context, indent=2, ensure_ascii=False)}")

        message_parts.append("\n请给出你的分析结论和交易建议。")

        return "\n".join(message_parts)


class RiskAssessorAgent(ReActAgent):
    """风险评估 Agent.

    负责评估交易风险。
    """

    agent_type = AgentType.RISK_ASSESSOR
    default_system_prompt = """你是一个专业的风险评估 AI 助手。你的任务是：
1. 分析交易提案的潜在风险
2. 评估风险等级
3. 提供风险缓解建议

请以 JSON 格式输出你的评估结果：
{
    "risk_level": "low" | "medium" | "high" | "extreme",
    "risk_score": 0.0-1.0,
    "risks": [
        {"type": "风险类型", "description": "描述", "probability": 0.0-1.0, "impact": "low|medium|high"}
    ],
    "mitigation": ["缓解措施1", "缓解措施2"],
    "recommendation": "是否建议执行"
}
"""

    async def extract_result(
        self, response: AIMessage, state: AgentState
    ) -> tuple[dict[str, Any], list[Decision]]:
        """从响应中提取风险评估结果."""
        content = response.content

        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content

            result = json.loads(json_str.strip())
            return result, []

        except (json.JSONDecodeError, IndexError):
            return {"raw_response": content}, []


class SignalGeneratorAgent(ReActAgent):
    """信号生成 Agent.

    负责生成交易信号。
    """

    agent_type = AgentType.SIGNAL_GENERATOR
    default_system_prompt = """你是一个交易信号生成 AI 助手。基于分析结果，你需要：
1. 生成明确的交易信号
2. 设定入场点位
3. 设定止损和止盈位
4. 估算预期收益

请以 JSON 格式输出信号：
{
    "signal": "buy" | "sell" | "hold",
    "entry_price": 价格,
    "stop_loss": 止损价,
    "take_profit": 止盈价,
    "position_size": "建议仓位比例 (如 10%)",
    "time_frame": "持仓周期建议",
    "confidence": 0.0-1.0,
    "notes": "备注"
}
"""

    async def extract_result(
        self, response: AIMessage, state: AgentState
    ) -> tuple[dict[str, Any], list[Decision]]:
        """从响应中提取信号."""
        content = response.content
        decisions: list[Decision] = []

        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content

            result = json.loads(json_str.strip())

            # 创建决策
            signal = result.get("signal", "hold")
            decision_type_map = {
                "buy": DecisionType.BUY,
                "sell": DecisionType.SELL,
                "hold": DecisionType.HOLD,
            }

            decision = Decision(
                decision_type=decision_type_map.get(signal, DecisionType.HOLD),
                symbol=state.get("task_input", {}).get("symbol", "UNKNOWN"),
                confidence=result.get("confidence", 0.5),
                reasoning=[result.get("notes", "")],
                supporting_data={
                    "entry_price": result.get("entry_price"),
                    "stop_loss": result.get("stop_loss"),
                    "take_profit": result.get("take_profit"),
                    "position_size": result.get("position_size"),
                    "time_frame": result.get("time_frame"),
                },
            )
            decisions.append(decision)

            return result, decisions

        except (json.JSONDecodeError, IndexError):
            return {"raw_response": content}, []


class TechnicalAnalystAgent(ReActAgent):
    """技术分析 Agent.

    专注于技术面分析。
    """

    agent_type = AgentType.TECHNICAL_ANALYST
    default_system_prompt = """你是一个技术分析专家 AI 助手。你需要：
1. 分析价格走势和成交量
2. 识别技术形态
3. 分析关键技术指标 (MA, MACD, RSI, KDJ 等)
4. 识别支撑和阻力位
5. 给出技术面观点

请使用工具获取所需数据，然后以 JSON 格式输出分析结果：
{
    "trend": "up" | "down" | "sideways",
    "patterns": ["形态1", "形态2"],
    "support_levels": [价格1, 价格2],
    "resistance_levels": [价格1, 价格2],
    "indicators": {
        "ma": {"status": "bullish|bearish", "detail": "说明"},
        "macd": {"status": "bullish|bearish", "detail": "说明"},
        "rsi": {"value": 数值, "status": "overbought|oversold|neutral"}
    },
    "outlook": "short_term_bullish | short_term_bearish | neutral",
    "summary": "总结"
}
"""


class FundamentalAnalystAgent(ReActAgent):
    """基本面分析 Agent.

    专注于基本面分析。
    """

    agent_type = AgentType.FUNDAMENTAL_ANALYST
    default_system_prompt = """你是一个基本面分析专家 AI 助手。你需要：
1. 分析公司财务数据
2. 评估估值水平
3. 分析行业地位和竞争优势
4. 评估成长性
5. 给出基本面观点

请以 JSON 格式输出分析结果：
{
    "valuation": {
        "pe_ratio": 数值,
        "pb_ratio": 数值,
        "status": "undervalued | fairly_valued | overvalued"
    },
    "growth": {
        "revenue_growth": "百分比",
        "profit_growth": "百分比",
        "outlook": "accelerating | stable | decelerating"
    },
    "quality": {
        "roe": "百分比",
        "debt_ratio": "百分比",
        "rating": "excellent | good | fair | poor"
    },
    "moat": ["护城河1", "护城河2"],
    "risks": ["风险1", "风险2"],
    "fair_value": "估算的合理价值",
    "summary": "总结"
}
"""


class SentimentAnalystAgent(ReActAgent):
    """情绪分析 Agent.

    专注于市场情绪分析。
    """

    agent_type = AgentType.SENTIMENT_ANALYST
    default_system_prompt = """你是一个市场情绪分析专家 AI 助手。你需要：
1. 分析市场整体情绪
2. 分析资金流向
3. 分析投资者行为
4. 识别极端情绪信号

请以 JSON 格式输出分析结果：
{
    "market_sentiment": "bullish" | "bearish" | "neutral",
    "sentiment_score": -1.0 到 1.0,
    "money_flow": {
        "direction": "inflow" | "outflow" | "balanced",
        "magnitude": "strong" | "moderate" | "weak"
    },
    "crowd_behavior": {
        "retail": "buying | selling | waiting",
        "institutional": "buying | selling | waiting"
    },
    "extreme_signals": ["信号1", "信号2"],
    "contrarian_opportunity": true | false,
    "summary": "总结"
}
"""
