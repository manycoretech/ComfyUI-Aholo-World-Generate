"""Boundary / error-path tests (mostly offline)."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from aholo_world_generate.client.world_api import AholoClient
from aholo_world_generate.client.world_poll import poll_world_detail
from aholo_world_generate.util.config import API_KEY_ENV_NAME, resolve_api_key
from aholo_world_generate.util.errors import AholoApiError, AholoTimeoutError

LIVE_TEST_ENV_NAME = "AHOLO_RUN_LIVE_TESTS"


@patch.dict("os.environ", {}, clear=True)
def test_resolve_api_key_missing():
    try:
        resolve_api_key(None)
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "AHOLO_API_KEY" in str(exc)


def test_create_generation_requires_prompt_or_resources():
    client = AholoClient(region="cn", api_key="dummy-key")
    try:
        client.create_generation()
        raise AssertionError("expected AholoApiError")
    except AholoApiError as exc:
        assert exc.status_code == 400


def test_create_generation_rejects_multiple_resources():
    client = AholoClient(region="cn", api_key="dummy-key")
    resources = [
        {"url": "https://a.example/a.png", "type": "image"},
        {"url": "https://a.example/b.png", "type": "image"},
    ]
    try:
        client.create_generation(prompt="x", resources=resources)
        raise AssertionError("expected AholoApiError")
    except AholoApiError as exc:
        assert exc.status_code == 400


def test_poll_timeout():
    client = MagicMock()
    client.get_world.return_value = {"worldId": "w1", "status": "RUNNING", "progress": 0.0}
    try:
        poll_world_detail(client, "w1", timeout_seconds=0.05, poll_interval_seconds=0.01)
        raise AssertionError("expected AholoTimeoutError")
    except AholoTimeoutError as exc:
        assert "轮询超时" in str(exc)


def test_poll_failed_status():
    client = MagicMock()
    client.get_world.return_value = {"worldId": "w1", "status": "FAILED"}
    try:
        poll_world_detail(client, "w1", timeout_seconds=5, poll_interval_seconds=0.01)
        raise AssertionError("expected RuntimeError")
    except RuntimeError as exc:
        assert "FAILED" in str(exc)


def test_poll_succeeded_missing_assets():
    client = MagicMock()
    client.get_world.return_value = {
        "worldId": "w1",
        "status": "SUCCEEDED",
        "assets": {"imagery": {}, "splats": {"urls": {}}},
    }
    try:
        poll_world_detail(client, "w1", timeout_seconds=5, poll_interval_seconds=0.01)
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "pano_url" in str(exc) or "产物字段" in str(exc)


def test_live_invalid_api_key():
    """If the gateway rejects bogus keys, expect 401/403; otherwise skip."""
    if os.environ.get(LIVE_TEST_ENV_NAME) != "1":
        pytest.skip("set AHOLO_RUN_LIVE_TESTS=1 to run live API tests")
    if not os.environ.get(API_KEY_ENV_NAME, "").strip():
        pytest.skip("AHOLO_API_KEY is not configured")
    client = AholoClient(region="cn", api_key="invalid-key-for-boundary-test")
    try:
        client.get_asset_upload_token()
    except AholoApiError as exc:
        assert exc.status_code in (401, 403)
