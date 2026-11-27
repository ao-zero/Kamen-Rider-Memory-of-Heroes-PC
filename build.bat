@echo off
title Rebuilding Kamen Rider: Memory of Heroes Standalone Launcher
cd /d "%~dp0"

echo ==============================================================================
echo [BUILD] KAMEN RIDER: MEMORY OF HEROES - PC EDITION LAUNCHER BUILDER
echo Lead: AO Zero ^| Partner: Bakka Sub (www.bakkasub.my.id)
echo ==============================================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found in your system PATH.
    echo Please install Python 3.10+ and tick "Add Python to PATH".
    pause
    exit /b 1
)

echo [1/3] Verifying and installing required build dependencies...
python -m pip install -r requirements.txt --quiet

echo [2/3] Compiling standalone executable with PyInstaller...
python -m PyInstaller "Kamen Rider Memory of Heroes.spec" --noconfirm

if exist "dist\Kamen Rider Memory of Heroes.exe" (
    echo [3/3] Copying built binary to project root...
    copy /y "dist\Kamen Rider Memory of Heroes.exe" "Kamen Rider Memory of Heroes.exe" >nul
    echo.
    echo ==============================================================================
    echo [SUCCESS] Build completed successfully!
    echo Binary: Kamen Rider Memory of Heroes.exe
    echo ==============================================================================
) else (
    echo [ERROR] PyInstaller build failed. Check output above.
)

echo.
pause
