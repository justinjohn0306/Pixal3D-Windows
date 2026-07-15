"""Optional auto-rigging post-process backed by SkinTokens (VAST-AI-Research).

SkinTokens (https://github.com/VAST-AI-Research/SkinTokens) generates a
skeleton and skinning weights for a static mesh. It lives in its own Python
environment (different torch/flash-attn stack than Pixal3D), so it is invoked
as a subprocess rather than imported.

Configuration (environment variables, both optional):
    SKINTOKENS_DIR     Path to the SkinTokens checkout.
                       Default: a "SkinTokens" directory next to this repo.
    SKINTOKENS_PYTHON  Python executable of the SkinTokens environment.
                       Default: auto-detected (.venv inside SKINTOKENS_DIR,
                       or a conda env named "SkinTokens").
"""

import os
import subprocess
import sys
from typing import Callable, Optional

_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))

# demo.py stdout markers -> user-facing progress stages
_PROGRESS_MARKERS = [
    ("bpy_server.py started", "Rigging: starting mesh server"),
    ("Loading model:", "Rigging: loading SkinTokens model"),
    ("Model loaded", "Rigging: generating skeleton & skin weights"),
    ("[OK] Exported", "Rigging: exported"),
]


def find_skintokens_dir() -> Optional[str]:
    candidates = [
        os.environ.get("SKINTOKENS_DIR"),
        os.path.join(os.path.dirname(_REPO_ROOT), "SkinTokens"),
    ]
    for d in candidates:
        if d and os.path.isfile(os.path.join(d, "demo.py")):
            return os.path.abspath(d)
    return None


def find_skintokens_python(skintokens_dir: Optional[str] = None) -> Optional[str]:
    exe = "python.exe" if os.name == "nt" else "python"
    candidates = [os.environ.get("SKINTOKENS_PYTHON")]
    if skintokens_dir:
        candidates.append(os.path.join(
            skintokens_dir, ".venv", "Scripts" if os.name == "nt" else "bin", exe))
    # conda env named "SkinTokens": sys.prefix is either <base> or <base>/envs/<name>
    prefix = sys.prefix
    if os.path.basename(os.path.dirname(prefix)) == "envs":
        base = os.path.dirname(os.path.dirname(prefix))
    else:
        base = prefix
    candidates.append(os.path.join(base, "envs", "SkinTokens", exe))
    for p in candidates:
        if p and os.path.isfile(p):
            return os.path.abspath(p)
    return None


def rigging_available() -> bool:
    d = find_skintokens_dir()
    return d is not None and find_skintokens_python(d) is not None


def rig_glb(
    input_glb: str,
    output_glb: str,
    use_transfer: bool = True,
    progress_callback: Optional[Callable[[str], None]] = None,
    timeout: int = 1800,
) -> str:
    """Rig a GLB with SkinTokens; returns the output path.

    Raises RuntimeError if SkinTokens is not installed or the run fails.
    """
    skintokens_dir = find_skintokens_dir()
    if skintokens_dir is None:
        raise RuntimeError(
            "SkinTokens not found. Clone https://github.com/VAST-AI-Research/SkinTokens "
            "next to this repo (or set SKINTOKENS_DIR).")
    python_exe = find_skintokens_python(skintokens_dir)
    if python_exe is None:
        raise RuntimeError(
            "SkinTokens Python environment not found. Set SKINTOKENS_PYTHON to the "
            "python executable of the environment where SkinTokens is installed.")

    input_glb = os.path.abspath(input_glb)
    output_glb = os.path.abspath(output_glb)
    if not os.path.isfile(input_glb):
        raise RuntimeError(f"Input GLB not found: {input_glb}")
    os.makedirs(os.path.dirname(output_glb), exist_ok=True)

    cmd = [python_exe, "demo.py", "--input", input_glb, "--output", output_glb]
    if use_transfer:
        cmd.append("--use_transfer")

    if progress_callback:
        progress_callback("Rigging: starting SkinTokens")
    print(f"[Rigging] {' '.join(cmd)}")

    log_lines = []
    proc = subprocess.Popen(
        cmd, cwd=skintokens_dir,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", bufsize=1,
    )
    try:
        for line in proc.stdout:
            line = line.rstrip()
            if not line:
                continue
            log_lines.append(line)
            print(f"[SkinTokens] {line}")
            if progress_callback:
                for marker, stage in _PROGRESS_MARKERS:
                    if marker in line:
                        progress_callback(stage)
                        break
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        raise RuntimeError(f"SkinTokens timed out after {timeout}s")
    finally:
        if proc.poll() is None:
            proc.kill()

    if proc.returncode != 0 or not os.path.isfile(output_glb):
        tail = "\n".join(log_lines[-15:])
        raise RuntimeError(
            f"SkinTokens failed (exit code {proc.returncode}). Last output:\n{tail}")
    return output_glb


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Auto-rig a GLB with SkinTokens")
    parser.add_argument("--input", required=True, help="Input GLB path")
    parser.add_argument("--output", required=True, help="Output (rigged) GLB path")
    parser.add_argument("--no_transfer", action="store_true",
                        help="Skip texture/scale transfer from the source mesh")
    args = parser.parse_args()
    rig_glb(args.input, args.output, use_transfer=not args.no_transfer)
    print(f"[Done] Rigged GLB saved to: {args.output}")
