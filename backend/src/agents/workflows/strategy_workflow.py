"""策略决策工作流."""

from typing import Any, Literal

from langchain_core.messages import AIMessage, HumanMessage

from ..core.base import BaseAgent
from ..core.types import AgentState, AgentType, Decision, DecisionType
from .engine import MultiAgentWorkflow, WorkflowEngine


class StrategyDecisionWorkflow(MultiAgentWorkflow):
    """策略决策工作流.

    完整的策略决策流程：
    1. 数据收集 -> 2. 多维度分析 -> 3. 风险评估 -> 4. 决策生成
    """

    def __init__(self) -> None:
        super().__init__("strategy_decision")

    def setup_standard_flow(
        self,
        data_collector: BaseAgent,
        analyzers: list[BaseAgent],
        risk_assessor: BaseAgent,
        decision_maker: BaseAgent,
    ) -> "StrategyDecisionWorkflow":
        """设置标准决策流程.

        Args:
            data_collector: 数据收集 Agent
            analyzers: 分析 Agent 列表 (可并行)
            risk_assessor: 风险评估 Agent
            decision_maker: 决策生成 Agent

        Returns:
            self，支持链式调用
        """
        # 创建 Agent 处理函数
        async def collect_data(state: AgentState) -> AgentState:
            from ..core.types import AgentInput

            agent_input = AgentInput(
                task_id=state.get("task_id", ""),
                task_type="data_collection",
                content=state.get("task_input", {}),
            )
            output = await data_collector.run(agent_input)

            new_outputs = dict(state.get("agent_outputs", {}))
            new_outputs["data_collector"] = output.result

            return AgentState(
                **dict(state),
                agent_outputs=new_outputs,
            )

        async def analyze(state: AgentState) -> AgentState:
            """并行执行所有分析器."""
            from ..core.types import AgentInput
            import asyncio

            collected_data = state.get("agent_outputs", {}).get("data_collector", {})

            async def run_analyzer(analyzer: BaseAgent) -> tuple[str, dict[str, Any]]:
                agent_input = AgentInput(
                    task_id=state.get("task_id", ""),
                    task_type="analysis",
                    content=state.get("task_input", {}),
                    context={"collected_data": collected_data},
                )
                output = await analyzer.run(agent_input)
                return analyzer.agent_id, output.result

            # 并行执行
            results = await asyncio.gather(*[run_analyzer(a) for a in analyzers])

            new_outputs = dict(state.get("agent_outputs", {}))
            new_outputs["analysis"] = dict(results)

            return AgentState(
                **dict(state),
                agent_outputs=new_outputs,
            )

        async def assess_risk(state: AgentState) -> AgentState:
            from ..core.types import AgentInput

            agent_input = AgentInput(
                task_id=state.get("task_id", ""),
                task_type="risk_assessment",
                content=state.get("task_input", {}),
                context={
                    "collected_data": state.get("agent_outputs", {}).get("data_collector", {}),
                    "analysis": state.get("agent_outputs", {}).get("analysis", {}),
                },
            )
            output = await risk_assessor.run(agent_input)

            new_outputs = dict(state.get("agent_outputs", {}))
            new_outputs["risk_assessment"] = output.result

            return AgentState(
                **dict(state),
                agent_outputs=new_outputs,
            )

        async def make_decision(state: AgentState) -> AgentState:
            from ..core.types import AgentInput

            agent_input = AgentInput(
                task_id=state.get("task_id", ""),
                task_type="decision_making",
                content=state.get("task_input", {}),
                context=state.get("agent_outputs", {}),
            )
            output = await decision_maker.run(agent_input)

            new_outputs = dict(state.get("agent_outputs", {}))
            new_outputs["decision"] = output.result

            # 提取决策
            decisions = [d.to_dict() for d in output.decisions]

            return AgentState(
                **dict(state),
                agent_outputs=new_outputs,
                decisions=decisions,
                final_decision=decisions[0] if decisions else None,
                should_end=True,
            )

        # 添加节点
        self.add_node("collect_data", collect_data)
        self.add_node("analyze", analyze)
        self.add_node("assess_risk", assess_risk)
        self.add_node("make_decision", make_decision)

        # 设置流程
        self.set_entry_point("collect_data")
        self.add_edge("collect_data", "analyze")
        self.add_edge("analyze", "assess_risk")
        self.add_edge("assess_risk", "make_decision")
        self.set_finish_point("make_decision")

        return self


class TechnicalAnalysisWorkflow(WorkflowEngine):
    """技术分析工作流.

    专注于技术面分析的决策流程。
    """

    def __init__(self) -> None:
        super().__init__("technical_analysis")

    def setup(
        self,
        symbol: str,
        analyze_func: Any,
    ) -> "TechnicalAnalysisWorkflow":
        """设置技术分析流程.

        Args:
            symbol: 股票代码
            analyze_func: 分析函数

        Returns:
            self，支持链式调用
        """

        async def fetch_data(state: AgentState) -> AgentState:
            """获取市场数据."""
            # 这里应该调用真实的数据源
            market_data = {
                "symbol": symbol,
                "prices": [100, 101, 99, 102, 103, 101, 104, 105, 103, 106],
                "volumes": [1000, 1200, 900, 1100, 1300, 1000, 1400, 1500, 1100, 1600],
            }

            return AgentState(
                **dict(state),
                tool_results={"market_data": market_data},
            )

        async def calculate_indicators(state: AgentState) -> AgentState:
            """计算技术指标."""
            market_data = state.get("tool_results", {}).get("market_data", {})
            prices = market_data.get("prices", [])

            # 计算简单指标
            indicators = {}

            if len(prices) >= 5:
                indicators["sma_5"] = sum(prices[-5:]) / 5
            if len(prices) >= 10:
                indicators["sma_10"] = sum(prices[-10:]) / 10

            # 简单的趋势判断
            if len(prices) >= 2:
                indicators["trend"] = "up" if prices[-1] > prices[-2] else "down"

            tool_results = dict(state.get("tool_results", {}))
            tool_results["indicators"] = indicators

            return AgentState(
                **dict(state),
                tool_results=tool_results,
            )

        async def generate_signal(state: AgentState) -> AgentState:
            """生成交易信号."""
            indicators = state.get("tool_results", {}).get("indicators", {})

            # 简单的信号生成逻辑
            signal = "hold"
            confidence = 0.5
            reasoning = []

            sma_5 = indicators.get("sma_5", 0)
            sma_10 = indicators.get("sma_10", 0)

            if sma_5 and sma_10:
                if sma_5 > sma_10:
                    signal = "buy"
                    confidence = 0.7
                    reasoning.append("短期均线上穿长期均线")
                elif sma_5 < sma_10:
                    signal = "sell"
                    confidence = 0.7
                    reasoning.append("短期均线下穿长期均线")

            if indicators.get("trend") == "up":
                confidence += 0.1
                reasoning.append("价格处于上升趋势")
            elif indicators.get("trend") == "down":
                confidence -= 0.1
                reasoning.append("价格处于下降趋势")

            decision = {
                "signal": signal,
                "confidence": min(1.0, max(0.0, confidence)),
                "reasoning": reasoning,
                "indicators": indicators,
            }

            return AgentState(
                **dict(state),
                final_decision=decision,
                should_end=True,
            )

        # 设置流程
        self.add_node("fetch_data", fetch_data)
        self.add_node("calculate_indicators", calculate_indicators)
        self.add_node("generate_signal", generate_signal)

        self.set_entry_point("fetch_data")
        self.add_edge("fetch_data", "calculate_indicators")
        self.add_edge("calculate_indicators", "generate_signal")
        self.set_finish_point("generate_signal")

        return self


class ResearchWorkflow(WorkflowEngine):
    """研究分析工作流.

    用于深度研究分析的工作流，支持迭代式研究。
    """

    def __init__(self, max_iterations: int = 5) -> None:
        super().__init__("research")
        self.max_iterations = max_iterations

    def setup(self, researcher: BaseAgent) -> "ResearchWorkflow":
        """设置研究流程.

        Args:
            researcher: 研究 Agent

        Returns:
            self，支持链式调用
        """

        async def research_step(state: AgentState) -> AgentState:
            """执行研究步骤."""
            from ..core.types import AgentInput

            iteration = state.get("iteration_count", 0)

            agent_input = AgentInput(
                task_id=state.get("task_id", ""),
                task_type="research",
                content=state.get("task_input", {}),
                context={
                    "previous_results": state.get("agent_outputs", {}),
                    "iteration": iteration,
                },
            )

            output = await researcher.run(agent_input)

            new_outputs = dict(state.get("agent_outputs", {}))
            new_outputs[f"research_iteration_{iteration}"] = output.result

            return AgentState(
                **dict(state),
                agent_outputs=new_outputs,
                iteration_count=iteration + 1,
            )

        def should_continue(state: AgentState) -> Literal["continue", "finish"]:
            """判断是否继续研究."""
            iteration = state.get("iteration_count", 0)

            # 检查迭代次数
            if iteration >= self.max_iterations:
                return "finish"

            # 检查是否标记结束
            if state.get("should_end", False):
                return "finish"

            # 可以添加更多结束条件，如达到满意的置信度等
            return "continue"

        async def summarize(state: AgentState) -> AgentState:
            """汇总研究结果."""
            all_results = state.get("agent_outputs", {})

            summary = {
                "total_iterations": state.get("iteration_count", 0),
                "findings": all_results,
            }

            return AgentState(
                **dict(state),
                final_decision=summary,
                should_end=True,
            )

        # 设置流程
        self.add_node("research", research_step)
        self.add_node("summarize", summarize)

        self.set_entry_point("research")
        self.add_conditional_edge(
            "research",
            should_continue,
            {"continue": "research", "finish": "summarize"},
        )
        self.set_finish_point("summarize")

        return self
