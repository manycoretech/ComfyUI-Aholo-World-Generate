from __future__ import annotations

import hashlib
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import httpx

from aholo_world_generate.util.errors import AholoUploadError

OUS_TOKEN_HEADER = "ous-token-v2"
OUS_STATUS_SUCCESS = 5
OUS_TERMINAL_FAILURE = frozenset({6, 8})

DEFAULT_POLL_INTERVAL_SECONDS = 0.3
DEFAULT_POLL_TIMEOUT_SECONDS = 60.0
DEFAULT_PART_CONCURRENCY = 2
DEFAULT_PART_TIMEOUT_SECONDS = 120.0


def md5_hex(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def parse_lack_blocks(lack_blocks: list[Any]) -> set[int]:
    """Parse OUS lackBlocks into 1-based block numbers (supports ranges like '1-3')."""
    result: set[int] = set()
    for item in lack_blocks:
        text = str(item)
        if "-" in text:
            start, end = text.split("-", 1)
            result.update(range(int(start), int(end) + 1))
        else:
            result.add(int(text))
    return result


def _coerce_status(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def assert_ous_ok(body: dict[str, Any], context: str) -> None:
    if body.get("c") != "0":
        message = body.get("m") or f"{context} failed (c={body.get('c')})"
        raise AholoUploadError(message)


def assert_ous_data(body: dict[str, Any], context: str) -> Any:
    assert_ous_ok(body, context)
    data = body.get("d")
    if data is None:
        raise AholoUploadError(f"{context} succeeded but response data is empty")
    return data


class OusUploader:
    """Upload bytes to Aholo OUS (COS) and return the public URL."""

    def __init__(
        self,
        *,
        global_domain: str,
        ous_token: str,
        block_size: int,
        poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
        poll_timeout_seconds: float = DEFAULT_POLL_TIMEOUT_SECONDS,
    ) -> None:
        if not global_domain:
            raise AholoUploadError("OUS token 响应缺少 globalDomain")
        if not ous_token:
            raise AholoUploadError("OUS token 响应缺少 ousToken")
        if block_size <= 0:
            raise AholoUploadError("OUS token 响应 blockSize 无效")

        self._base_url = global_domain.rstrip("/")
        self._headers = {OUS_TOKEN_HEADER: ous_token}
        self._block_size = block_size
        self._poll_interval_seconds = poll_interval_seconds
        self._poll_timeout_seconds = poll_timeout_seconds

    def upload_bytes(self, data: bytes, *, filename: str = "upload.png") -> str:
        digest = md5_hex(data)
        if len(data) <= self._block_size:
            self._single_upload(data, digest, filename)
        else:
            self._block_upload(data, digest, filename)
        status = self._poll_status()
        url = status.get("url")
        if not url:
            raise AholoUploadError("上传成功但响应缺少 url")
        return str(url)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        timeout: float = 60.0,
    ) -> dict[str, Any]:
        with httpx.Client(
            base_url=self._base_url,
            headers=self._headers,
            timeout=timeout,
        ) as client:
            response = client.request(method, path, params=params, files=files)
        try:
            body = response.json()
        except ValueError as exc:
            raise AholoUploadError(
                f"OUS 返回非 JSON 响应 (HTTP {response.status_code})"
            ) from exc
        if not isinstance(body, dict):
            raise AholoUploadError("OUS 响应格式无效")
        return body

    def _single_upload(self, data: bytes, digest: str, filename: str) -> None:
        body = self._request(
            "POST",
            "/ous/api/v2/single/upload",
            files={
                "md5": (None, digest),
                "file": (filename, data, "application/octet-stream"),
            },
        )
        assert_ous_ok(body, "OUS 单文件上传")

    def _block_upload(self, data: bytes, digest: str, filename: str) -> None:
        parts = [
            data[index : index + self._block_size]
            for index in range(0, len(data), self._block_size)
        ]
        init_body = self._request(
            "POST",
            "/ous/api/v2/block/upload/init",
            params={
                "md5": digest,
                "blocks": len(parts),
                "size": len(data),
                "name": filename,
            },
        )
        init_data = assert_ous_data(init_body, "OUS 分片上传初始化")
        if init_data.get("deduplicated"):
            return

        indexed_parts = list(enumerate(parts))
        lack_blocks = init_data.get("lackBlocks")
        if lack_blocks is not None:
            lack_set = parse_lack_blocks(lack_blocks)
            indexed_parts = [
                (index, chunk) for index, chunk in indexed_parts if (index + 1) in lack_set
            ]
        if not indexed_parts:
            return

        def upload_part(index: int, chunk: bytes) -> None:
            part_body = self._request(
                "POST",
                "/ous/api/v2/block/upload/part",
                files={
                    "block": (None, str(index + 1)),
                    "file": (
                        f"{filename}.part{index + 1}",
                        chunk,
                        "application/octet-stream",
                    ),
                },
                timeout=DEFAULT_PART_TIMEOUT_SECONDS,
            )
            assert_ous_ok(part_body, f"OUS 分片上传 part {index + 1}")

        with ThreadPoolExecutor(max_workers=DEFAULT_PART_CONCURRENCY) as pool:
            futures = [
                pool.submit(upload_part, index, chunk) for index, chunk in indexed_parts
            ]
            for future in as_completed(futures):
                future.result()

    def _poll_status(self) -> dict[str, Any]:
        started = time.monotonic()
        while True:
            body = self._request("GET", "/ous/api/v2/upload/status")
            status_data = assert_ous_data(body, "OUS 上传状态查询")
            status = _coerce_status(status_data.get("status"))
            if status in OUS_TERMINAL_FAILURE:
                error_code = status_data.get("errorCode")
                raise AholoUploadError(
                    f"垫图上传失败: status={status}, errorCode={error_code}"
                )
            if status == OUS_STATUS_SUCCESS and status_data.get("url"):
                return status_data
            if time.monotonic() - started >= self._poll_timeout_seconds:
                raise AholoUploadError(
                    f"垫图上传轮询超时（>{self._poll_timeout_seconds:.0f}s）"
                )
            time.sleep(self._poll_interval_seconds)
