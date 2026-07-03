from __future__ import annotations

from typing_extensions import override

from comfy_api.v0_0_2 import ComfyExtension, io

from aholo_world_generate.nodes.generate import AholoWorldGenerate
from aholo_world_generate.nodes.wait import AholoWorldWait


class AholoExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [AholoWorldGenerate, AholoWorldWait]


async def comfy_entrypoint() -> AholoExtension:
    return AholoExtension()
