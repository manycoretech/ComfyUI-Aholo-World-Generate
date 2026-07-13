from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from manycore.aholo_sdk_asset import AssetClient
from manycore.aholo_sdk_core import AholoClientConfig, AholoError
from manycore.aholo_sdk_world import WorldClient

from aholo_world_generate.util.config import (
    resolve_api_key,
    resolve_region,
)
from aholo_world_generate.util.errors import AholoApiError

SDK_USER_AGENT = "comfyui-aholo-world-generate/1.0.0"


class AholoClient:
    """Small adapter around the official Aholo Python SDK."""

    def __init__(self, region: str, api_key: str | None = None) -> None:
        self.region = resolve_region(region)
        self.api_key = resolve_api_key(api_key)
        self.config = AholoClientConfig(
            api_key=self.api_key,
            region=self.region,
            user_agent=SDK_USER_AGENT,
        )
        self._world_client = WorldClient(self.config)

    def create_generation(
        self,
        *,
        prompt: str | None = None,
        resources: list[dict[str, str]] | None = None,
        name: str | None = None,
        cover: str | None = None,
    ) -> str:
        """POST .../world/v1/generations — body: GenerateWorldRequest."""
        has_prompt = bool((prompt or "").strip())
        has_resources = bool(resources)
        if not has_prompt and not has_resources:
            raise AholoApiError(
                "GenerateWorldRequest 要求 prompt 与 resources 至少满足其一",
                status_code=400,
            )
        if resources and len(resources) > 1:
            raise AholoApiError(
                "GenerateWorldRequest.resources 至多 1 条图片资源",
                status_code=400,
            )

        payload: dict[str, Any] = {}
        if name:
            payload["name"] = name
        if cover:
            payload["cover"] = cover
        if has_prompt:
            payload["prompt"] = prompt.strip()
        if resources:
            payload["resources"] = resources

        try:
            operation = self._world_client.generations.create(
                prompt=payload.get("prompt"),
                resources=payload.get("resources"),
                name=payload.get("name"),
                cover=payload.get("cover"),
            )
        except AholoError as exc:
            raise self._to_api_error(exc) from exc
        return self._parse_world_id(operation)

    def get_world(self, world_id: str) -> dict[str, Any]:
        """GET .../world/v1/{worldId} — response: WorldDetail."""
        try:
            return self._as_dict(self._world_client.retrieve(world_id))
        except AholoError as exc:
            raise self._to_api_error(exc) from exc

    def get_asset_upload_token(self) -> dict[str, Any]:
        """GET .../asset/v1/token — response: UploadTokenOuterOpen."""
        asset_client = AssetClient(self.config)
        try:
            return self._as_dict(asset_client.get_upload_token())
        except AholoError as exc:
            raise self._to_api_error(exc) from exc
        finally:
            self._close_sdk_client(asset_client)

    def close(self) -> None:
        self._close_sdk_client(self._world_client)

    @staticmethod
    def _close_sdk_client(client: Any) -> None:
        gateway = getattr(client, "gateway", None) or getattr(client, "_gateway", None)
        close = getattr(gateway, "close", None)
        if callable(close):
            close()

    def _parse_world_id(self, data: Any) -> str:
        data = self._as_dict(data)
        world_id = data.get("worldId")
        if not world_id:
            raise AholoApiError(
                "创建任务成功但响应缺少 worldId（WorldAsyncOperation）",
            )
        return str(world_id)

    @staticmethod
    def _as_dict(value: Any) -> dict[str, Any]:
        if isinstance(value, Mapping):
            return dict(value)
        if hasattr(value, "model_dump"):
            dumped = value.model_dump()
            if isinstance(dumped, Mapping):
                return dict(dumped)
        if hasattr(value, "to_dict"):
            dumped = value.to_dict()
            if isinstance(dumped, Mapping):
                return dict(dumped)
        if hasattr(value, "__dict__"):
            return {
                key: item
                for key, item in vars(value).items()
                if not key.startswith("_")
            }
        raise AholoApiError("Aholo SDK 响应格式异常")

    @staticmethod
    def _to_api_error(exc: AholoError) -> AholoApiError:
        return AholoApiError(
            str(exc),
            status_code=getattr(exc, "status_code", None),
            biz_code=getattr(exc, "biz_code", None),
        )
