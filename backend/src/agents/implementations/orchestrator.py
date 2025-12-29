"""编排协调 Agent 实现."""

import json
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import BaseTool

from ..core.base import BaseAgent
from ..core.types import (
    AgentConfig,
    AgentInput,
    AgentState,
    AgentType,
    Decision,
)


class OrchestratorAgent(BaseAgent):
    """编排调度 Agent.

    负责协调多个 Agent 的执行，决定执行顺序和任务分配。
    """

    agent_type = AgentType.ORCHESTRATOR
    default_system_prompt = """你是一个智能任务编排 AI 助手。你的职责是：
1. 分析用户的请求，确定需要哪些分析步骤
2. 决定调用哪些专业 Agent
3. 规划执行顺序
4. 汇总各 Agent 的输出

可用的 Agent 类型：
- technical_analyst: 技术分析专家，分析价格走势和技术指标
- fundamental_analyst: 基本面分析专家，分析财务数据和估值
- sentiment_analyst: 情绪分析专家，分析市场情绪和资金流向
- risk_assessor: 风险评估专家，评估交易风险
- signal_generator: 信号生成专家，生成具体交易信号

请根据任务需求，输出你的执行计划（JSON 格式）：
{
    "analysis_type": "综合分析类型",
    "agents_to_call": ["agent1", "agent2"],
    "execution_order": "sequential" | "parallel",
    "priority": ["优先调用的agent"],
    "reasoning": "规划理由"
}
"""

    def __init__(
        self,
        config: AgentConfig,
        llm: BaseChatModel,
        tools: list[BaseTool] | None = None,
        available_agents: dict[str, BaseAgent] | None = None,
    ) -> None:
        super().__init__(config, llm, tools)
        self.available_agents = available_agents or {}

    async def execute(
        self, state: AgentState, agent_input: AgentInput
    ) -> tuple[dict[str, Any], list[Decision]]:
        """执行编排逻辑."""
        # 1. 让 LLM 规划执行策略
        messages = state.get("messages", [])
        response = await self.invoke_llm(messages, use_tools=False)

        # 2. 解析执行计划
        plan = self._parse_plan(response)

        # 3. 按计划执行 Agent
        agent_results = {}
        all_decisions: list[Decision] = []

        agents_to_call = plan.get("agents_to_call", [])
        execution_order = plan.get("execution_order", "sequential")

        if execution_order == "parallel":
            # 并行执行
            import asyncio

            async def run_agent(agent_id: str) -> tuple[str, dict[str, Any], list[Decision]]:
                agent = self.available_agents.get(agent_id)
                if agent:
                    sub_input = AgentInput(
                        task_id=f"{agent_input.task_id}_{agent_id}",
                        task_type=agent_id,
                        content=agent_input.content,
                        context={
                            "parent_task": agent_input.task_id,
                            "orchestrator_plan": plan,
                        },
                    )
                    output = await agent.run(sub_input)
                    return agent_id, output.result, output.decisions
                return agent_id, {}, []

            results = await asyncio.gather(*[run_agent(a) for a in agents_to_call])

            for agent_id, result, decisions in results:
                agent_results[agent_id] = result
                all_decisions.extend(decisions)

        else:
            # 顺序执行
            for agent_id in agents_to_call:
                agent = self.available_agents.get(agent_id)
                if agent:
                    sub_input = AgentInput(
                        task_id=f"{agent_input.task_id}_{agent_id}",
                        task_type=agent_id,
                        content=agent_input.content,
                        context={
                            "parent_task": agent_input.task_id,
                            "orchestrator_plan": plan,
                            "previous_results": agent_results,
                        },
                    )
                    output = await agent.run(sub_input)
                    agent_results[agent_id] = output.result
                    all_decisions.extend(output.decisions)

        # 4. 汇总结果
        summary = await self._summarize_results(agent_results, agent_input)

        final_result = {
            "plan": plan,
            "agent_results": agent_results,
            "summary": summary,
        }

        return final_result, all_decisions

    def _parse_plan(self, response: AIMessage) -> dict[str, Any]:
        """解析执行计划."""
        content = response.content

        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content

            return json.loads(json_str.strip())

        except (json.JSONDecodeError, IndexError):
            # 解析失败，使用默认计划
            return {
                "analysis_type": "default",
                "agents_to_call": ["technical_analyst", "risk_assessor"],
                "execution_order": "sequential",
                "reasoning": "使用默认执行计划",
            }

    async def _summarize_results(
        self, agent_results: dict[str, Any], agent_input: AgentInput
    ) -> dict[str, Any]:
        """汇总所有 Agent 的结果."""
        from langchain_core.messages import HumanMessage, SystemMessage

        summary_prompt = f"""请汇总以下各专家 Agent 的分析结果，给出综合评估：

原始任务：
{json.dumps(agent_input.content, indent=2, ensure_ascii=False)}

各专家分析结果：
{json.dumps(agent_results, indent=2, ensure_ascii=False)}

请输出综合评估（JSON 格式）：
{{
    "overall_recommendation": "buy" | "sell" | "hold" | "observe",
    "confidence": 0.0-1.0,
    "key_points": ["要点1", "要点2"],
    "risks": ["风险1", "风险2"],
    "action_plan": "具体行动建议"
}}
"""

        messages = [
            SystemMessage(content="你是一个综合分析师，负责汇总多个专家的观点。"),
            HumanMessage(content=summary_prompt),
        ]

        response = await self.invoke_llm(messages, use_tools=False)

        try:
            content = response.content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content

            return json.loads(json_str.strip())

        except (json.JSONDecodeError, IndexError):
            return {"raw_summary": response.content}


class SupervisorAgent(BaseAgent):
    """监督 Agent.

    负责监督其他 Agent 的执行，检查质量，处理异常。
    """

    agent_type = AgentType.SUPERVISOR
    default_system_prompt = """你是一个 Agent 监督者。你的职责是：
1. 检查其他 Agent 的输出质量
2. 识别潜在问题和不一致
3. 决定是否需要重新执行或补充分析
4. 确保最终输出符合质量标准

请根据检查结果，输出你的评估（JSON 格式）：
{
    "quality_score": 0.0-1.0,
    "issues_found": ["问题1", "问题2"],
    "recommendations": ["建议1", "建议2"],
    "action": "approve" | "retry" | "supplement",
    "next_agent": "如果需要补充，指定下一个agent"
}
"""

    async def execute(
        self, state: AgentState, agent_input: AgentInput
    ) -> tuple[dict[str, Any], list[Decision]]:
        """执行监督检查."""
        # 获取需要检查的 Agent 输出
        agent_outputs = state.get("agent_outputs", {})

        # 构建检查消息
        from langchain_core.messages import HumanMessage

        check_message = f"""请检查以下 Agent 的输出质量：

任务输入：
{json.dumps(agent_input.content, indent=2, ensure_ascii=False)}

Agent 输出：
{json.dumps(agent_outputs, indent=2, ensure_ascii=False)}

请给出你的评估。
"""

        messages = list(state.get("messages", []))
        messages.append(HumanMessage(content=check_message))

        response = await self.invoke_llm(messages, use_tools=False)

        # 解析评估结果
        try:
            content = response.content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content

            result = json.loads(json_str.strip())

        except (json.JSONDecodeError, IndexError):
            result = {
                "quality_score": 0.5,
                "issues_found": [],
                "recommendations": [],
                "action": "approve",
                "raw_response": response.content,
            }

        return result, []
