# ComfyUI-Aholo-World-Generate

[English](README.md) | 简体中文

Aholo **Spatial Gen**（3D 室内空间生成）的 ComfyUI V3 自定义节点插件。

## 安装

### 手动安装

将本仓库克隆或软链到 ComfyUI 的 `custom_nodes/` 目录：

```bash
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/manycoretech/ComfyUI-Aholo-World-Generate.git
cd ComfyUI-Aholo-World-Generate
pip install -r requirements.txt
```

重启 ComfyUI 后，在节点菜单 **Aholo/World** 下可见：

- **Aholo World Generate** — 提交异步生成任务
- **Aholo World Wait** — 轮询任务直至 `SUCCEEDED`

要求 ComfyUI **>= 0.3.0**（支持 `comfy_api` V3）。如果你的 ComfyUI 版本较旧，请先升级 ComfyUI，否则插件无法加载。

## 环境变量

| 变量 | 说明 |
|------|------|
| `AHOLO_API_KEY` | Aholo 开放平台 API Key |

API Key 申请地址：

- 国内：https://labs.aholo3d.cn/api-keys
- 海外：https://labs.aholo3d.com/api-keys

节点内 `api_key` 可覆盖上述环境变量。

## 快速使用

```text
[prompt] ──► [Aholo World Generate] ── world_id ──► [Aholo World Wait] ──► pano/spz/ply URL
[image]  ──►       (可选垫图)
```

1. 在 **Generate** 填写 `prompt`（或与 `image` 至少其一）。
2. 将 `world_id` 连到 **Wait**。
3. `region` 默认 `cn`；海外用 `com`。
4. Wait 默认轮询 1800s（30 分钟）、间隔 3s；成功时输出全景与 splat 产物 URL。

ComfyUI 的输出插槽只表示可连接的数据，不会直接显示字符串内容。Wait 节点成功后会在节点上显示文本预览；如需在画布其他位置查看或保存具体 URL，可将 `pano_url` / `spz_url` / `ply_url` 连接到文本显示或保存类节点。

示例 prompt：`废弃工业厂房室内，高挑空间与生锈金属管道，多扇大窗透入阳光与丁达尔光束，裂缝混凝土地面与浅水倒影，墙面与窗框爬满常春藤与绿植，窗外茂密森林，电影感光影，写实风格`

## 示例 Workflow

`examples/` 目录提供可导入的 Workflow：

| 文件 | 说明 |
|------|------|
| `spatial_gen_prompt.json` | 纯 prompt（ComfyUI **Workflow → Open**） |
| `spatial_gen_prompt_image.json` | prompt + 垫图（将 `examples/example.jpg` 复制到 ComfyUI `input/` 目录） |
| `*.api.json` | API 格式（**File → Export Workflow (API)** 同类结构，供 `/prompt` 调用） |

校验示例文件：

```bash
python scripts/validate_examples.py
```

## 本地测试

```bash
pip install -e ".[dev]"
python -m pytest -q
python scripts/validate_examples.py
```

## 命令行冒烟测试（无需 ComfyUI）

```bash
pip install httpx torch pillow numpy
python scripts/smoke_upload.py
python scripts/smoke_generate.py
python scripts/smoke_generate.py --with-image
```
