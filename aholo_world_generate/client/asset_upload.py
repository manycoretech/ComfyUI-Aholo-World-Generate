from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import torch

from manycore.aholo_sdk_asset import AssetClient
from manycore.aholo_sdk_core import AholoError

from aholo_world_generate.client.world_api import AholoClient
from aholo_world_generate.util.errors import AholoUploadError
from aholo_world_generate.util.image_tensor import first_image_tensor, tensor_to_png_bytes

UPLOAD_FILENAME = "comfyui-reference.png"


class AssetUploader:
    """Upload ComfyUI IMAGE tensors to Aholo OUS and return a public URL."""

    def __init__(self, client: AholoClient) -> None:
        self._asset_client = AssetClient(client.config)

    def upload_image_tensor(self, image: torch.Tensor) -> str:
        tensor = first_image_tensor(image)
        if tensor is None:
            raise ValueError("image tensor is required")

        png_bytes = tensor_to_png_bytes(tensor)

        try:
            result = self._asset_client.upload_bytes(
                png_bytes,
                filename=UPLOAD_FILENAME,
            )
        except AholoError as exc:
            raise AholoUploadError(str(exc)) from exc
        finally:
            self.close()
        url = self._extract_url(result)
        if not url:
            raise AholoUploadError("上传成功但响应缺少 url")
        return url

    def close(self) -> None:
        gateway = getattr(self._asset_client, "gateway", None)
        close = getattr(gateway, "close", None)
        if callable(close):
            close()

    @staticmethod
    def _extract_url(result: Any) -> str:
        if isinstance(result, Mapping):
            return str(result.get("url") or "")
        return str(getattr(result, "url", "") or "")
