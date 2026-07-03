"""Optional live upload test (skipped without API key)."""

from __future__ import annotations

import os

import pytest
import torch

from aholo_world_generate.client.asset_upload import AssetUploader
from aholo_world_generate.client.world_api import AholoClient
from aholo_world_generate.util.config import API_KEY_ENV_NAME

LIVE_TEST_ENV_NAME = "AHOLO_RUN_LIVE_TESTS"


def _has_api_key() -> bool:
    return bool(os.environ.get(API_KEY_ENV_NAME, "").strip())


def test_live_upload_smoke():
    if os.environ.get(LIVE_TEST_ENV_NAME) != "1":
        pytest.skip("set AHOLO_RUN_LIVE_TESTS=1 to run live upload tests")
    if not _has_api_key():
        pytest.skip("AHOLO_API_KEY is not configured")

    client = AholoClient(region="cn")
    tensor = torch.zeros(1, 32, 32, 3)
    url = AssetUploader(client).upload_image_tensor(tensor)
    assert url.startswith("http")
