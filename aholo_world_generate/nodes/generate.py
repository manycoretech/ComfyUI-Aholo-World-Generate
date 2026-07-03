from __future__ import annotations

from typing import Any

from comfy_api.v0_0_2 import io

from aholo_world_generate.client.asset_upload import AssetUploader
from aholo_world_generate.client.world_api import AholoClient
from aholo_world_generate.util.config import resolve_api_key
from aholo_world_generate.util.errors import AholoApiError, AholoUploadError


class AholoWorldGenerate(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="aholo.world_generate",
            display_name="Aholo World Generate",
            category="Aholo/World",
            description=(
                "提交 Aholo Spatial Gen 异步任务（POST /world/v1/generations）。"
                "支持纯文案、单张垫图或图文组合；室内效果更稳定，非室内为 Beta。"
            ),
            inputs=[
                io.String.Input(
                    "prompt",
                    multiline=True,
                    default="",
                    tooltip="文本提示词（GenerateWorldRequest.prompt）；与 image 至少填其一",
                ),
                io.Image.Input(
                    "image",
                    optional=True,
                    tooltip="至多 1 张垫图，上传后填入 resources[].url（type=image）",
                ),
                io.String.Input(
                    "name",
                    default="",
                    tooltip="世界展示名称（GenerateWorldRequest.name，可选）",
                ),
                io.String.Input(
                    "cover",
                    default="",
                    tooltip="封面图 URL（GenerateWorldRequest.cover，可选）",
                ),
                io.Combo.Input(
                    "region",
                    options=["cn", "com"],
                    default="cn",
                    tooltip="cn=api.aholo3d.cn；com=api.aholo3d.com（路径带 /global 前缀）",
                ),
                io.String.Input(
                    "api_key",
                    default="",
                    tooltip="覆盖环境变量 AHOLO_API_KEY；留空则读取环境变量",
                ),
            ],
            outputs=[
                io.String.Output(
                    "world_id",
                    tooltip="WorldAsyncOperation.worldId，供 Wait 节点轮询",
                ),
            ],
        )

    @classmethod
    def validate_inputs(
        cls,
        prompt: str,
        image: Any = None,
        name: str = "",
        cover: str = "",
        region: str = "cn",
        api_key: str = "",
    ) -> bool | str:
        prompt_value = (prompt or "").strip()
        has_image = image is not None
        if not prompt_value and not has_image:
            return "prompt 与 image 不能同时为空（GenerateWorldRequest 要求至少其一）"
        try:
            resolve_api_key(api_key or None)
        except ValueError as exc:
            return str(exc)
        return True

    @classmethod
    def execute(
        cls,
        prompt: str,
        image: Any = None,
        name: str = "",
        cover: str = "",
        region: str = "cn",
        api_key: str = "",
    ) -> io.NodeOutput:
        prompt_value = (prompt or "").strip() or None
        name_value = (name or "").strip() or None
        cover_value = (cover or "").strip() or None

        client = AholoClient(region=region, api_key=api_key or None)
        resources: list[dict[str, str]] | None = None

        if image is not None:
            try:
                image_url = AssetUploader(client).upload_image_tensor(image)
            except AholoUploadError as exc:
                raise RuntimeError(str(exc)) from exc
            resources = [{"url": image_url, "type": "image"}]

        try:
            world_id = client.create_generation(
                prompt=prompt_value,
                resources=resources,
                name=name_value,
                cover=cover_value,
            )
        except AholoApiError as exc:
            raise RuntimeError(str(exc)) from exc

        return io.NodeOutput(world_id)
