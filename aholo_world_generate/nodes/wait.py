from __future__ import annotations

from comfy_api.v0_0_2 import UI, io

from aholo_world_generate.client.world_api import AholoClient
from aholo_world_generate.client.world_poll import poll_world_detail
from aholo_world_generate.util.config import resolve_api_key
from aholo_world_generate.util.errors import AholoTimeoutError


class AholoWorldWait(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="aholo.world_wait",
            display_name="Aholo World Wait",
            category="Aholo/World",
            description=(
                "轮询 GET /world/v1/{worldId} 直至终态或超时。"
                "SUCCEEDED 时输出 WorldDetail 与 assets（imagery.panoUrl、splats.urls、semanticsMetadata.upAxis）。"
            ),
            inputs=[
                io.String.Input("world_id", tooltip="WorldAsyncOperation.worldId"),
                io.Combo.Input("region", options=["cn", "com"], default="cn"),
                io.String.Input(
                    "api_key",
                    default="",
                    tooltip="覆盖环境变量 AHOLO_API_KEY",
                ),
                io.Int.Input(
                    "timeout_seconds",
                    default=1800,
                    min=60,
                    max=3600,
                    tooltip="轮询超时（秒）",
                ),
                io.Float.Input(
                    "poll_interval_seconds",
                    default=3.0,
                    min=1.0,
                    max=30.0,
                    step=0.5,
                    tooltip="轮询间隔（秒）",
                ),
            ],
            outputs=[
                io.String.Output("world_id", tooltip="WorldDetail.worldId"),
                io.String.Output("name", tooltip="WorldDetail.name"),
                io.String.Output("cover", tooltip="WorldDetail.cover"),
                io.String.Output(
                    "scene",
                    tooltip="WorldDetail.scene（Spatial Gen 成功示例为 ai_gen）",
                ),
                io.String.Output("status", tooltip="WorldOpenApiTaskStatus"),
                io.Float.Output("progress", tooltip="WorldDetail.progress [0.0, 1.0]"),
                io.String.Output("pano_url", tooltip="assets.imagery.panoUrl"),
                io.String.Output("spz_url", tooltip="assets.splats.urls.spzPath"),
                io.String.Output("ply_url", tooltip="assets.splats.urls.plyPath"),
                io.String.Output(
                    "lod_meta_url",
                    tooltip="assets.splats.urls.lodMetaPath（LOD 后处理完成后才有，可为空）",
                ),
                io.String.Output(
                    "up_axis",
                    tooltip="assets.semanticsMetadata.upAxis（Y 或 Z）",
                ),
                io.Int.Output("create_time", tooltip="WorldDetail.createTime，Unix 毫秒"),
                io.Int.Output("update_time", tooltip="WorldDetail.updateTime，Unix 毫秒"),
            ],
            not_idempotent=True,
            is_output_node=True,
        )

    @classmethod
    def validate_inputs(
        cls,
        world_id: str,
        region: str = "cn",
        api_key: str = "",
        timeout_seconds: int = 1800,
        poll_interval_seconds: float = 3.0,
    ) -> bool | str:
        # world_id 若来自上游连线，validate 阶段尚无实际值，勿在此校验非空
        try:
            resolve_api_key(api_key or None)
        except ValueError as exc:
            return str(exc)
        return True

    @classmethod
    def fingerprint_inputs(cls, world_id: str, **kwargs) -> str:
        return (world_id or "").strip()

    @classmethod
    def execute(
        cls,
        world_id: str,
        region: str = "cn",
        api_key: str = "",
        timeout_seconds: int = 1800,
        poll_interval_seconds: float = 3.0,
    ) -> io.NodeOutput:
        world_id_value = (world_id or "").strip()
        if not world_id_value:
            raise RuntimeError("world_id 不能为空")
        client = AholoClient(region=region, api_key=api_key or None)

        try:
            detail = poll_world_detail(
                client,
                world_id_value,
                timeout_seconds=float(timeout_seconds),
                poll_interval_seconds=float(poll_interval_seconds),
            )
        except AholoTimeoutError as exc:
            raise RuntimeError(str(exc)) from exc
        except ValueError as exc:
            raise RuntimeError(str(exc)) from exc
        finally:
            client.close()

        progress = detail.get("progress")
        progress_value = (
            float(progress) if isinstance(progress, (int, float)) else 1.0
        )
        pano_url = str(detail["pano_url"])
        spz_url = str(detail["spz_url"])
        ply_url = str(detail["ply_url"])
        lod_meta_url = str(detail.get("lod_meta_url") or "")
        result_world_id = str(detail.get("world_id") or world_id_value)
        preview_text = "\n".join(
            [
                "status: SUCCEEDED",
                f"world_id: {result_world_id}",
                f"pano_url: {pano_url}",
                f"spz_url: {spz_url}",
                f"ply_url: {ply_url}",
                f"lod_meta_url: {lod_meta_url or '(empty)'}",
            ]
        )
        return io.NodeOutput(
            result_world_id,
            str(detail.get("name") or ""),
            str(detail.get("cover") or ""),
            str(detail.get("scene") or ""),
            "SUCCEEDED",
            progress_value,
            pano_url,
            spz_url,
            ply_url,
            lod_meta_url,
            str(detail["up_axis"]),
            int(detail.get("create_time") or 0),
            int(detail.get("update_time") or 0),
            ui=UI.PreviewText(preview_text),
        )
