
<div align="center">

# Pixal3D: Pixel-Aligned 3D Generation from Images

<h3>SIGGRAPH 2026</h3>

<small>[Dong-Yang Li](https://ldyang694.github.io/)¹ · [Wang Zhao](https://thuzhaowang.github.io/)²* · [Yuxin Chen](https://orcid.org/0000-0002-7854-1072)² · [Wenbo Hu](https://wbhu.github.io/)² · [Meng-Hao Guo](https://menghaoguo.github.io/)¹ · [Fang-Lue Zhang](https://fanglue.github.io/)³ · [Ying Shan](https://www.linkedin.com/in/YingShanProfile)² · [Shi-Min Hu](https://cg.cs.tsinghua.edu.cn/shimin.htm)¹✉</small>

¹Tsinghua University (BNRist) &nbsp;&nbsp; ²Tencent ARC Lab &nbsp;&nbsp; ³Victoria University of Wellington

*Project lead &nbsp;&nbsp; ✉Corresponding author

</div>

<div align="center">
  <a href="https://ldyang694.github.io/projects/pixal3d/"><img src=https://img.shields.io/badge/Project%20Page-333399.svg?logo=googlehome height=22px></a>
  <a href="https://huggingface.co/spaces/TencentARC/Pixal3D"><img src=https://img.shields.io/badge/%F0%9F%A4%97%20Demo-276cb4.svg height=22px></a>
  <a href="https://huggingface.co/TencentARC/Pixal3D"><img src=https://img.shields.io/badge/%F0%9F%A4%97%20Models-d96902.svg height=22px></a>
  <a href="https://arxiv.org/abs/2605.10922"><img src=https://img.shields.io/badge/Arxiv-b5212f.svg?logo=arxiv height=22px></a>
  <a href="LICENSE"><img src=https://img.shields.io/badge/License-MIT-yellow.svg height=22px></a>
</div>

<div align="center">
    <img src="assets/teaser.png" alt="Teaser image of Pixal3D"/>
</div>

**Pixal3D** generates high-fidelity 3D assets from a single image. Unlike previous methods that loosely inject image features via attention, Pixal3D explicitly lifts pixel features into 3D through back-projection, establishing direct pixel-to-3D correspondences. This enables near-reconstruction-level fidelity with detailed geometry and PBR textures.

---

## ✨ News

- **May 2026**: Release training code and data preparation toolkit. 🔧
- **May 2026**: Release the improved version based on [Trellis.2](https://github.com/microsoft/TRELLIS.2) backbone. 💪
- **May 2026**: Release inference code and online demo. 🤗
- **Apr 2026**: Our paper is accepted to SIGGRAPH 2026! 🎉

## 📌 Branches

| Branch | Description |
|--------|-------------|
| `main` | **Latest version** — improved implementation based on [Trellis.2](https://github.com/microsoft/TRELLIS.2) backbone with better performance. |
| `paper` | **Paper version** — original implementation based on [Direct3D-S2](https://github.com/DreamTechAI/Direct3D-S2), corresponding to results reported in our SIGGRAPH 2026 paper. |

> If you want to reproduce the results in our paper, please switch to the `paper` branch.

## 🎮 Try It Online

You can try Pixal3D directly in your browser without any installation via our Hugging Face Gradio demo:

👉 [**Launch Demo**](https://huggingface.co/spaces/TencentARC/Pixal3D)

## 🚀 Getting Started

### Installation

#### Step 1: Follow TRELLIS.2 Installation

Please first follow the installation guide of [TRELLIS.2](https://github.com/microsoft/TRELLIS.2) to set up the base environment.

#### Step 2: Install Additional Dependencies

```bash
pip install -r requirements.txt
```

#### Step 3: Install natten

```bash
NATTEN_CUDA_ARCH="xx" NATTEN_N_WORKERS=xx pip install natten==0.21.0 --no-build-isolation
```

Please replace `xx` with the CUDA architecture and the number of build workers suitable for your machine.

#### Step 4: Install utils3d

```bash
pip install https://github.com/LDYang694/Storages/releases/download/20260430/utils3d-0.0.2-py3-none-any.whl
```

> **Note**: `requirements-hfdemo.txt` is for the Hugging Face Spaces demo (H-series GPU architecture) and may not be compatible with other architectures.

### Windows Installation (this fork)

This fork runs natively on Windows — no WSL required. Tested on Windows 11 with an RTX 3090 (24 GB, CUDA 13.0).

**Requirements:**

- Python 3.12 (conda recommended)
- Visual Studio 2022 or later with the *Desktop development with C++* workload
- CUDA Toolkit 13.x
- NVIDIA GPU (Ampere or newer)

```bash
conda create -n pixal3d python=3.12 -y
conda activate pixal3d
python setup_windows.py
```

The setup script installs PyTorch 2.10 (cu130), prebuilt Windows wheels for all CUDA extensions (FlexGEMM, CuMesh, O-Voxel, FlashAttention, NATTEN), compiles [nvdiffrast](https://github.com/NVlabs/nvdiffrast) and [nvdiffrec](https://github.com/JeffreyXiang/nvdiffrec) against your local MSVC, and applies the small compatibility patches Windows needs.

Then use the provided launchers — they configure the attention backend, OpenEXR support, and the MSVC environment automatically:

```bat
:: CLI inference
run_inference.bat --image assets\images\0_img.png --output output.glb --low_vram

:: Gradio web demo (http://127.0.0.1:7860)
run_app.bat
```

> **Note**: The default background-removal model `briaai/RMBG-2.0` is a gated Hugging Face repo. Either request access and log in with `hf auth login`, or point to an un-gated alternative before launching: `set REMBG_MODEL=1038lab/RMBG-2.0`

> **VRAM**: 24 GB runs the full 1536 pipeline; use `--low_vram` (CLI) or `LOW_VRAM=1` (web demo) for ~10-12 GB peak at 1024 resolution. If FlashAttention gives you trouble, `set ATTN_BACKEND=sdpa` falls back to PyTorch's built-in attention (slower).

### Usage

#### Inference

Generate a GLB mesh from a single image:

```bash
python inference.py --image assets/images/0_img.png --output ./output.glb
```

**Low-VRAM mode** (reduces peak VRAM by loading models on-demand):

```bash
python inference.py --image assets/images/0_img.png --output ./output.glb --low_vram
```

By default, the pipeline resolution is **1536** (standard mode) or **1024** (low-VRAM mode). You can override this with `--resolution`:

```bash
# Force 1536 even in low-VRAM mode
python inference.py --image assets/images/0_img.png --output ./output.glb --low_vram --resolution 1536

# Force 1024 in standard mode
python inference.py --image assets/images/0_img.png --output ./output.glb --resolution 1024
```

**Tip**: If you don't have `flash_attn` installed, you can use PyTorch's built-in SDPA backend instead:
> ```bash
> ATTN_BACKEND=sdpa python inference.py --image assets/images/0_img.png --output ./output.glb --low_vram
> ```

### Web Demo

We provide a Gradio web demo for Pixal3D, which allows you to generate 3D meshes from images interactively.

```bash
python app.py 
```

Low-VRAM mode is also available for the web demo. The frontend default resolution will automatically switch to 1024 in low-VRAM mode (1536 otherwise), but can be changed manually in the UI.

```bash
python app.py --low_vram
# or via environment variable:
LOW_VRAM=1 python app.py
```

### Auto-Rigging (optional)

Generated meshes can be automatically rigged (skeleton + skinning weights) with [SkinTokens](https://github.com/VAST-AI-Research/SkinTokens), producing an animation-ready GLB. SkinTokens runs in its own Python environment and is invoked as a subprocess, so its torch/flash-attn stack never conflicts with Pixal3D's.

**Setup** — clone SkinTokens next to this repo and follow [its installation guide](https://github.com/VAST-AI-Research/SkinTokens#-installation) (needs ~14 GB VRAM at inference):

```bash
git clone https://github.com/VAST-AI-Research/SkinTokens ../SkinTokens
# ... install its environment per its README, then download its checkpoints:
# python download.py --model
```

If SkinTokens lives elsewhere or uses a non-default environment, point to it explicitly:

```bash
set SKINTOKENS_DIR=D:\path\to\SkinTokens
set SKINTOKENS_PYTHON=D:\path\to\envs\SkinTokens\python.exe
```

Auto-detection looks for a `SkinTokens` directory next to this repo, and a `.venv` inside it or a conda env named `SkinTokens`.

**Usage:**

```bash
# CLI: writes output.glb plus output_rigged.glb
python inference.py --image assets/images/0_img.png --output ./output.glb --rig

# Standalone: rig any existing GLB
python rigging.py --input ./output.glb --output ./output_rigged.glb
```

In the web demo, a **Rig Character** button appears in step 3 (after mesh extraction) whenever a SkinTokens installation is detected. The Pixal3D models are temporarily offloaded to CPU while rigging runs, then restored.

> **Note**: SkinTokens installation on Windows: use a prebuilt flash-attn wheel from [kingbri1/flash-attention](https://github.com/kingbri1/flash-attention/releases) matching its torch/CUDA/Python versions, and `pip install scipy` (missing from its requirements.txt).

## 🔧 Training

We provide the full training codebase for reproducing Pixal3D from scratch.

### Data Preparation

Prepare view-aligned O-Voxel data and rendered condition images by following the data toolkit instructions:

> 📂 **[data_toolkit/README.md](data_toolkit/README.md)**

### Overview

Pixal3D is trained as a three-stage cascade, each progressively increasing resolution:

| Stage | Model | Resolutions | Config Prefix |
|-------|-------|-------------|---------------|
| 1 | Sparse Structure | 32 → 64 | `ss_flow_img_dit_*_proj_finetune` |
| 2 | Shape | 256 → 512 → 1024 | `slat_flow_img2shape_*_proj_finetune` |
| 3 | Texture | 256 → 512 → 1024 | `slat_flow_imgshape2tex_*_proj_finetune` |

All stages use **pixel-aligned projection conditioning** and **view-aligned latents** (2 views by default). Within each stage, start from the lowest resolution and progressively fine-tune to higher resolutions by setting `finetune_ckpt` in the config.

### Quick Start

```sh
python train.py \
  --config <CONFIG_JSON> \
  --output_dir <OUTPUT_DIR> \
  --data_dir '<DATA_DIR_JSON>'
```

`--data_dir` is a JSON string describing the dataset layout. Different stages require different keys:

| Stage | Required keys |
|-------|---------------|
| Sparse Structure | `base`, `ss_latent`, `render_cond` |
| Shape | `base`, `shape_latent`, `render_cond` |
| Texture | `base`, `shape_latent`, `pbr_latent`, `render_cond` |

### Example: Training All Three Stages

Below we show the full training sequence using ObjaverseXL as an example. Each higher-resolution step requires updating `finetune_ckpt` in its config JSON to point to the previous checkpoint.

<details>
<summary><b>Stage 1: Sparse Structure (32 → 64)</b></summary>

```sh
# Resolution 32
python train.py \
  --config configs/gen/ss_flow_img_dit_1_3B_32_bf16_proj_finetune.json \
  --output_dir results/ss_32 \
  --data_dir '{"ObjaverseXL_sketchfab": {"base": "datasets/ObjaverseXL_sketchfab", "ss_latent": "datasets/ObjaverseXL_sketchfab/ss_latents/ss_enc_conv3d_16l8_fp16_64_view", "render_cond": "datasets/ObjaverseXL_sketchfab/renders_cond"}}'

# Resolution 64 (set finetune_ckpt → results/ss_32 checkpoint)
python train.py \
  --config configs/gen/ss_flow_img_dit_1_3B_32_bf16_proj_finetune_ft64.json \
  --output_dir results/ss_ft64 \
  --data_dir '{"ObjaverseXL_sketchfab": {"base": "datasets/ObjaverseXL_sketchfab", "ss_latent": "datasets/ObjaverseXL_sketchfab/ss_latents/ss_enc_conv3d_16l8_fp16_64_view", "render_cond": "datasets/ObjaverseXL_sketchfab/renders_cond"}}'
```
</details>

<details>
<summary><b>Stage 2: Shape (256 → 512 → 1024)</b></summary>

```sh
# Resolution 256
python train.py \
  --config configs/gen/slat_flow_img2shape_dit_1_3B_256_bf16_proj_finetune.json \
  --output_dir results/shape_256 \
  --data_dir '{"ObjaverseXL_sketchfab": {"base": "datasets/ObjaverseXL_sketchfab", "shape_latent": "datasets/ObjaverseXL_sketchfab/shape_latents/shape_enc_next_dc_f16c32_fp16_256_view", "render_cond": "datasets/ObjaverseXL_sketchfab/renders_cond"}}'

# Resolution 512
python train.py \
  --config configs/gen/slat_flow_img2shape_dit_1_3B_256_bf16_proj_finetune_ft512.json \
  --output_dir results/shape_ft512 \
  --data_dir '{"ObjaverseXL_sketchfab": {"base": "datasets/ObjaverseXL_sketchfab", "shape_latent": "datasets/ObjaverseXL_sketchfab/shape_latents/shape_enc_next_dc_f16c32_fp16_512_view", "render_cond": "datasets/ObjaverseXL_sketchfab/renders_cond"}}'

# Resolution 1024
python train.py \
  --config configs/gen/slat_flow_img2shape_dit_1_3B_512_bf16_proj_finetune_ft1024.json \
  --output_dir results/shape_ft1024 \
  --data_dir '{"ObjaverseXL_sketchfab": {"base": "datasets/ObjaverseXL_sketchfab", "shape_latent": "datasets/ObjaverseXL_sketchfab/shape_latents/shape_enc_next_dc_f16c32_fp16_1024_view", "render_cond": "datasets/ObjaverseXL_sketchfab/renders_cond"}}'
```
</details>

<details>
<summary><b>Stage 3: Texture (256 → 512 → 1024)</b></summary>

```sh
# Resolution 256
python train.py \
  --config configs/gen/slat_flow_imgshape2tex_dit_1_3B_256_bf16_proj_finetune.json \
  --output_dir results/tex_256 \
  --data_dir '{"ObjaverseXL_sketchfab": {"base": "datasets/ObjaverseXL_sketchfab", "shape_latent": "datasets/ObjaverseXL_sketchfab/shape_latents/shape_enc_next_dc_f16c32_fp16_256_view", "pbr_latent": "datasets/ObjaverseXL_sketchfab/pbr_latents/tex_enc_next_dc_f16c32_fp16_256_view", "render_cond": "datasets/ObjaverseXL_sketchfab/renders_cond"}}'

# Resolution 512
python train.py \
  --config configs/gen/slat_flow_imgshape2tex_dit_1_3B_512_bf16_proj_finetune.json \
  --output_dir results/tex_512 \
  --data_dir '{"ObjaverseXL_sketchfab": {"base": "datasets/ObjaverseXL_sketchfab", "shape_latent": "datasets/ObjaverseXL_sketchfab/shape_latents/shape_enc_next_dc_f16c32_fp16_512_view", "pbr_latent": "datasets/ObjaverseXL_sketchfab/pbr_latents/tex_enc_next_dc_f16c32_fp16_512_view", "render_cond": "datasets/ObjaverseXL_sketchfab/renders_cond"}}'

# Resolution 1024
python train.py \
  --config configs/gen/slat_flow_imgshape2tex_dit_1_3B_512_bf16_proj_finetune_ft1024.json \
  --output_dir results/tex_ft1024 \
  --data_dir '{"ObjaverseXL_sketchfab": {"base": "datasets/ObjaverseXL_sketchfab", "shape_latent": "datasets/ObjaverseXL_sketchfab/shape_latents/shape_enc_next_dc_f16c32_fp16_1024_view", "pbr_latent": "datasets/ObjaverseXL_sketchfab/pbr_latents/tex_enc_next_dc_f16c32_fp16_1024_view", "render_cond": "datasets/ObjaverseXL_sketchfab/renders_cond"}}'
```
</details>

### Additional Options

<details>
<summary><b>All command-line arguments</b></summary>

| Argument | Description | Default |
|----------|-------------|---------|
| `--config` | Config JSON path | *required* |
| `--output_dir` | Output directory | *required* |
| `--data_dir` | Dataset JSON string | `./data/` |
| `--load_dir` | Checkpoint load directory | `output_dir` |
| `--ckpt` | Resume from step | `latest` |
| `--auto_retry` | Retries on failure | `3` |
| `--tryrun` | Dry run | `false` |
| `--profile` | Profiling | `false` |
| `--num_nodes` | Number of nodes | `1` |
| `--node_rank` | Current node rank | `0` |
| `--num_gpus` | GPUs per node | all |
| `--master_addr` | Master address | `localhost` |
| `--master_port` | Master port | `12666` |
| `--use_wandb` | Enable W&B logging | `false` |
| `--wandb_project` | W&B project | `trellis2-training` |
| `--wandb_name` | W&B run name | basename of `output_dir` |
| `--wandb_id` | W&B run ID (resume) | — |

</details>

## 🌐 Community Projects

We thank the community for building extensions and deployment guides for Pixal3D!

- [Pixal3D-ComfyUI](https://github.com/Saganaki22/Pixal3D-ComfyUI) — ComfyUI integration with deployment guides for Windows, WSL, and more.

## 🤗 Acknowledgements

This project is heavily built upon [Trellis.2](https://github.com/microsoft/TRELLIS.2) and [Direct3D-S2](https://github.com/DreamTechAI/Direct3D-S2). We sincerely thank the authors for their outstanding work on scalable 3D generation , which serves as the foundation of our codebase and model architecture.

We also thank the following repos for their great contributions:

- [Direct3D-S2](https://github.com/DreamTechAI/Direct3D-S2)
- [Trellis](https://github.com/microsoft/TRELLIS)
- [Trellis.2](https://github.com/microsoft/TRELLIS.2)

The native Windows support in this fork builds on community work:

- [PozzettiAndrea/cuda-wheels](https://github.com/PozzettiAndrea/cuda-wheels) — Windows wheels for FlexGEMM, CuMesh, O-Voxel and FlashAttention
- [NeilsMabet](https://github.com/NeilsMabet/Natten-0.21.6-Amphere-wheel-windows) and [drbaph](https://huggingface.co/drbaph/NATTEN-0.21.6-torch2100cu130-cp312-cp312-win_amd64) — NATTEN Windows builds
- [Saganaki22/Pixal3D-ComfyUI](https://github.com/Saganaki22/Pixal3D-ComfyUI) — Windows deployment guides

## 📄 Citation

If you find this work useful, please consider citing:

```bibtex
@article{li2026pixal3d,
    title={Pixal3D: Pixel-Aligned 3D Generation from Images},
    author={Li, Dong-Yang and Zhao, Wang and Chen, Yuxin and Hu, Wenbo and Guo, Meng-Hao and Zhang, Fang-Lue and Shan, Ying and Hu, Shi-Min},
    journal={arXiv preprint arXiv:2605.10922},
    year={2026}
}
```

## 📜 License

This project is released under the [MIT License](LICENSE). The third-party components included in this project remain licensed under their respective original terms; see [NOTICE](NOTICE) for the full list of dependencies and their licenses.

