from __future__ import annotations

import os
from typing import Any

# OpenAPI: WorldOpenApiTaskStatus
IN_PROGRESS_STATUSES = frozenset({"PENDING", "PREPROCESSING", "RUNNING"})
TERMINAL_STATUSES = frozenset(
    {"SUCCEEDED", "FAILED", "CANCELED", "TIMEOUT", "REJECTED"}
)
SUCCESS_STATUSES = frozenset({"SUCCEEDED"})
FAILURE_STATUSES = TERMINAL_STATUSES - SUCCESS_STATUSES

# OpenAPI: WorldOpenApiUpAxis
VALID_UP_AXES = frozenset({"Y", "Z"})

VALID_REGIONS = frozenset({"cn", "com"})

# Spatial Gen 成功时必须有的 assets 字段（lodMetaPath 见 SplatFileUrls：LOD 后处理完成后才有，可为空）
REQUIRED_SUCCESS_ASSET_FIELDS = (
    "pano_url",
    "ply_url",
    "spz_url",
    "up_axis",
)


API_KEY_ENV_NAME = "AHOLO_API_KEY"


def resolve_api_key(api_key: str | None) -> str:
    key = (api_key or "").strip()
    if not key:
        key = os.environ.get(API_KEY_ENV_NAME, "").strip()
    if not key:
        raise ValueError(
            "未配置 Aholo API Key：请在节点中填写 api_key，"
            f"或设置环境变量 {API_KEY_ENV_NAME}"
        )
    return key


def resolve_region(region: str | None) -> str:
    value = (region or os.environ.get("AHOLO_REGION", "cn")).strip().lower()
    if value not in VALID_REGIONS:
        raise ValueError(f"不支持的 region: {value!r}，仅支持 cn / com")
    return value


def parse_world_detail(detail: dict[str, Any]) -> dict[str, Any]:
    """Map OpenAPI WorldDetail (+ WorldAssetBundle) to flat node fields."""
    assets = detail.get("assets") or {}
    imagery = assets.get("imagery") or {}
    splats = assets.get("splats") or {}
    urls = splats.get("urls") or {}
    semantics = assets.get("semanticsMetadata") or {}

    return {
        "world_id": detail.get("worldId"),
        "name": detail.get("name"),
        "cover": detail.get("cover"),
        "scene": detail.get("scene"),
        "create_time": detail.get("createTime"),
        "update_time": detail.get("updateTime"),
        "status": detail.get("status"),
        "progress": detail.get("progress"),
        "pano_url": imagery.get("panoUrl"),
        "spz_url": urls.get("spzPath"),
        "ply_url": urls.get("plyPath"),
        "lod_meta_url": urls.get("lodMetaPath"),
        "up_axis": semantics.get("upAxis"),
    }


def validate_success_assets(detail: dict[str, Any], world_id: str) -> None:
    missing = [field for field in REQUIRED_SUCCESS_ASSET_FIELDS if not detail.get(field)]
    if missing:
        raise ValueError(
            f"任务 SUCCEEDED 但响应缺少产物字段: {', '.join(missing)}（world_id={world_id}）"
        )
    up_axis = str(detail.get("up_axis"))
    if up_axis not in VALID_UP_AXES:
        raise ValueError(
            f"任务 SUCCEEDED 但 upAxis 无效: {up_axis!r}（world_id={world_id}）"
        )


def format_terminal_failure(status: str, detail: dict[str, Any]) -> str:
    """WorldDetail 无 message 字段；终态失败仅输出 status 与已知上下文。"""
    world_id = detail.get("world_id") or "?"
    return f"Aholo 生成失败: status={status}（world_id={world_id}）"


# Backwards-compatible alias
extract_world_assets = parse_world_detail
