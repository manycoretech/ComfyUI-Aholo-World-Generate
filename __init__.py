"""ComfyUI-Aholo-World-Generate — Aholo Spatial Gen custom nodes."""

from __future__ import annotations

import sys
from pathlib import Path

# ComfyUI loads this file via importlib.util.spec_from_file_location and does
# not add the custom-node directory to sys.path, so nested packages like
# aholo_world_generate would otherwise fail with ModuleNotFoundError.
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


async def comfy_entrypoint():
    from aholo_world_generate.extension import comfy_entrypoint as _comfy_entrypoint

    return await _comfy_entrypoint()


__all__ = ["comfy_entrypoint"]
