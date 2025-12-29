"""Agent 基类定义."""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool

from .types import (
    AgentConfig,
    AgentError,
    AgentErrorCode,
    AgentInput,
    AgentOutput,
    AgentState,
    AgentStatus,
    AgentType,
    Decision,
)

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Agent 抽象基类.

    所有具体的 Agent 实现都需要继承此类。
    """

    # 类级别属性，子类需要覆盖
    agent_type: AgentType
    default_system_prompt: str = ""

    def __init__(
        self,
        config: AgentConfig,
        llm: BaseChatModel,
        tools: list[BaseTool] | None = None,
    ) -> None:
        """初始化 Agent.

        Args:
            config: Agent 配置
            llm: LLM 模型实例
            tools: 可用工具列表
        """
        self.config = config
        self.llm = llm
        self.tools = tools or []
        self._tool_map: dict[str, BaseTool] = {tool.name: tool for tool in self.tools}

        # 如果 LLM 支持工具绑定，则绑定工具
        if self.tools and hasattr(llm, "bind_tools"):
            self.llm_with_tools = llm.bind_tools(self.tools)
        else:
            self.llm_with_tools = llm

    @property
    def agent_id(self) -> str:
        """获取 Agent ID."""
        return self.config.agent_id

    @property
    def name(self) -> str:
        """获取 Agent 名称."""
        return self.config.name

    @property
    def system_prompt(self) -> str:
        """获取系统提示词."""
        return self.config.system_prompt or self.default_system_prompt

    def get_tool(self, name: str) -> BaseTool | None:
        """获取指定名称的工具."""
        return self._tool_map.get(name)

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """运行 Agent.

        这是 Agent 的主入口方法，负责执行完整的任务流程。

        Args:
            agent_input: Agent 输入

        Returns:
            Agent 输出结果
        """
        start_time = time.time()

        try:
            # 1. 验证输入
            self._validate_input(agent_input)

            # 2. 准备初始状态
            state = self._prepare_initial_state(agent_input)

            # 3. 执行主逻辑
            result, decisions = await self.execute(state, agent_input)

            # 4. 构建输出
            execution_time_ms = (time.time() - start_time) * 1000
            return AgentOutput(
                task_id=agent_input.task_id,
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                status=AgentStatus.COMPLETED,
                result=result,
                decisions=decisions,
                execution_time_ms=execution_time_ms,
            )

        except AgentError:
            raise
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return AgentOutput(
                task_id=agent_input.task_id,
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                error=str(e),
                execution_time_ms=execution_time_ms,
            )

    @abstractmethod
    async def execute(
        self, state: AgentState, agent_input: AgentInput
    ) -> tuple[dict[str, Any], list[Decision]]:
        """执行 Agent 核心逻辑.

        子类必须实现此方法。

        Args:
            state: 当前状态
            agent_input: 原始输入

        Returns:
            (结果字典, 决策列表)
        """
        ...

    def _validate_input(self, agent_input: AgentInput) -> None:
        """验证输入.

        子类可以覆盖此方法添加自定义验证。
        """
        if not agent_input.task_id:
            raise AgentError(
                AgentErrorCode.INVALID_INPUT,
                "Task ID is required",
                self.agent_id,
                self.agent_type,
            )

    def _prepare_initial_state(self, agent_input: AgentInput) -> AgentState:
        """准备初始状态."""
        messages: list[BaseMessage] = []

        # 添加系统消息
        if self.system_prompt:
            messages.append(SystemMessage(content=self.system_prompt))

        # 添加用户任务消息
        task_message = self._format_task_message(agent_input)
        messages.append(HumanMessage(content=task_message))

        return AgentState(
            messages=messages,
            task_id=agent_input.task_id,
            task_type=agent_input.task_type,
            task_input=agent_input.content,
            current_agent=self.agent_id,
            agent_outputs={},
            agent_errors={},
            tool_results={},
            decisions=[],
            final_decision=None,
            metadata=agent_input.metadata,
            iteration_count=0,
            max_iterations=self.config.max_iterations,
            should_end=False,
        )

    def _format_task_message(self, agent_input: AgentInput) -> str:
        """格式化任务消息.

        子类可以覆盖此方法自定义任务消息格式。
        """
        return f"""任务类型: {agent_input.task_type}
任务内容: {agent_input.content}
上下文: {agent_input.context}"""

    async def invoke_llm(
        self,
        messages: list[BaseMessage],
        use_tools: bool = True,
    ) -> AIMessage:
        """调用 LLM (带重试机制).

        Args:
            messages: 消息列表
            use_tools: 是否使用工具

        Returns:
            AI 响应消息
        """
        llm = self.llm_with_tools if use_tools and self.tools else self.llm
        max_retries = self.config.max_retries
        last_error: Exception | None = None

        for attempt in range(max_retries):
            try:
                response = await llm.ainvoke(messages)
                if not isinstance(response, AIMessage):
                    response = AIMessage(content=str(response))
                return response
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    # 指数退避重试
                    wait_time = (2 ** attempt) * 0.5  # 0.5s, 1s, 2s...
                    logger.warning(
                        f"LLM invocation failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait_time}s: {e}"
                    )
                    await asyncio.sleep(wait_time)

        raise AgentError(
            AgentErrorCode.LLM_ERROR,
            f"LLM invocation failed after {max_retries} attempts: {last_error}",
            self.agent_id,
            self.agent_type,
        ) from last_error

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """执行工具.

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        tool = self.get_tool(tool_name)
        if not tool:
            raise AgentError(
                AgentErrorCode.TOOL_EXECUTION_FAILED,
                f"Tool '{tool_name}' not found",
                self.agent_id,
                self.agent_type,
            )

        try:
            result = await tool.ainvoke(arguments)
            return result
        except Exception as e:
            raise AgentError(
                AgentErrorCode.TOOL_EXECUTION_FAILED,
                f"Tool '{tool_name}' execution failed: {e}",
                self.agent_id,
                self.agent_type,
                {"tool_name": tool_name, "arguments": arguments},
            ) from e

    def update_state(self, state: AgentState, **updates: Any) -> AgentState:
        """更新状态.

        Args:
            state: 当前状态
            **updates: 要更新的字段

        Returns:
            更新后的状态
        """
        new_state = dict(state)
        new_state.update(updates)
        return AgentState(**new_state)


class ReActAgent(BaseAgent):
    """ReAct 模式 Agent 基类.

    实现 Reasoning + Acting 的循环执行模式。
    """

    async def execute(
        self, state: AgentState, agent_input: AgentInput
    ) -> tuple[dict[str, Any], list[Decision]]:
        """执行 ReAct 循环."""
        current_state = state
        decisions: list[Decision] = []

        while not current_state.get("should_end", False):
            # 检查迭代次数
            iteration = current_state.get("iteration_count", 0)
            if iteration >= current_state.get("max_iterations", 10):
                raise AgentError(
                    AgentErrorCode.MAX_ITERATIONS_EXCEEDED,
                    f"Max iterations ({current_state['max_iterations']}) exceeded",
                    self.agent_id,
                    self.agent_type,
                )

            # 推理步骤
            messages = current_state.get("messages", [])
            response = await self.invoke_llm(messages)

            # 更新消息历史
            new_messages = list(messages) + [response]

            # 检查是否有工具调用
            if hasattr(response, "tool_calls") and response.tool_calls:
                # 执行工具调用
                tool_results = await self._execute_tool_calls(response.tool_calls)

                # 添加工具结果到消息
                for tool_call, result in zip(response.tool_calls, tool_results):
                    from langchain_core.messages import ToolMessage

                    new_messages.append(
                        ToolMessage(
                            content=str(result),
                            tool_call_id=tool_call.get("id", ""),
                        )
                    )

                current_state = self.update_state(
                    current_state,
                    messages=new_messages,
                    iteration_count=iteration + 1,
                    tool_results=dict(
                        current_state.get("tool_results", {}),
                        **{tc["name"]: r for tc, r in zip(response.tool_calls, tool_results)},
                    ),
                )
            else:
                # 没有工具调用，提取结果
                result, extracted_decisions = await self.extract_result(response, current_state)
                decisions.extend(extracted_decisions)

                current_state = self.update_state(
                    current_state,
                    messages=new_messages,
                    should_end=True,
                    iteration_count=iteration + 1,
                )

        # 构建最终结果
        final_result = {
            "response": current_state["messages"][-1].content
            if current_state.get("messages")
            else "",
            "tool_results": current_state.get("tool_results", {}),
            "iteration_count": current_state.get("iteration_count", 0),
        }

        return final_result, decisions

    async def _execute_tool_calls(self, tool_calls: list[dict[str, Any]]) -> list[Any]:
        """执行多个工具调用."""
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("name", "")
            arguments = tool_call.get("args", {})
            try:
                result = await self.execute_tool(tool_name, arguments)
                results.append(result)
            except AgentError as e:
                results.append(f"Error: {e}")
        return results

    async def extract_result(
        self, response: AIMessage, state: AgentState
    ) -> tuple[dict[str, Any], list[Decision]]:
        """从响应中提取结果和决策.

        子类可以覆盖此方法自定义结果提取逻辑。
        """
        return {"content": response.content}, []


class PlanAndExecuteAgent(BaseAgent):
    """Plan-and-Execute 模式 Agent 基类.

    先制定计划，然后按步骤执行。
    """

    plan_prompt: str = """请根据以下任务制定执行计划：

任务: {task}

请输出一个 JSON 格式的计划，包含步骤列表：
{{
    "plan": [
        {{"step": 1, "action": "动作描述", "expected_output": "预期输出"}},
        ...
    ]
}}
"""

    async def execute(
        self, state: AgentState, agent_input: AgentInput
    ) -> tuple[dict[str, Any], list[Decision]]:
        """执行 Plan-and-Execute 流程."""
        # 1. 制定计划
        plan = await self.create_plan(agent_input)

        # 2. 执行计划
        results = []
        decisions: list[Decision] = []

        for step in plan:
            step_result, step_decisions = await self.execute_step(step, state, agent_input)
            results.append(step_result)
            decisions.extend(step_decisions)

        # 3. 汇总结果
        final_result = await self.summarize_results(results, agent_input)

        return final_result, decisions

    async def create_plan(self, agent_input: AgentInput) -> list[dict[str, Any]]:
        """创建执行计划.

        子类可以覆盖此方法自定义计划生成逻辑。
        """
        import json

        plan_message = HumanMessage(
            content=self.plan_prompt.format(task=agent_input.content)
        )
        messages = [SystemMessage(content=self.system_prompt), plan_message]

        response = await self.invoke_llm(messages, use_tools=False)

        # 尝试解析 JSON
        try:
            content = response.content
            # 提取 JSON 部分
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            plan_data = json.loads(content)
            return plan_data.get("plan", [])
        except json.JSONDecodeError:
            # 如果解析失败，返回单步计划
            return [{"step": 1, "action": "Execute task directly", "task": agent_input.content}]

    async def execute_step(
        self,
        step: dict[str, Any],
        state: AgentState,
        agent_input: AgentInput,
    ) -> tuple[dict[str, Any], list[Decision]]:
        """执行单个步骤.

        子类应该覆盖此方法实现具体的步骤执行逻辑。
        """
        step_message = HumanMessage(
            content=f"请执行以下步骤:\n{step}"
        )
        messages = list(state.get("messages", [])) + [step_message]

        response = await self.invoke_llm(messages)

        return {"step": step, "result": response.content}, []

    async def summarize_results(
        self,
        results: list[dict[str, Any]],
        agent_input: AgentInput,
    ) -> dict[str, Any]:
        """汇总执行结果.

        子类可以覆盖此方法自定义结果汇总逻辑。
        """
        return {
            "steps_completed": len(results),
            "results": results,
        }
