#!/usr/bin/env python3
"""Smoke test: GET asset token + upload a tiny PNG via OUS.

Usage (from repo root):
  AHOLO_API_KEY=xxx python scripts/smoke_upload.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import torch

from aholo_world_generate.client.asset_upload import AssetUploader
from aholo_world_generate.client.world_api import AholoClient
from aholo_world_generate.util.config import resolve_api_key
from aholo_world_generate.util.errors import AholoApiError, AholoUploadError


def main() -> int:
    try:
        resolve_api_key(None)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    region = "cn"
    client = AholoClient(region=region)

    print("1/3 GET /asset/v1/token ...")
    try:
        token = client.get_asset_upload_token()
    except AholoApiError as exc:
        print(f"ERROR: token failed: {exc}", file=sys.stderr)
        return 1
    print(f"   globalDomain={token.get('globalDomain')}")
    print(f"   blockSize={token.get('blockSize')}")

    tensor = torch.zeros(1, 64, 64, 3)
    tensor[0, :, :, 1] = 0.5

    print("2/3 tensor -> PNG -> OUS upload ...")
    try:
        url = AssetUploader(client).upload_image_tensor(tensor)
    except (AholoUploadError, ValueError, RuntimeError) as exc:
        print(f"ERROR: upload failed: {exc}", file=sys.stderr)
        return 1

    print("3/3 done")
    print(f"public_url={url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
