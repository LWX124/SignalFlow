"""LLM Provider 到 LangChain 的适配器."""

from typing import Any, AsyncIterator, List

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    FunctionMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import ConfigDict

from src.infra.llm.base import BaseTextProvider
from src.infra.llm.types import ChatMessage, TextGenerationRequest


class LLMProviderAdapter(BaseChatModel):
    """将 SignalFlow 的 LLM Provider 适配为 LangChain ChatModel.

    这个适配器使得现有的 LLM Provider 可以在 LangChain/LangGraph 生态中使用。
    """

    provider: BaseTextProvider
    """底层的 LLM Provider."""

    model_name: str = ""
    """模型名称."""

    temperature: float = 0.7
    """温度参数."""

    max_tokens: int = 4096
    """最大 token 数."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def _llm_type(self) -> str:
        """返回 LLM 类型标识."""
        return f"signalflow-{self.provider.provider_type.value}"

    @property
    def _identifying_params(self) -> dict[str, Any]:
        """返回识别参数."""
        return {
            "provider_type": self.provider.provider_type.value,
            "model_name": self.model_name or self.provider.get_default_model(),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    def _convert_messages(self, messages: List[BaseMessage]) -> list[ChatMessage]:
        """将 LangChain 消息转换为 Provider 消息格式."""
        result = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                result.append(ChatMessage(role="system", content=str(msg.content)))
            elif isinstance(msg, HumanMessage):
                result.append(ChatMessage(role="user", content=str(msg.content)))
            elif isinstance(msg, AIMessage):
                result.append(ChatMessage(role="assistant", content=str(msg.content)))
            elif isinstance(msg, ToolMessage):
                # ToolMessage 转换为 assistant 上下文中的工具结果
                # 大多数 API 将工具结果作为 user 消息或特殊格式处理
                tool_result = f"[Tool Result: {msg.tool_call_id}]\n{msg.content}"
                result.append(ChatMessage(role="user", content=tool_result))
            elif isinstance(msg, FunctionMessage):
                # FunctionMessage (旧版) 同样处理
                func_result = f"[Function Result: {msg.name}]\n{msg.content}"
                result.append(ChatMessage(role="user", content=func_result))
            else:
                # 其他类型作为 user 消息处理
                result.append(ChatMessage(role="user", content=str(msg.content)))
        return result

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: List[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        """同步生成 (不支持，会抛出异常)."""
        raise NotImplementedError(
            "LLMProviderAdapter 只支持异步调用，请使用 ainvoke() 方法"
        )

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: List[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        """异步生成响应."""
        # 转换消息格式
        provider_messages = self._convert_messages(messages)

        # 构建请求
        request = TextGenerationRequest(
            messages=provider_messages,
            model=self.model_name or None,
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            stream=False,
        )

        # 调用 Provider
        response = await self.provider.generate_text(request)

        # 转换响应
        generations = []
        for choice in response.choices:
            ai_message = AIMessage(content=choice.message.content)
            generations.append(
                ChatGeneration(
                    message=ai_message,
                    generation_info={
                        "finish_reason": choice.finish_reason,
                    },
                )
            )

        # 构建结果
        llm_output = {}
        if response.usage:
            llm_output["token_usage"] = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        llm_output["model"] = response.model

        return ChatResult(generations=generations, llm_output=llm_output)

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: List[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGeneration]:
        """异步流式生成响应."""
        # 转换消息格式
        provider_messages = self._convert_messages(messages)

        # 构建请求
        request = TextGenerationRequest(
            messages=provider_messages,
            model=self.model_name or None,
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            stream=True,
        )

        # 流式调用 Provider
        async for chunk in self.provider.generate_text_stream(request):
            for choice in chunk.choices:
                if choice.delta.content:
                    ai_message = AIMessage(content=choice.delta.content)
                    yield ChatGeneration(
                        message=ai_message,
                        generation_info={
                            "finish_reason": choice.finish_reason,
                        },
                    )


def create_chat_model(
    provider: BaseTextProvider,
    model_name: str = "",
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> LLMProviderAdapter:
    """创建 LangChain ChatModel.

    Args:
        provider: SignalFlow LLM Provider 实例
        model_name: 模型名称，不指定则使用 Provider 默认模型
        temperature: 温度参数
        max_tokens: 最大 token 数

    Returns:
        LangChain ChatModel 实例
    """
    return LLMProviderAdapter(
        provider=provider,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
    )


async def create_chat_model_from_factory(
    model_name: str = "qwen3-max",
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> LLMProviderAdapter:
    """从工厂创建 LangChain ChatModel.

    使用 SignalFlow 的 LLM Provider Factory 创建 ChatModel。

    Args:
        model_name: 模型名称
        temperature: 温度参数
        max_tokens: 最大 token 数

    Returns:
        LangChain ChatModel 实例
    """
    from src.infra.llm.factory import get_default_text_provider

    provider = get_default_text_provider()

    return LLMProviderAdapter(
        provider=provider,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
    )
