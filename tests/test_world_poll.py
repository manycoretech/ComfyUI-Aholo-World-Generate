"""Tests for world polling logic."""

from unittest.mock import MagicMock

from aholo_world_generate.client.world_poll import poll_world_detail


def test_poll_succeeded():
    client = MagicMock()
    client.get_world.side_effect = [
        {"worldId": "w1", "status": "RUNNING", "progress": 0.5},
        {
            "worldId": "w1",
            "status": "SUCCEEDED",
            "progress": 1.0,
            "assets": {
                "imagery": {"panoUrl": "https://cdn.example.com/pano.jpg"},
                "splats": {
                    "urls": {
                        "plyPath": "https://cdn.example.com/a.ply",
                        "spzPath": "https://cdn.example.com/a.spz",
                    }
                },
                "semanticsMetadata": {"upAxis": "Z"},
            },
        },
    ]
    detail = poll_world_detail(
        client, "w1", timeout_seconds=10, poll_interval_seconds=0.01
    )
    assert detail["pano_url"].endswith("pano.jpg")
    assert detail["up_axis"] == "Z"


def test_poll_failed_terminal():
    client = MagicMock()
    client.get_world.return_value = {"worldId": "w1", "status": "FAILED"}
    try:
        poll_world_detail(client, "w1", timeout_seconds=5, poll_interval_seconds=0.01)
        raise AssertionError("expected RuntimeError")
    except RuntimeError as exc:
        assert "FAILED" in str(exc)
