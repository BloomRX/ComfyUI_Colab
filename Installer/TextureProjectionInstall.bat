@echo off
REM ============================================================================
REM   PixelArtistry  -  AeroX Texture Projection Installer
REM   For ComfyUI Easy Install (Windows)
REM   https://pixel-artistry.com/TextureProjectionWorkflows
REM ============================================================================
REM   Installs:
REM     - AeroX Texture Projection custom node (always latest from GitHub)
REM     - Its Python dependencies (using --no-deps to preserve numpy etc.)
REM     - Pre-compiled rasterizer wheel matching your environment
REM       (target: Python 3.12 + PyTorch 2.8 + CUDA 12.8)
REM     - CuMesh (visualbruno fork) for the CuMesh UV Unwrap node:
REM       pre-built wheel from ComfyUI-Trellis2\wheels if available,
REM       otherwise compiled from https://github.com/visualbruno/CuMesh
REM     - NVIDIA VFX SDK python package (nvidia-vfx / nvvfx) for the
REM       RTX Video Super Resolution node, from NVIDIA's own pip index
REM
REM   Models are NOT downloaded by this script. Once the node is installed,
REM   download the workflow JSON from:
REM     https://pixel-artistry.com/TextureProjectionWorkflows
REM   Load it in ComfyUI and follow the guide box inside the workflow to
REM   download the required models (FLUX.2 klein 9B GGUF, VAE, text encoders,
REM   albedo LoRA) into the right folders.
REM
REM   Run this script from EITHER:
REM     a) The ComfyUI Easy Install root folder
REM        (contains run_nvidia_gpu.bat, ComfyUI\, python_embeded\)
REM     b) The addons folder inside ComfyUI Easy Install
REM
REM   Requirements:
REM     - ComfyUI Easy Install (portable) already set up
REM     - ComfyUI-Trellis2 + ComfyUI-Trellis2-GGUF already installed
REM     - Python 3.12, PyTorch 2.8, CUDA 12.8 (the recommended baseline)
REM     - NVIDIA GPU with 6GB+ VRAM
REM     - git installed and on PATH
REM ============================================================================

setlocal enabledelayedexpansion
title PixelArtistry - AeroX Texture Projection Installer

echo.
echo ============================================================================
echo   PixelArtistry - AeroX Texture Projection Installer
echo ============================================================================
echo.

REM ---- 0. git check ---------------------------------------------------------

where git >nul 2>nul
if errorlevel 1 (
    echo [ERROR] git is not installed or not on PATH.
    echo         Install git from https://git-scm.com/download/win and re-run.
    pause
    exit /b 1
)

REM ---- 0b. Detect run location ----------------------------------------------

set "BASE="

if exist "ComfyUI\custom_nodes" (
    if exist "python_embeded\python.exe" (
        set "BASE=."
        echo [OK] Detected: running from ComfyUI Easy Install root folder.
    )
)

if not defined BASE (
    if exist "..\ComfyUI\custom_nodes" (
        if exist "..\python_embeded\python.exe" (
            set "BASE=.."
            echo [OK] Detected: running from addons folder.
        )
    )
)

if not defined BASE (
    echo [ERROR] Could not find ComfyUI Easy Install structure.
    echo         Place this script in EITHER:
    echo           a^) The ComfyUI Easy Install root folder
    echo              (the folder with run_nvidia_gpu.bat^)
    echo         OR
    echo           b^) The addons folder inside ComfyUI Easy Install
    pause
    exit /b 1
)

echo.

REM ---- 1. Trellis2 prereq check (BOTH default + GGUF fork required) --------

set "TRELLIS_PLAIN_FOUND=0"
set "TRELLIS_GGUF_FOUND=0"

if exist "%BASE%\ComfyUI\custom_nodes\ComfyUI-Trellis2\" (
    set "TRELLIS_PLAIN_FOUND=1"
    echo [OK] Found default Trellis2 node: ComfyUI-Trellis2
)

if exist "%BASE%\ComfyUI\custom_nodes\ComfyUI-Trellis2-GGUF\" (
    set "TRELLIS_GGUF_FOUND=1"
    echo [OK] Found Trellis2 GGUF fork: ComfyUI-Trellis2-GGUF
)

if "!TRELLIS_PLAIN_FOUND!"=="1" if "!TRELLIS_GGUF_FOUND!"=="1" goto TRELLIS_OK

echo.
echo This workflow needs BOTH custom nodes installed:
if "!TRELLIS_PLAIN_FOUND!"=="0" echo   [MISSING] ComfyUI-Trellis2       ^(default^)
if "!TRELLIS_GGUF_FOUND!"=="0" echo   [MISSING] ComfyUI-Trellis2-GGUF  ^(GGUF fork^)
echo.
echo Install guide on the channel: https://www.youtube.com/@PixelArtistry
echo.
set /p CONTINUE="Continue anyway? (y/N): "
if /i not "!CONTINUE!"=="y" exit /b 1

:TRELLIS_OK
echo.

REM ============================================================================
REM   AeroX repo settings  -  the installer always pulls the latest commit
REM ============================================================================
set AEROX_REPO=https://github.com/Aero-Ex/Texture_Projection-Nodes.git
set AEROX_FOLDER=Texture_Projection-Nodes

REM CuMesh (NOT a custom node - a compiled python package, installed via pip).
REM Source fallback repo if no pre-built wheel is found in ComfyUI-Trellis2:
set CUMESH_REPO=https://github.com/visualbruno/CuMesh.git
REM Pre-built wheels ship inside ComfyUI-Trellis2 (wheels\Windows\Torch280):
set "CUMESH_WHEEL_DIR_REL=ComfyUI\custom_nodes\ComfyUI-Trellis2\wheels\Windows\Torch280"
set CUMESH_WHEEL_PATTERN=cumesh-*cp312*win_amd64.whl

REM Set to 0 to skip the NVIDIA VFX (nvvfx) install step.
set INSTALL_NVVFX=1

REM Pre-compiled rasterizer wheel for the recommended baseline:
REM   Python 3.12 + PyTorch 2.8.0 + CUDA 12.8
REM   Matched by pattern so a renamed wheel in a newer repo commit still works.
set RASTERIZER_WHEEL_PATTERN=custom_rasterizer-*cp312*torch2.8*cu128*win_amd64.whl
REM ============================================================================

set "PYTHON=%BASE%\python_embeded\python.exe"

REM ---- 2. Verify baseline environment ---------------------------------------
REM   Recommended baseline (matches the pre-built wheel above):
REM     Python 3.12, PyTorch 2.8.x, CUDA 12.8
REM   Mismatches are warned but don't block - user can continue at own risk.

echo [STEP 1/5] Verifying environment baseline...
echo.

set "BASELINE_OK=1"

REM Check Python 3.12
for /f "tokens=2" %%V in ('"%PYTHON%" --version 2^>^&1') do set "PY_VER=%%V"
echo   Python:  !PY_VER!
echo !PY_VER! | findstr /b "3.12" >nul
if errorlevel 1 (
    echo   [WARN]   Expected Python 3.12 - the pre-built rasterizer wheel won't match.
    set "BASELINE_OK=0"
)

REM Check PyTorch 2.8.x and CUDA 12.8
REM   Using temp file redirection instead of for /f to avoid nested-quote
REM   parsing issues with the Python -c argument.

set "TMP_TORCH=%TEMP%\pa_torch_ver.txt"
set "TMP_CUDA=%TEMP%\pa_cuda_ver.txt"

"%PYTHON%" -c "import torch; print(torch.__version__)" > "%TMP_TORCH%" 2>nul
set "TORCH_VER="
if exist "%TMP_TORCH%" (
    set /p TORCH_VER=<"%TMP_TORCH%"
    del "%TMP_TORCH%" >nul 2>nul
)

"%PYTHON%" -c "import torch; print(torch.version.cuda)" > "%TMP_CUDA%" 2>nul
set "CUDA_VER="
if exist "%TMP_CUDA%" (
    set /p CUDA_VER=<"%TMP_CUDA%"
    del "%TMP_CUDA%" >nul 2>nul
)

if "!TORCH_VER!"=="" set "TORCH_VER=(not detected)"
if "!CUDA_VER!"=="" set "CUDA_VER=(not detected)"

echo   PyTorch: !TORCH_VER!
echo   CUDA:    !CUDA_VER!

echo !TORCH_VER! | findstr /b "2.8" >nul
if errorlevel 1 (
    echo   [WARN]   Expected PyTorch 2.8.x - the pre-built rasterizer wheel won't match.
    set "BASELINE_OK=0"
)

if not "!CUDA_VER!"=="12.8" (
    echo   [WARN]   Expected CUDA 12.8 - the pre-built rasterizer wheel won't match.
    set "BASELINE_OK=0"
)

if "!BASELINE_OK!"=="0" (
    echo.
    echo Your environment does not match the recommended baseline.
    echo The rasterizer kernel will fall back to JIT compilation, which needs
    echo Visual Studio Build Tools with the C++ workload installed.
    echo.
    echo Recommended: use ComfyUI Easy Install with Python 3.12 + PyTorch 2.8 + CUDA 12.8
    echo Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo.
    set /p CONTINUE="Continue anyway? (y/N): "
    if /i not "!CONTINUE!"=="y" exit /b 1
    echo.
) else (
    echo   [OK]     Environment matches the recommended baseline.
    echo.
)

REM ---- 3. Install AeroX node ------------------------------------------------

echo [STEP 2/5] Installing AeroX Texture Projection node...
echo.

pushd "%BASE%\ComfyUI\custom_nodes"

if exist "%AEROX_FOLDER%" (
    echo [INFO] %AEROX_FOLDER% already exists - updating to latest...
    pushd "%AEROX_FOLDER%"
    git fetch origin
    set "REMOTE_HEAD="
    for /f "delims=" %%B in ('git symbolic-ref refs/remotes/origin/HEAD --short 2^>nul') do set "REMOTE_HEAD=%%B"
    if not defined REMOTE_HEAD set "REMOTE_HEAD=origin/main"
    git reset --hard !REMOTE_HEAD!
    if errorlevel 1 (
        echo [WARNING] Could not update - keeping current state.
    ) else (
        echo [OK] Updated to latest !REMOTE_HEAD!.
    )
    popd
) else (
    git clone %AEROX_REPO% %AEROX_FOLDER%
    if errorlevel 1 (
        echo [ERROR] Failed to clone %AEROX_REPO%
        popd
        pause
        exit /b 1
    )
)

popd
echo [OK] AeroX node installed.
echo.

REM ---- 4. Install dependencies + pre-built rasterizer wheel -----------------
REM   --no-deps on requirements.txt prevents trimesh's loose numpy^>=1.20
REM   from upgrading numpy to 2.x and breaking other ComfyUI nodes.

echo [STEP 3/5] Installing dependencies and rasterizer wheel...
echo.

REM Python deps from requirements.txt
if exist "%BASE%\ComfyUI\custom_nodes\%AEROX_FOLDER%\requirements.txt" (
    echo Installing Python requirements...
    "%PYTHON%" -m pip install -r "%BASE%\ComfyUI\custom_nodes\%AEROX_FOLDER%\requirements.txt" --no-deps
    if errorlevel 1 (
        echo [WARNING] Some AeroX requirements failed - check log above.
    )
) else (
    echo [INFO] No requirements.txt found - skipping Python deps.
)

echo.

REM Pre-built rasterizer wheel (the fix for the import error)
REM   The wheel filename in the repo doesn't follow PEP 427 (too many
REM   hyphen-separated parts), so pip rejects it directly. We copy it
REM   to a temp location with a valid name and install from there.

set "WHEEL_DIR=%BASE%\ComfyUI\custom_nodes\%AEROX_FOLDER%\wheels"
set "ORIGINAL_WHEEL="
for %%W in ("%WHEEL_DIR%\%RASTERIZER_WHEEL_PATTERN%") do set "ORIGINAL_WHEEL=%%~fW"
set "RENAMED_WHEEL=%TEMP%\custom_rasterizer-0.1-cp312-cp312-win_amd64.whl"

if defined ORIGINAL_WHEEL (
    echo Installing pre-built rasterizer wheel...
    echo   !ORIGINAL_WHEEL!

    copy "!ORIGINAL_WHEEL!" "%RENAMED_WHEEL%" >nul

    "%PYTHON%" -m pip install "%RENAMED_WHEEL%" --force-reinstall --no-deps
    if errorlevel 1 (
        echo [WARNING] Rasterizer wheel install failed.
        echo           The node will try to JIT-compile on first ComfyUI launch.
        echo           If that fails, install Visual Studio Build Tools.
    ) else (
        echo [OK] Rasterizer wheel installed - no compilation needed.
    )

    del "%RENAMED_WHEEL%" >nul 2>nul
) else (
    echo [WARNING] No matching pre-built rasterizer wheel found in:
    echo           %WHEEL_DIR%
    echo           ^(pattern: %RASTERIZER_WHEEL_PATTERN%^)
    echo           The node will try to JIT-compile on first ComfyUI launch.
    echo           If that fails, install Visual Studio Build Tools.
)

echo.

REM ---- 5. CuMesh for the CuMesh UV Unwrap node ------------------------------
REM   CuMesh is a compiled CUDA python package, NOT a custom node - cloning it
REM   into custom_nodes does nothing. Pre-built wheels ship inside
REM   ComfyUI-Trellis2 (wheels\Windows\Torch280, cp311 + cp312), so we install
REM   from there first. Only if no wheel matches do we clone the visualbruno
REM   fork and compile from source (needs VS Build Tools + CUDA Toolkit).
REM   Both paths use --no-deps: only cumesh itself is installed, nothing else
REM   in the environment (numpy, torch, etc.) is touched.

echo [STEP 4/5] Installing CuMesh ^(UV Unwrap node dependency^)...
echo.

"%PYTHON%" -c "import cumesh" >nul 2>nul
if not errorlevel 1 (
    echo [OK] cumesh already importable - skipping.
    goto CUMESH_DONE
)

REM 5a. Try the pre-built wheel from ComfyUI-Trellis2
set "CUMESH_WHEEL="
for %%W in ("%BASE%\%CUMESH_WHEEL_DIR_REL%\%CUMESH_WHEEL_PATTERN%") do set "CUMESH_WHEEL=%%~fW"

if defined CUMESH_WHEEL (
    echo Installing pre-built CuMesh wheel from ComfyUI-Trellis2...
    echo   !CUMESH_WHEEL!
    "%PYTHON%" -m pip install "!CUMESH_WHEEL!" --no-deps
    if not errorlevel 1 goto CUMESH_VERIFY
    echo [WARNING] Wheel install failed - falling back to source build.
    echo.
) else (
    echo [INFO] No pre-built cumesh wheel found in:
    echo        %BASE%\%CUMESH_WHEEL_DIR_REL%
    echo        ^(pattern: %CUMESH_WHEEL_PATTERN%^)
    echo        Falling back to source build.
    echo.
)

REM 5b. Source build from the visualbruno fork (--recursive: has submodules)
echo Building CuMesh from source - this needs VS Build Tools ^(C++ workload^)
echo and a CUDA Toolkit install, and can take several minutes...
set "CUMESH_SRC=%TEMP%\CuMesh-src"
if exist "%CUMESH_SRC%" rmdir /s /q "%CUMESH_SRC%"
git clone --recursive %CUMESH_REPO% "%CUMESH_SRC%"
if errorlevel 1 (
    echo [WARNING] Failed to clone %CUMESH_REPO%
    echo           The CuMesh UV Unwrap node will not work.
    goto CUMESH_DONE
)
"%PYTHON%" -m pip install "%CUMESH_SRC%" --no-build-isolation --no-deps
if errorlevel 1 (
    echo [WARNING] CuMesh source build failed.
    echo           Install Visual Studio Build Tools ^(C++ workload^) and the
    echo           CUDA Toolkit 12.8, then re-run this script.
    goto CUMESH_DONE
)

:CUMESH_VERIFY
"%PYTHON%" -c "import cumesh" >nul 2>nul
if errorlevel 1 (
    echo [WARNING] cumesh installed but 'import cumesh' still fails.
    echo           Check the pip output above; the UV Unwrap node may not load.
) else (
    echo [OK] cumesh installed and importable.
)

:CUMESH_DONE
echo.

REM ---- 6. NVIDIA VFX (nvvfx) for RTX Video Super Resolution -----------------
REM   ComfyUI Manager pulls nvidia-vfx as a source tarball from PyPI and tries
REM   to compile it, which fails silently in the embedded Python. NVIDIA's own
REM   index ships proper wheels, so we install from there with --no-build-isolation.
REM   Non-blocking: a failure here only affects the RTX nodes, not Texture Projection.

echo [STEP 5/5] Installing NVIDIA VFX SDK ^(nvvfx^)...
echo.

if not "%INSTALL_NVVFX%"=="1" (
    echo [INFO] INSTALL_NVVFX is off - skipping.
    goto NVVFX_DONE
)

"%PYTHON%" -c "import nvvfx" >nul 2>nul
if not errorlevel 1 (
    echo [OK] nvvfx already importable - skipping.
    goto NVVFX_DONE
)

echo Installing nvidia-vfx from https://pypi.nvidia.com ...
"%PYTHON%" -m pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com
if errorlevel 1 (
    echo [WARNING] nvidia-vfx install failed. RTX Video Super Resolution nodes
    echo           will not load, but Texture Projection is unaffected.
    goto NVVFX_DONE
)

"%PYTHON%" -c "import nvvfx" >nul 2>nul
if errorlevel 1 (
    echo [WARNING] nvidia-vfx installed but 'import nvvfx' still fails.
    echo           Check the pip output above; RTX nodes may not load.
) else (
    echo [OK] nvvfx installed and importable.
)

:NVVFX_DONE
echo.

REM ---- 7. Done --------------------------------------------------------------

echo ============================================================================
echo   INSTALL COMPLETE
echo ============================================================================
echo.
echo Next steps:
echo   1. Close ComfyUI if it is running, then start it again with run_nvidia_gpu.bat
echo   2. Download the workflow JSONs from:
echo        https://pixel-artistry.com/TextureProjectionWorkflows
echo   3. Load the workflow in ComfyUI and follow the guide box INSIDE it to download:
echo        - FLUX.2 klein 9B (GGUF, ~5-6 GB)
echo        - FLUX.2 VAE
echo        - FLUX.2 Mistral text encoders (NOT the FLUX.1 ones)
echo        - Albedo Projection LoRA
echo   4. Drop in your input image (or GLB) and hit Queue
echo.
echo If you hit issues:
echo   - "rasterizer kernel" error: install Visual Studio Build Tools (C++ workload)
echo     https://visualstudio.microsoft.com/visual-cpp-build-tools/
echo   - Confirm all model files are in the folders the workflow guide specifies
echo   - Make sure the clip folder has the FLUX.2 Mistral encoder, not FLUX.1
echo   - "No module named 'cumesh'" / CuMesh UV Unwrap node missing: re-run this
echo     script with ComfyUI closed; if the source build kicked in, it needs
echo     VS Build Tools ^(C++ workload^) + CUDA Toolkit 12.8
echo   - "No module named 'nvvfx'": re-run this script with ComfyUI closed, or run
echo     python_embeded\python.exe -m pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com
echo   - Paste the last 30 lines of this log into the YouTube comments
echo.
echo Workflows + troubleshooting: https://pixel-artistry.com/TextureProjectionWorkflows
echo.

pause
endlocal
