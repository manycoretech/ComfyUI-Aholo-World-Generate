from __future__ import annotations

from typing import Any

import httpx

from aholo_world_generate.util.config import (
    asset_token_path,
    generations_path,
    resolve_api_key,
    resolve_base_url,
    world_detail_path,
)
from aholo_world_generate.util.errors import AholoApiError


class AholoClient:
    """HTTP client for Aholo World Spatial Gen APIs (OpenAPI: world/openapi.yaml)."""

    def __init__(self, region: str, api_key: str | None = None) -> None:
        self.region = region
        self.api_key = resolve_api_key(api_key)
        self.base_url = resolve_base_url(region)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": self.api_key,
        }

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

        with httpx.Client(base_url=self.base_url, timeout=60.0) as client:
            response = client.post(
                generations_path(self.region),
                json=payload,
                headers=self._headers(),
            )
        return self._parse_world_id(response)

    def get_world(self, world_id: str) -> dict[str, Any]:
        """GET .../world/v1/{worldId} — response: WorldDetail."""
        with httpx.Client(base_url=self.base_url, timeout=60.0) as client:
            response = client.get(
                world_detail_path(self.region, world_id),
                headers=self._headers(),
            )
        return self._parse_json(response)

    def get_asset_upload_token(self) -> dict[str, Any]:
        """GET .../asset/v1/token — response: UploadTokenOuterOpen."""
        with httpx.Client(base_url=self.base_url, timeout=60.0) as client:
            response = client.get(
                asset_token_path(self.region),
                headers=self._headers(),
            )
        return self._parse_json(response)

    def _parse_world_id(self, response: httpx.Response) -> str:
        data = self._parse_json(response)
        world_id = data.get("worldId")
        if not world_id:
            raise AholoApiError(
                "创建任务成功但响应缺少 worldId（WorldAsyncOperation）",
                status_code=response.status_code,
            )
        return str(world_id)

    @staticmethod
    def _extract_api_error(data: dict[str, Any]) -> tuple[str, str | None]:
        message = data.get("message") or "Aholo API 错误"
        localized = data.get("localizedMessage") or {}
        if isinstance(localized, dict) and localized.get("message"):
            message = str(localized["message"])

        biz_code: str | None = None
        details = data.get("details") or {}
        if isinstance(details, dict):
            meta = details.get("metaData") or {}
            if isinstance(meta, dict) and meta.get("bizCode"):
                biz_code = str(meta["bizCode"])
        return str(message), biz_code

    def _parse_json(self, response: httpx.Response) -> dict[str, Any]:
        try:
            data = response.json()
        except ValueError as exc:
            raise AholoApiError(
                f"Aholo API 返回非 JSON 响应 (HTTP {response.status_code})",
                status_code=response.status_code,
            ) from exc

        if response.status_code >= 400:
            if isinstance(data, dict):
                message, biz_code = self._extract_api_error(data)
            else:
                message, biz_code = response.reason_phrase or "HTTP 错误", None
            raise AholoApiError(
                message,
                status_code=response.status_code,
                biz_code=biz_code,
            )
        if not isinstance(data, dict):
            raise AholoApiError("Aholo API 响应格式异常", status_code=response.status_code)
        return data
