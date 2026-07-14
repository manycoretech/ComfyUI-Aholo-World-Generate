# ComfyUI-Aholo-World-Generate

English | [Simplified Chinese](README.zh-CN.md)

ComfyUI V3 custom nodes for Aholo **Spatial Gen**, which generates 3D spaces from text prompts with an optional reference image.

## Installation

### ComfyUI-Manager (recommended)

1. Open ComfyUI and launch **ComfyUI-Manager**.
2. Search for **Aholo World Generate** (publisher: `manycoretech`).
3. Install, then restart ComfyUI.

Registry page: https://comfyregistry.org/nodes/manycoretech/aholo-world-generate

### Manual Installation

Clone or symlink this repository into ComfyUI's `custom_nodes/` directory:

```bash
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/manycoretech/ComfyUI-Aholo-World-Generate.git
cd ComfyUI-Aholo-World-Generate
pip install -r requirements.txt
```

Restart ComfyUI. The following nodes will appear under **Aholo/World**:

- **Aholo World Generate** — submits an async generation task
- **Aholo World Wait** — polls the task until it reaches `SUCCEEDED`

Requires ComfyUI **>= 0.3.0** with `comfy_api` V3 support. If your ComfyUI version is older, upgrade ComfyUI first or this plugin will not load.

## Environment Variables

| Variable | Description |
|------|------|
| `AHOLO_API_KEY` | Aholo Open Platform API key |

Get an API key:

- China: https://labs.aholo3d.cn/api-keys
- Global: https://labs.aholo3d.com/api-keys

The node-level `api_key` input can override this environment variable.

## Quick Start

```text
[prompt] ──► [Aholo World Generate] ── world_id ──► [Aholo World Wait] ──► pano/spz/ply URL
[image]  ──►       (optional reference image)
```

1. Enter a `prompt` in **Generate**. You can also provide an `image`; at least one of `prompt` or `image` is required.
2. Connect `world_id` from **Generate** to **Wait**.
3. `region` defaults to `cn`; use `com` for the global endpoint.
4. **Wait** polls for up to 1800 seconds by default, every 3 seconds. On success, it outputs panorama and splat asset URLs.

ComfyUI output sockets represent connectable data and do not display string values directly on the node. After **Wait** succeeds, it shows a text preview on the node. To view or save URLs elsewhere on the canvas, connect `pano_url`, `spz_url`, or `ply_url` to a text display or text saving node.

Example prompt: `abandoned industrial factory interior, high-ceiling space with rusty metal pipes, sunlight and volumetric rays through large windows, cracked concrete floor with shallow water reflections, ivy and greenery covering the walls and window frames, dense forest outside, cinematic lighting, realistic style`

## Example Workflows

The `examples/` directory contains importable workflows. To open a UI workflow in ComfyUI:

- Drag the `.json` file onto the canvas, or
- Press `Ctrl+O` / `Cmd+O`, or
- Use the menu **File → Open**

| File | Description |
|------|------|
| `spatial_gen_prompt.json` | Prompt-only workflow |
| `spatial_gen_prompt_image.json` | Prompt + reference image. Copy `examples/example.jpg` to ComfyUI's `input/` directory before running. |
| `*.api.json` | API-format workflows for ComfyUI `/prompt` calls |

Validate example files:

```bash
python scripts/validate_examples.py
```

## Local Testing

```bash
pip install -e ".[dev]"
python -m pytest -q
python scripts/validate_examples.py
```

## CLI Smoke Tests

```bash
pip install -r requirements.txt torch pillow numpy
python scripts/smoke_upload.py
python scripts/smoke_generate.py
python scripts/smoke_generate.py --with-image
```
