"""Unit tests for OUS upload helpers (no network)."""

from unittest.mock import patch

from aholo_world_generate.client.ous_upload import (
    OusUploader,
    md5_hex,
    parse_lack_blocks,
)
from aholo_world_generate.util.errors import AholoUploadError


def test_md5_hex():
    assert md5_hex(b"") == "d41d8cd98f00b204e9800998ecf8427e"


def test_parse_lack_blocks_range():
    assert parse_lack_blocks(["1-3", "5"]) == {1, 2, 3, 5}


def test_single_upload_poll_success():
    uploader = OusUploader(
        global_domain="https://ous-cos.example.com",
        ous_token="token",
        block_size=1024,
        poll_interval_seconds=0.01,
        poll_timeout_seconds=1.0,
    )
    payload = b"hello"
    digest = md5_hex(payload)

    responses = [
        {"c": "0", "d": {"taskId": "1"}},
        {"c": "0", "d": {"status": 4}},
        {
            "c": "0",
            "d": {
                "status": 5,
                "url": "https://cdn.example.com/ref.png",
                "md5": digest,
            },
        },
    ]

    with patch.object(uploader, "_request", side_effect=responses) as request:
        url = uploader.upload_bytes(payload, filename="ref.png")

    assert url == "https://cdn.example.com/ref.png"
    assert request.call_count == 3
    first_call = request.call_args_list[0]
    assert first_call.args == ("POST", "/ous/api/v2/single/upload")


def test_poll_terminal_failure():
    uploader = OusUploader(
        global_domain="https://ous-cos.example.com",
        ous_token="token",
        block_size=1024,
        poll_interval_seconds=0.01,
        poll_timeout_seconds=1.0,
    )

    with patch.object(
        uploader,
        "_single_upload",
    ), patch.object(
        uploader,
        "_request",
        return_value={"c": "0", "d": {"status": 6, "errorCode": 5}},
    ):
        try:
            uploader.upload_bytes(b"x", filename="ref.png")
            raise AssertionError("expected AholoUploadError")
        except AholoUploadError as exc:
            assert "垫图上传失败" in str(exc)
