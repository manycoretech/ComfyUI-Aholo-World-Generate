#!/usr/bin/env python3
"""End-to-end smoke: POST generations + poll until SUCCEEDED.

Usage:
  python scripts/smoke_generate.py
  python scripts/smoke_generate.py --with-image
  python scripts/smoke_generate.py --prompt "现代简约客厅，木地板，暖光"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import torch

from aholo_world_generate.client.asset_upload import AssetUploader
from aholo_world_generate.client.world_api import AholoClient
from aholo_world_generate.client.world_poll import poll_world_detail
from aholo_world_generate.util.config import resolve_api_key
from aholo_world_generate.util.errors import AholoApiError, AholoTimeoutError, AholoUploadError


DEFAULT_PROMPT = "现代简约客厅，落地窗，暖色灯光，木地板"


def _progress(detail: dict) -> None:
    status = detail.get("status")
    progress = detail.get("progress")
    if progress is not None:
        print(f"  status={status} progress={progress:.2f}", flush=True)
    else:
        print(f"  status={status}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Aholo Spatial Gen E2E smoke test")
    parser.add_argument("--region", default="cn", choices=["cn", "com"])
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--with-image", action="store_true", help="upload a 64x64垫图")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--poll-interval", type=float, default=5.0)
    args = parser.parse_args()

    try:
        resolve_api_key(None)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    client = AholoClient(region=args.region)
    resources = None

    if args.with_image:
        print("0/3 upload reference image ...")
        tensor = torch.zeros(1, 64, 64, 3)
        tensor[0, :, :, 2] = 0.6
        try:
            image_url = AssetUploader(client).upload_image_tensor(tensor)
        except AholoUploadError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        resources = [{"url": image_url, "type": "image"}]
        print(f"   image_url={image_url[:72]}...")

    print("1/3 POST /world/v1/generations ...")
    try:
        world_id = client.create_generation(prompt=args.prompt, resources=resources)
    except AholoApiError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"   world_id={world_id}")

    print("2/3 poll world detail ...")
    try:
        detail = poll_world_detail(
            client,
            world_id,
            timeout_seconds=float(args.timeout),
            poll_interval_seconds=args.poll_interval,
            on_progress=_progress,
        )
    except (AholoTimeoutError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("3/3 SUCCEEDED")
    print(f"scene={detail.get('scene')}")
    print(f"pano_url={detail.get('pano_url')}")
    print(f"spz_url={detail.get('spz_url')}")
    print(f"ply_url={detail.get('ply_url')}")
    print(f"up_axis={detail.get('up_axis')}")
    lod = detail.get("lod_meta_url")
    if lod:
        print(f"lod_meta_url={lod}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
