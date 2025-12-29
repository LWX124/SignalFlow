"""LangGraph 工作流引擎."""

from typing import Any, Callable, Literal

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from ..core.types import AgentState


class WorkflowEngine:
    """工作流引擎.

    基于 LangGraph 实现的工作流编排引擎。
    """

    def __init__(self, name: str = "workflow") -> None:
        """初始化工作流引擎.

        Args:
            name: 工作流名称
        """
        self.name = name
        self._graph = StateGraph(AgentState)
        self._compiled: CompiledStateGraph | None = None
        self._nodes: dict[str, Callable] = {}
        self._edges: list[tuple[str, str]] = []
        self._conditional_edges: list[tuple[str, Callable, dict[str, str]]] = []

    def add_node(
        self,
        name: str,
        handler: Callable[[AgentState], AgentState],
    ) -> "WorkflowEngine":
        """添加节点.

        Args:
            name: 节点名称
            handler: 节点处理函数

        Returns:
            self，支持链式调用
        """
        self._nodes[name] = handler
        self._graph.add_node(name, handler)
        return self

    def add_edge(self, from_node: str, to_node: str) -> "WorkflowEngine":
        """添加边.

        Args:
            from_node: 起始节点
            to_node: 目标节点

        Returns:
            self，支持链式调用
        """
        self._edges.append((from_node, to_node))
        self._graph.add_edge(from_node, to_node)
        return self

    def add_conditional_edge(
        self,
        from_node: str,
        condition: Callable[[AgentState], str],
        path_map: dict[str, str],
    ) -> "WorkflowEngine":
        """添加条件边.

        Args:
            from_node: 起始节点
            condition: 条件函数，返回下一个节点名称
            path_map: 条件值到节点的映射

        Returns:
            self，支持链式调用
        """
        self._conditional_edges.append((from_node, condition, path_map))
        self._graph.add_conditional_edges(from_node, condition, path_map)
        return self

    def set_entry_point(self, node: str) -> "WorkflowEngine":
        """设置入口点.

        Args:
            node: 入口节点名称

        Returns:
            self，支持链式调用
        """
        self._graph.add_edge(START, node)
        return self

    def set_finish_point(self, node: str) -> "WorkflowEngine":
        """设置结束点.

        Args:
            node: 结束节点名称

        Returns:
            self，支持链式调用
        """
        self._graph.add_edge(node, END)
        return self

    def compile(self) -> CompiledStateGraph:
        """编译工作流.

        Returns:
            编译后的状态图
        """
        self._compiled = self._graph.compile()
        return self._compiled

    async def run(
        self,
        initial_state: AgentState,
        config: dict[str, Any] | None = None,
    ) -> AgentState:
        """运行工作流.

        Args:
            initial_state: 初始状态
            config: 运行配置

        Returns:
            最终状态
        """
        if self._compiled is None:
            self.compile()

        result = await self._compiled.ainvoke(initial_state, config=config)  # type: ignore
        return AgentState(**result)

    def stream(
        self,
        initial_state: AgentState,
        config: dict[str, Any] | None = None,
    ):
        """流式运行工作流.

        Args:
            initial_state: 初始状态
            config: 运行配置

        Yields:
            中间状态
        """
        if self._compiled is None:
            self.compile()

        return self._compiled.stream(initial_state, config=config)  # type: ignore

    def get_graph(self) -> StateGraph:
        """获取底层状态图."""
        return self._graph

    def visualize(self) -> str:
        """可视化工作流 (返回 Mermaid 格式).

        Returns:
            Mermaid 格式的图描述
        """
        if self._compiled is None:
            self.compile()

        try:
            return self._compiled.get_graph().draw_mermaid()  # type: ignore
        except Exception:
            # 手动生成简单的 Mermaid 图
            lines = ["graph TD"]
            for from_node, to_node in self._edges:
                lines.append(f"    {from_node} --> {to_node}")
            for from_node, _, path_map in self._conditional_edges:
                for condition, to_node in path_map.items():
                    lines.append(f"    {from_node} -->|{condition}| {to_node}")
            return "\n".join(lines)


class MultiAgentWorkflow(WorkflowEngine):
    """多 Agent 协作工作流.

    预置的多 Agent 协作模式。
    """

    def __init__(self, name: str = "multi_agent_workflow") -> None:
        super().__init__(name)
        self._agent_handlers: dict[str, Callable] = {}

    def add_agent(
        self,
        agent_id: str,
        handler: Callable[[AgentState], AgentState],
    ) -> "MultiAgentWorkflow":
        """添加 Agent.

        Args:
            agent_id: Agent ID
            handler: Agent 处理函数

        Returns:
            self，支持链式调用
        """
        self._agent_handlers[agent_id] = handler
        return self.add_node(agent_id, handler)

    def setup_sequential(self, agent_order: list[str]) -> "MultiAgentWorkflow":
        """设置顺序执行模式.

        Args:
            agent_order: Agent 执行顺序

        Returns:
            self，支持链式调用
        """
        if not agent_order:
            return self

        # 设置入口点
        self.set_entry_point(agent_order[0])

        # 设置顺序边
        for i in range(len(agent_order) - 1):
            self.add_edge(agent_order[i], agent_order[i + 1])

        # 设置结束点
        self.set_finish_point(agent_order[-1])

        return self

    def setup_parallel_then_aggregate(
        self,
        parallel_agents: list[str],
        aggregator: str,
    ) -> "MultiAgentWorkflow":
        """设置并行执行后聚合模式.

        注意: LangGraph 不原生支持并行分支，这里使用单个节点内的 asyncio.gather
        来实现真正的并行执行。

        Args:
            parallel_agents: 并行执行的 Agent 列表
            aggregator: 聚合 Agent

        Returns:
            self，支持链式调用
        """
        import asyncio

        # 获取 agent handlers 的引用
        agent_handlers = self._agent_handlers

        async def parallel_executor(state: AgentState) -> AgentState:
            """在单个节点内并行执行多个 Agent."""
            tasks = []
            for agent_id in parallel_agents:
                handler = agent_handlers.get(agent_id)
                if handler:
                    # 如果 handler 是异步的，直接调用；否则包装
                    if asyncio.iscoroutinefunction(handler):
                        tasks.append(handler(state))
                    else:
                        tasks.append(asyncio.to_thread(handler, state))

            if not tasks:
                return state

            # 并行执行所有 Agent
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 合并结果到 agent_outputs
            new_outputs = dict(state.get("agent_outputs", {}))
            new_errors = dict(state.get("agent_errors", {}))

            for agent_id, result in zip(parallel_agents, results):
                if isinstance(result, Exception):
                    # 记录错误
                    new_errors[agent_id] = str(result)
                elif isinstance(result, dict):
                    # 如果返回的是 AgentState，提取 agent_outputs
                    if "agent_outputs" in result:
                        new_outputs.update(result.get("agent_outputs", {}))
                    else:
                        new_outputs[agent_id] = result

            return AgentState(
                **dict(state),
                agent_outputs=new_outputs,
                agent_errors=new_errors,
            )

        # 添加并行执行节点
        self.add_node("parallel_executor", parallel_executor)
        self.set_entry_point("parallel_executor")

        # 从并行执行节点到聚合器
        self.add_edge("parallel_executor", aggregator)
        self.set_finish_point(aggregator)

        return self

    def setup_supervisor(
        self,
        supervisor: str,
        workers: list[str],
        route_condition: Callable[[AgentState], str],
    ) -> "MultiAgentWorkflow":
        """设置监督者模式.

        Args:
            supervisor: 监督者 Agent
            workers: 工作者 Agent 列表
            route_condition: 路由条件函数

        Returns:
            self，支持链式调用
        """
        self.set_entry_point(supervisor)

        # 添加条件路由
        path_map = {worker: worker for worker in workers}
        path_map["FINISH"] = END

        self.add_conditional_edge(supervisor, route_condition, path_map)

        # 工作者完成后返回监督者
        for worker in workers:
            self.add_edge(worker, supervisor)

        return self


def create_should_continue(
    max_iterations: int = 10,
    end_conditions: list[Callable[[AgentState], bool]] | None = None,
) -> Callable[[AgentState], Literal["continue", "end"]]:
    """创建是否继续执行的判断函数.

    Args:
        max_iterations: 最大迭代次数
        end_conditions: 额外的结束条件

    Returns:
        判断函数
    """
    end_conditions = end_conditions or []

    def should_continue(state: AgentState) -> Literal["continue", "end"]:
        # 检查是否应该结束
        if state.get("should_end", False):
            return "end"

        # 检查迭代次数
        if state.get("iteration_count", 0) >= max_iterations:
            return "end"

        # 检查额外结束条件
        for condition in end_conditions:
            if condition(state):
                return "end"

        return "continue"

    return should_continue
