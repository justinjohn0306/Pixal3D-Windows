@echo off
setlocal
pushd "%~dp0"
REM Pixal3D Gradio web demo launcher (Windows). Run inside your activated pixal3d environment.
REM Optional: set LOW_VRAM=1 to reduce peak VRAM (default resolution drops to 1024)
REM Optional: set GRADIO_SHARE=1 to create a public gradio.live share link

for /f "delims=" %%p in ('python -c "import sys; print(sys.exec_prefix)"') do set "PYROOT=%%p"
if not defined PYROOT echo [Error] python not found - activate your pixal3d environment first. && exit /b 1

REM Minimal PATH before vcvars64: it appends ~2k chars and overflows cmd's 8191-char
REM line limit when combined with a long user/conda PATH ("The input line is too long")
set "PATH=%PYROOT%;%PYROOT%\Library\bin;%PYROOT%\Scripts;C:\Windows\System32;C:\Windows"

REM MSVC env for any runtime CUDA JIT (triton / torch cpp_extension)
for /f "usebackq delims=" %%i in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VSPATH=%%i"
if defined VSPATH call "%VSPATH%\VC\Auxiliary\Build\vcvars64.bat" >nul

REM Attention backend (flash_attn wheel installed by setup_windows.py; fallback: sdpa)
if not defined ATTN_BACKEND set ATTN_BACKEND=flash_attn

REM Must be set before cv2 import so the EnvMap .exr assets can be read
set OPENCV_IO_ENABLE_OPENEXR=1

REM Optional: set REMBG_MODEL to override the background-removal model
REM (config default briaai/RMBG-2.0 requires HF login + accepted license;
REM  un-gated alternatives: 1038lab/RMBG-2.0, ZhengPeng7/BiRefNet)

"%PYROOT%\python.exe" app.py %*
