from __future__ import annotations

import io
from typing import Any

import torch


def tensor_to_png_bytes(image: torch.Tensor) -> bytes:
    """Convert a ComfyUI IMAGE tensor batch item [H, W, 3] to PNG bytes."""
    if image is None:
        raise ValueError("image tensor is required")
    if image.ndim != 3 or image.shape[-1] != 3:
        raise ValueError("image tensor must have shape [H, W, 3]")

    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            "垫图上传需要 Pillow（ComfyUI 环境通常已内置）"
        ) from exc

    import numpy as np

    array = image.detach().clamp(0.0, 1.0).cpu().numpy()
    pixels = (array * 255.0).round().astype(np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(pixels, mode="RGB").save(buffer, format="PNG")
    return buffer.getvalue()


def first_image_tensor(image: Any) -> torch.Tensor | None:
    if image is None:
        return None
    if not isinstance(image, torch.Tensor):
        raise TypeError("image must be a ComfyUI IMAGE tensor")
    if image.ndim != 4 or image.shape[-1] != 3:
        raise ValueError("image tensor must have shape [B, H, W, 3]")
    return image[0]
