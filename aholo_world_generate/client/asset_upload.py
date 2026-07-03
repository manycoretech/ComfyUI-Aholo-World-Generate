from __future__ import annotations

import torch

from aholo_world_generate.client.ous_upload import OusUploader
from aholo_world_generate.client.world_api import AholoClient
from aholo_world_generate.util.errors import AholoApiError, AholoUploadError
from aholo_world_generate.util.image_tensor import first_image_tensor, tensor_to_png_bytes

UPLOAD_FILENAME = "comfyui-reference.png"


class AssetUploader:
    """Upload ComfyUI IMAGE tensors to Aholo OUS and return a public URL."""

    def __init__(self, client: AholoClient) -> None:
        self._client = client

    def upload_image_tensor(self, image: torch.Tensor) -> str:
        tensor = first_image_tensor(image)
        if tensor is None:
            raise ValueError("image tensor is required")

        png_bytes = tensor_to_png_bytes(tensor)

        try:
            token = self._client.get_asset_upload_token()
        except AholoApiError as exc:
            raise AholoUploadError(str(exc)) from exc

        try:
            ous_token = token["ousToken"]
            global_domain = token["globalDomain"]
            block_size = int(token["blockSize"])
        except (KeyError, TypeError, ValueError) as exc:
            raise AholoUploadError("获取 OUS 上传凭证响应字段不完整") from exc

        uploader = OusUploader(
            global_domain=str(global_domain),
            ous_token=str(ous_token),
            block_size=block_size,
        )
        return uploader.upload_bytes(png_bytes, filename=UPLOAD_FILENAME)
