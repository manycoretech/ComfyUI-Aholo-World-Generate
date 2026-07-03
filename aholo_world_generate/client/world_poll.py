from __future__ import annotations

import time
from typing import Any, Callable

from aholo_world_generate.client.world_api import AholoClient
from aholo_world_generate.util.config import (
    TERMINAL_STATUSES,
    format_terminal_failure,
    parse_world_detail,
    validate_success_assets,
)
from aholo_world_generate.util.errors import AholoApiError, AholoTimeoutError

ProgressCallback = Callable[[dict[str, Any]], None]


def poll_world_detail(
    client: AholoClient,
    world_id: str,
    *,
    timeout_seconds: float = 600,
    poll_interval_seconds: float = 3.0,
    on_progress: ProgressCallback | None = None,
) -> dict[str, Any]:
    """Poll GET /world/v1/{worldId} until terminal; return parsed detail on SUCCEEDED."""
    world_id_value = (world_id or "").strip()
    if not world_id_value:
        raise ValueError("world_id 不能为空")

    deadline = time.monotonic() + timeout_seconds
    last_status = "PENDING"

    while time.monotonic() < deadline:
        try:
            raw = client.get_world(world_id_value)
        except AholoApiError as exc:
            raise RuntimeError(str(exc)) from exc

        detail = parse_world_detail(raw)
        last_status = str(detail.get("status") or last_status)

        if on_progress is not None:
            on_progress(detail)

        if last_status in TERMINAL_STATUSES:
            if last_status == "SUCCEEDED":
                validate_success_assets(detail, world_id_value)
                return detail
            raise RuntimeError(format_terminal_failure(last_status, detail))

        time.sleep(poll_interval_seconds)

    raise AholoTimeoutError(
        f"轮询超时（{timeout_seconds}s）: world_id={world_id_value}, last_status={last_status}"
    )
