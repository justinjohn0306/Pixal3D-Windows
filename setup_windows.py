"""
Native Windows setup for Pixal3D.

Run inside an activated Python 3.12 environment (conda recommended):

    conda create -n pixal3d python=3.12 -y
    conda activate pixal3d
    python setup_windows.py

Installs PyTorch 2.10 (cu130), prebuilt Windows wheels for the CUDA
extensions (FlexGEMM, CuMesh, O-Voxel, NATTEN, FlashAttention), compiles
nvdiffrast against your local MSVC, and applies the small compatibility
patches Windows needs. Requires Visual Studio with the C++ workload.
"""
import os
import sys
import glob
import shutil
import subprocess
import tempfile
import urllib.request

TORCH_INDEX = "https://download.pytorch.org/whl/cu130"
TORCH_VERSION = "2.10.0"

CUDA_WHEELS = [
    # Community Windows builds of the TRELLIS.2 CUDA extensions (PozzettiAndrea/cuda-wheels)
    "https://github.com/PozzettiAndrea/cuda-wheels/releases/download/flex_gemm_ap-latest/flex_gemm_ap-1.0.0%2Bcu130torch2.10-cp312-cp312-win_amd64.whl",
    "https://github.com/PozzettiAndrea/cuda-wheels/releases/download/cumesh_vb-latest/cumesh_vb-1.0%2Bcu130torch2.10-cp312-cp312-win_amd64.whl",
    "https://github.com/PozzettiAndrea/cuda-wheels/releases/download/o_voxel_vb_ap-latest/o_voxel_vb_ap-0.0.1%2Bcu130torch2.10-cp312-cp312-win_amd64.whl",
    "https://github.com/PozzettiAndrea/cuda-wheels/releases/download/flash_attn-latest/flash_attn-2.8.3%2Bcu130torch2.10-cp312-cp312-win_amd64.whl",
]

# NATTEN Windows builds are architecture-specific (NeilsMabet / drbaph)
NATTEN_WHEELS = {
    (8, 6): "https://raw.githubusercontent.com/NeilsMabet/Natten-0.21.6-Amphere-wheel-windows/main/natten-0.21.6-torch210-cu130-cp312-cp312-win_amd64.whl.whl",
    (8, 9): "https://raw.githubusercontent.com/NeilsMabet/Natten-0.21.6-Amphere-wheel-windows/main/natten-0.21.6-ada-lovelace-torch210-cu130-cp312-win_amd64.whl",
    (12, 0): "https://huggingface.co/drbaph/NATTEN-0.21.6-torch2100cu130-cp312-cp312-win_amd64/resolve/main/natten-0.21.6+torch2100cu130-cp312-cp312-win_amd64.whl",
}

UTILS3D_WHEEL = "https://github.com/LDYang694/Storages/releases/download/20260430/utils3d-0.0.2-py3-none-any.whl"

# The o_voxel Windows wheel omits two pure-Python modules; graft them from TRELLIS.2 (MIT)
TRELLIS2_RAW = "https://raw.githubusercontent.com/microsoft/TRELLIS.2/main/o-voxel/o_voxel"
OVOXEL_MISSING_MODULES = ["postprocess.py", "rasterize.py"]

# The wheels install under variant names; Pixal3D imports the plain ones
MODULE_ALIASES = {
    "flex_gemm": "flex_gemm_ap",
    "cumesh": "cumesh_vb",
    "o_voxel": "o_voxel_vb_ap",
}


def run(cmd, env=None):
    print(f"[Setup] $ {' '.join(cmd)}")
    subprocess.check_call(cmd, env=env)


def pip(*args, env=None):
    run([sys.executable, "-m", "pip", "install", *args], env=env)


def check_python():
    if sys.version_info[:2] != (3, 12):
        sys.exit(f"[Setup] Python 3.12 required (found {sys.version.split()[0]}). "
                 "The prebuilt Windows wheels are cp312-only.")


def install_torch():
    pip(f"torch=={TORCH_VERSION}", "torchvision", "--index-url", TORCH_INDEX)


def cuda_arch():
    out = subprocess.check_output([
        sys.executable, "-c",
        "import torch; print(*torch.cuda.get_device_capability())",
    ]).split()
    return int(out[0]), int(out[1])


def install_natten():
    arch = cuda_arch()
    url = NATTEN_WHEELS.get(arch)
    if url is None:
        print(f"[Setup] No prebuilt NATTEN wheel for sm_{arch[0]}{arch[1]}, skipping. "
              "NAF upsampling may be unavailable; see README for building NATTEN from source.")
        return
    # Some community wheels have malformed filenames; download and normalize
    with tempfile.TemporaryDirectory() as tmp:
        dst = os.path.join(tmp, "natten-0.21.6-cp312-cp312-win_amd64.whl")
        print(f"[Setup] Downloading NATTEN wheel for sm_{arch[0]}{arch[1]}...")
        urllib.request.urlretrieve(url, dst)
        pip("--no-deps", dst)


def install_cuda_wheels():
    pip("--no-deps", *CUDA_WHEELS)


def install_requirements():
    pip("-r", "requirements.txt")
    pip("einops", "triton-windows<3.7")
    # MoGe drags in a newer utils3d; the pinned wheel must win (app.py also self-repairs this)
    pip("--force-reinstall", "--no-deps", UTILS3D_WHEEL)


def site_packages():
    import sysconfig
    return sysconfig.get_paths()["purelib"]


def create_aliases():
    sp = site_packages()
    for alias, target in MODULE_ALIASES.items():
        pkg_dir = os.path.join(sp, alias)
        os.makedirs(pkg_dir, exist_ok=True)
        with open(os.path.join(pkg_dir, "__init__.py"), "w") as f:
            f.write(
                f"# Alias: Pixal3D imports `{alias}`, the Windows community wheel installs `{target}`.\n"
                f"import sys\n"
                f"import {target} as _impl\n"
                f"sys.modules[__name__] = _impl\n"
            )
        print(f"[Setup] Alias created: {alias} -> {target}")


def graft_o_voxel():
    sp = site_packages()
    pkg = os.path.join(sp, MODULE_ALIASES["o_voxel"])
    for name in OVOXEL_MISSING_MODULES:
        dst = os.path.join(pkg, name)
        print(f"[Setup] Grafting o_voxel/{name} from TRELLIS.2...")
        urllib.request.urlretrieve(f"{TRELLIS2_RAW}/{name}", dst)
    init_path = os.path.join(pkg, "__init__.py")
    with open(init_path) as f:
        init = f.read()
    if "postprocess" not in init:
        init = init.replace(
            "from . import (\n    convert,",
            "from . import (\n    convert,\n    postprocess,\n    rasterize,",
            1,
        )
        with open(init_path, "w") as f:
            f.write(init)
        print("[Setup] o_voxel __init__ updated to expose grafted modules")


def msvc_env():
    vswhere = os.path.join(
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
        "Microsoft Visual Studio", "Installer", "vswhere.exe",
    )
    vs_path = subprocess.check_output([
        vswhere, "-latest", "-products", "*",
        "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
        "-property", "installationPath",
    ], text=True).strip()
    vcvars = os.path.join(vs_path, "VC", "Auxiliary", "Build", "vcvars64.bat")
    out = subprocess.check_output(f'cmd /s /c ""{vcvars}" >nul && set"', shell=True, text=True)
    env = dict(line.split("=", 1) for line in out.splitlines() if "=" in line)
    env["DISTUTILS_USE_SDK"] = "1"
    env["MSSdk"] = "1"
    return env


def install_nvdiffrast():
    print("[Setup] Compiling nvdiffrast and nvdiffrec (requires MSVC + CUDA toolkit)...")
    pip("ninja")
    env = msvc_env()
    pip("--no-build-isolation", "git+https://github.com/NVlabs/nvdiffrast.git", env=env)
    # nvdiffrec_render: PBR shading for preview video rendering (TRELLIS.2's --nvdiffrec extension)
    pip("--no-build-isolation", "git+https://github.com/JeffreyXiang/nvdiffrec.git@renderutils", env=env)


def verify():
    code = (
        "import os; os.environ.setdefault('ATTN_BACKEND', 'flash_attn')\n"
        "import torch, o_voxel, o_voxel.postprocess, cumesh, flex_gemm, "
        "flex_gemm.ops.grid_sample, nvdiffrast.torch, nvdiffrec_render.light, "
        "utils3d, flash_attn, moge\n"
        "print('[Setup] All imports OK -', torch.__version__, torch.cuda.get_device_name(0))\n"
    )
    subprocess.check_call([sys.executable, "-c", code])


if __name__ == "__main__":
    check_python()
    install_torch()
    install_cuda_wheels()
    install_natten()
    install_requirements()
    create_aliases()
    graft_o_voxel()
    install_nvdiffrast()
    verify()
    print("[Setup] Done. Try: run_inference.bat --image assets\\images\\0_img.png --output output.glb")
