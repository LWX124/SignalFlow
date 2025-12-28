"""Kie Provider (图像生成).

支持模型: nano-banana-pro
"""

import asyncio
from collections.abc import Callable

from ..base import BaseImageProvider
from ..types import (
    ImageGenerationRequest,
    ImageGenerationResponse,
    ImageResult,
    ImageTaskStatusResponse,
    LLMError,
    LLMErrorCode,
    ProviderType,
)

# Kie 支持的模型
KIE_MODELS: list[str] = ["nano-banana-pro"]

# Kie 默认模型
KIE_DEFAULT_MODEL = "nano-banana-pro"

# Kie API 基础 URL
KIE_BASE_URL = "https://api.kie.ai/api/v1"


class KieProvider(BaseImageProvider):
    """Kie Provider 实现 (图像生成)."""

    def __init__(self, api_key: str) -> None:
        super().__init__(
            api_key=api_key,
            base_url=KIE_BASE_URL,
            default_model=KIE_DEFAULT_MODEL,
            supported_models=KIE_MODELS.copy(),
        )

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.KIE

    async def create_image_task(
        self, request: ImageGenerationRequest
    ) -> ImageGenerationResponse:
        """创建图像生成任务."""
        model = self._get_model(request)

        payload = {
            "model": model,
            "input": {
                "prompt": request.prompt,
                "aspect_ratio": request.aspect_ratio,
                "resolution": request.resolution,
                "output_format": request.output_format,
            },
        }

        if request.callback_url:
            payload["callBackUrl"] = request.callback_url

        response = await self._client.post(
            f"{self._base_url}/jobs/createTask",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

        if response.status_code != 200:
            await self._handle_response_error(response)

        data = response.json()

        return ImageGenerationResponse(
            task_id=data.get("taskId") or data.get("task_id") or data.get("id"),
            status="pending",
            result=None,
            error=None,
        )

    async def get_task_status(self, task_id: str) -> ImageTaskStatusResponse:
        """查询任务状态."""
        response = await self._client.get(
            f"{self._base_url}/jobs/getTaskStatus",
            params={"taskId": task_id},
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )

        if response.status_code != 200:
            await self._handle_response_error(response)

        data = response.json()

        # 映射 Kie API 状态到标准状态
        status_map = {
            "pending": "pending",
            "queued": "pending",
            "processing": "processing",
            "running": "processing",
            "completed": "completed",
            "success": "completed",
            "failed": "failed",
            "error": "failed",
        }

        raw_status = (data.get("status") or "pending").lower()
        status = status_map.get(raw_status, "pending")

        result = None
        if data.get("result"):
            result = ImageResult(
                url=data["result"].get("url") or data["result"].get("image_url") or "",
                width=data["result"].get("width") or 0,
                height=data["result"].get("height") or 0,
            )

        return ImageTaskStatusResponse(
            task_id=task_id,
            status=status,  # type: ignore
            progress=data.get("progress"),
            result=result,
            error=data.get("error") or data.get("message"),
        )

    async def wait_for_completion(
        self,
        task_id: str,
        max_attempts: int = 60,
        interval_seconds: float = 2.0,
        on_progress: Callable[[ImageTaskStatusResponse], None] | None = None,
    ) -> ImageTaskStatusResponse:
        """轮询等待任务完成.

        Args:
            task_id: 任务 ID
            max_attempts: 最大尝试次数
            interval_seconds: 轮询间隔 (秒)
            on_progress: 进度回调函数

        Returns:
            任务状态响应

        Raises:
            LLMError: 任务失败或超时
        """
        for _ in range(max_attempts):
            status = await self.get_task_status(task_id)

            if on_progress:
                on_progress(status)

            if status.status == "completed":
                return status

            if status.status == "failed":
                raise LLMError(
                    LLMErrorCode.INTERNAL_ERROR,
                    f"Image generation failed: {status.error or 'Unknown error'}",
                    self.provider_type,
                )

            await asyncio.sleep(interval_seconds)

        raise LLMError(
            LLMErrorCode.INTERNAL_ERROR,
            f"Image generation timed out after {max_attempts * interval_seconds} seconds",
            self.provider_type,
        )


def create_kie_provider(api_key: str) -> KieProvider:
    """创建 Kie Provider 实例."""
    return KieProvider(api_key)
