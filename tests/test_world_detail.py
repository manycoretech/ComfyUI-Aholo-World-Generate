"""Tests for OpenAPI WorldDetail parsing (generateWorldDetail example)."""

from aholo_world_generate.util.config import (
    parse_world_detail,
    validate_success_assets,
)


GENERATE_WORLD_DETAIL = {
    "worldId": "B2c3D4e5F6",
    "name": "现代简约客厅",
    "cover": "https://cdn.example.com/cover/world-gen-001.jpg",
    "scene": "ai_gen",
    "createTime": 1699339916000,
    "updateTime": 1699340120000,
    "status": "SUCCEEDED",
    "progress": 1.0,
    "assets": {
        "imagery": {
            "panoUrl": "https://cdn.example.com/output/world-gen-001-pano.jpg",
        },
        "splats": {
            "urls": {
                "plyPath": "https://cdn.example.com/output/world-gen-001.ply",
                "spzPath": "https://cdn.example.com/output/world-gen-001.spz",
                "lodMetaPath": "https://cdn.example.com/output/world-gen-001-lod-meta.json",
            },
        },
        "semanticsMetadata": {"upAxis": "Z"},
    },
}


def test_parse_generate_world_detail_example():
    parsed = parse_world_detail(GENERATE_WORLD_DETAIL)
    assert parsed["world_id"] == "B2c3D4e5F6"
    assert parsed["scene"] == "ai_gen"
    assert parsed["pano_url"].endswith("-pano.jpg")
    assert parsed["spz_url"].endswith(".spz")
    assert parsed["ply_url"].endswith(".ply")
    assert parsed["lod_meta_url"].endswith("-lod-meta.json")
    assert parsed["up_axis"] == "Z"


def test_validate_success_without_lod_meta():
  detail = parse_world_detail(GENERATE_WORLD_DETAIL)
  detail["lod_meta_url"] = None
  validate_success_assets(detail, "B2c3D4e5F6")



def test_ignores_legacy_assets_top_level_lod_meta():
    legacy = {
        **GENERATE_WORLD_DETAIL,
        "assets": {
            **GENERATE_WORLD_DETAIL["assets"],
            "lodMetaPath": "https://cdn.example.com/legacy-lod-meta.json",
            "splats": {"urls": {}},
        },
    }
    parsed = parse_world_detail(legacy)
    assert parsed["lod_meta_url"] is None

def test_validate_fails_when_pano_missing():
  detail = parse_world_detail(GENERATE_WORLD_DETAIL)
  detail["pano_url"] = None
  try:
      validate_success_assets(detail, "x")
      assert False, "expected ValueError"
  except ValueError as exc:
      assert "pano_url" in str(exc)
