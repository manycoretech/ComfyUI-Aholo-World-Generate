"""ComfyUI-Aholo-World-Generate — Aholo Spatial Gen custom nodes."""

async def comfy_entrypoint():
    from aholo_world_generate.extension import comfy_entrypoint as _comfy_entrypoint

    return await _comfy_entrypoint()

__all__ = ["comfy_entrypoint"]
