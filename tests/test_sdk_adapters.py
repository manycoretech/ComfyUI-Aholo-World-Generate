"""Tests that the ComfyUI plugin delegates Aholo API work to the SDK."""

from __future__ import annotations

from types import SimpleNamespace

import torch
from manycore.aholo_sdk_core import AholoError

from aholo_world_generate.client import asset_upload, world_api
from aholo_world_generate.client.asset_upload import AssetUploader
from aholo_world_generate.client.world_api import AholoClient
from aholo_world_generate.util.errors import AholoApiError, AholoUploadError


class FakeConfig:
    def __init__(self, *, api_key: str | None = None, region: str = "cn", **kwargs):
        self.api_key = api_key
        self.region = region
        self.kwargs = kwargs


class FakeWorldClient:
    instances: list["FakeWorldClient"] = []

    def __init__(self, config: FakeConfig) -> None:
        self.config = config
        self.generation_calls = []
        self.retrieve_calls = []
        self.generations = SimpleNamespace(create=self._create_generation)
        FakeWorldClient.instances.append(self)

    def _create_generation(self, **kwargs):
        self.generation_calls.append(kwargs)
        return {"worldId": "world-from-sdk"}

    def retrieve(self, world_id: str):
        self.retrieve_calls.append(world_id)
        return {"worldId": world_id, "status": "RUNNING"}


class FakeAssetClient:
    instances: list["FakeAssetClient"] = []

    def __init__(self, config: FakeConfig) -> None:
        self.config = config
        self.upload_calls = []
        self.gateway = SimpleNamespace(close=lambda: None)
        FakeAssetClient.instances.append(self)

    def get_upload_token(self):
        return SdkObject(
            globalDomain="https://ous.example.com",
            ousToken="token",
            blockSize=1024,
        )

    def upload_bytes(self, data: bytes, *, filename: str):
        self.upload_calls.append((data, filename))
        return SimpleNamespace(url="https://cdn.example.com/ref.png")


class SdkObject:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_world_client_delegates_generation_to_sdk(monkeypatch):
    FakeWorldClient.instances.clear()
    monkeypatch.setattr(world_api, "AholoClientConfig", FakeConfig, raising=False)
    monkeypatch.setattr(world_api, "WorldClient", FakeWorldClient, raising=False)

    def fail_direct_http(*args, **kwargs):
        raise AssertionError("AholoClient should delegate world calls to the SDK")

    if hasattr(world_api, "httpx"):
        monkeypatch.setattr(world_api.httpx, "Client", fail_direct_http)

    client = AholoClient(region="com", api_key="dummy-key")
    world_id = client.create_generation(
        prompt=" hello ",
        resources=[{"url": "https://cdn.example.com/ref.png", "type": "image"}],
        name="demo",
    )

    assert world_id == "world-from-sdk"
    sdk_client = FakeWorldClient.instances[0]
    assert sdk_client.config.region == "com"
    assert sdk_client.config.api_key == "dummy-key"
    assert sdk_client.generation_calls == [
        {
            "prompt": "hello",
            "resources": [{"url": "https://cdn.example.com/ref.png", "type": "image"}],
            "name": "demo",
        }
    ]


def test_world_client_accepts_sdk_object_responses(monkeypatch):
    class ObjectWorldClient(FakeWorldClient):
        def _create_generation(self, **kwargs):
            return SdkObject(worldId="object-world")

        def retrieve(self, world_id: str):
            return SdkObject(worldId=world_id, status="RUNNING")

    monkeypatch.setattr(world_api, "AholoClientConfig", FakeConfig, raising=False)
    monkeypatch.setattr(world_api, "WorldClient", ObjectWorldClient, raising=False)

    client = AholoClient(region="cn", api_key="dummy-key")

    assert client.create_generation(prompt="hello") == "object-world"
    assert client.get_world("w1") == {"worldId": "w1", "status": "RUNNING"}


def test_world_client_maps_sdk_errors_without_optional_fields(monkeypatch):
    class ErrorWorldClient(FakeWorldClient):
        def _create_generation(self, **kwargs):
            raise AholoError("sdk failed")

    monkeypatch.setattr(world_api, "AholoClientConfig", FakeConfig, raising=False)
    monkeypatch.setattr(world_api, "WorldClient", ErrorWorldClient, raising=False)

    client = AholoClient(region="cn", api_key="dummy-key")

    try:
        client.create_generation(prompt="hello")
        raise AssertionError("expected AholoApiError")
    except AholoApiError as exc:
        assert "sdk failed" in str(exc)


def test_world_client_get_asset_upload_token_uses_sdk(monkeypatch):
    FakeAssetClient.instances.clear()
    monkeypatch.setattr(world_api, "AholoClientConfig", FakeConfig, raising=False)
    monkeypatch.setattr(world_api, "WorldClient", FakeWorldClient, raising=False)
    monkeypatch.setattr(world_api, "AssetClient", FakeAssetClient, raising=False)

    token = AholoClient(region="cn", api_key="dummy-key").get_asset_upload_token()

    assert token == {
        "globalDomain": "https://ous.example.com",
        "ousToken": "token",
        "blockSize": 1024,
    }
    assert FakeAssetClient.instances[0].config.api_key == "dummy-key"


def test_asset_uploader_delegates_upload_to_sdk(monkeypatch):
    FakeAssetClient.instances.clear()
    monkeypatch.setattr(asset_upload, "AssetClient", FakeAssetClient, raising=False)

    client = SimpleNamespace(config=FakeConfig(api_key="dummy-key", region="cn"))
    tensor = torch.zeros(1, 2, 2, 3)

    url = AssetUploader(client).upload_image_tensor(tensor)

    assert url == "https://cdn.example.com/ref.png"
    sdk_client = FakeAssetClient.instances[0]
    assert sdk_client.config.region == "cn"
    assert sdk_client.upload_calls[0][1] == "comfyui-reference.png"
    assert sdk_client.upload_calls[0][0].startswith(b"\x89PNG")


def test_asset_uploader_rejects_missing_sdk_url(monkeypatch):
    class MissingUrlAssetClient(FakeAssetClient):
        def upload_bytes(self, data: bytes, *, filename: str):
            return SimpleNamespace(url="")

    monkeypatch.setattr(asset_upload, "AssetClient", MissingUrlAssetClient, raising=False)

    client = SimpleNamespace(config=FakeConfig(api_key="dummy-key", region="cn"))
    tensor = torch.zeros(1, 2, 2, 3)

    try:
        AssetUploader(client).upload_image_tensor(tensor)
        raise AssertionError("expected AholoUploadError")
    except AholoUploadError as exc:
        assert "url" in str(exc)
