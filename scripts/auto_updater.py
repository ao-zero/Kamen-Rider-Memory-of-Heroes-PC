# SPDX-License-Identifier: GPL-2.0-or-later
"""
True 1-Click Auto-Updater for Kamen Rider: Memory of Heroes PC Native Edition.
Checks GitHub Releases, streams the latest portable ZIP with progress callbacks,
verifies archive integrity, and launches a safe Windows self-replace script that
NEVER touches CUSA17374/, savedata/, vanilla_backup/, saves_backup/, or launcher.ini.
"""

import os
import re
import sys
import json
import shutil
import zipfile
import subprocess
import urllib.request
from pathlib import Path
from typing import Callable, Optional

REPO_SLUG = "ao-zero/Kamen-Rider-Memory-of-Heroes-PC"
RELEASES_API = f"https://api.github.com/repos/{REPO_SLUG}/releases/latest"
RELEASES_URL = f"https://github.com/{REPO_SLUG}/releases"
USER_AGENT = "KR-Memory-of-Heroes-Launcher/1.3.0"


def parse_version(raw: str) -> tuple[int, int, int]:
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", str(raw or ""))
    if not m:
        return (0, 0, 0)
    return tuple(int(x) for x in m.groups())


def check_for_updates(current_version: str) -> dict:
    """Query GitHub Releases API and return release metadata including ZIP download URL."""
    try:
        req = urllib.request.Request(RELEASES_API, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        latest_tag = data.get("tag_name", current_version)
        is_up_to_date = parse_version(latest_tag) <= parse_version(current_version)

        download_url = ""
        asset_name = ""
        asset_size_mb = 0.0
        for asset in data.get("assets", []):
            name = asset.get("name", "")
            if name.lower().endswith(".zip"):
                download_url = asset.get("browser_download_url", "")
                asset_name = name
                asset_size_mb = round(asset.get("size", 0) / (1024 * 1024), 1)
                break

        return {
            "success": True,
            "current": current_version,
            "latest": latest_tag,
            "up_to_date": is_up_to_date,
            "url": data.get("html_url", RELEASES_URL),
            "download_url": download_url,
            "asset_name": asset_name,
            "asset_size_mb": asset_size_mb,
            "notes": (data.get("body") or "").strip()[:1200],
        }
    except Exception as e:
        return {
            "success": False,
            "current": current_version,
            "latest": current_version,
            "up_to_date": True,
            "url": RELEASES_URL,
            "download_url": "",
            "asset_name": "",
            "asset_size_mb": 0.0,
            "notes": f"Could not reach update server: {e}",
        }


def _safe_extract_zip(zip_path: Path, dest_dir: Path):
    dest_resolved = dest_dir.resolve()
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            target = (dest_dir / member.filename).resolve()
            if not str(target).startswith(str(dest_resolved)):
                raise ValueError(f"Blocked unsafe zip path: {member.filename}")
        zf.extractall(dest_dir)


def _find_extracted_root(extracted_dir: Path) -> Path:
    """Locate the folder containing Kamen Rider Memory of Heroes.exe inside extracted ZIP."""
    if (extracted_dir / "Kamen Rider Memory of Heroes.exe").is_file():
        return extracted_dir
    for child in extracted_dir.iterdir():
        if child.is_dir() and (child / "Kamen Rider Memory of Heroes.exe").is_file():
            return child
    raise FileNotFoundError("Updated executable 'Kamen Rider Memory of Heroes.exe' not found inside release archive.")


def build_apply_update_script(
    base_dir: Path,
    src_root: Path,
    temp_dir: Path,
    pid: int,
) -> Path:
    """Generate a safe Windows batch helper that replaces launcher files while preserving user data."""
    bat_path = temp_dir / "apply_update.bat"
    exe_name = "Kamen Rider Memory of Heroes.exe"

    # Explicitly copy ONLY launcher/runtime files; NEVER touch CUSA17374, savedata, vanilla_backup, saves_backup, launcher.ini
    script = f"""@echo off
title Updating Kamen Rider: Memory of Heroes Launcher...
echo ===============================================================
echo   Applying Kamen Rider: Memory of Heroes PC Native Update
echo ===============================================================
echo Waiting for launcher (PID {pid}) to exit...

set /a tries=0
:waitloop
tasklist /FI "PID eq {pid}" 2>nul | find "{pid}" >nul
if %errorlevel%==0 (
    set /a tries+=1
    if %tries% GEQ 20 goto forcekill
    timeout /t 1 /nobreak >nul
    goto waitloop
)
goto docopy

:forcekill
taskkill /PID {pid} /F >nul 2>&1
timeout /t 1 /nobreak >nul

:docopy
echo Copying updated launcher files (preserving CUSA17374, saves, and launcher.ini)...
copy /Y "{src_root}\\{exe_name}" "{base_dir}\\{exe_name}" >nul
if exist "{src_root}\\ui" xcopy /E /I /Y "{src_root}\\ui" "{base_dir}\\ui" >nul
if exist "{src_root}\\scripts" xcopy /E /I /Y "{src_root}\\scripts" "{base_dir}\\scripts" >nul
if exist "{src_root}\\patches" xcopy /E /I /Y "{src_root}\\patches" "{base_dir}\\patches" >nul
if exist "{src_root}\\assets" xcopy /E /I /Y "{src_root}\\assets" "{base_dir}\\assets" >nul
if exist "{src_root}\\README.txt" copy /Y "{src_root}\\README.txt" "{base_dir}\\README.txt" >nul

REM Update bin runtime binaries WITHOUT touching bin\\user (saves/config/vanilla_backup)
if exist "{src_root}\\bin" (
    for %%F in ("{src_root}\\bin\\*.exe" "{src_root}\\bin\\*.dll") do (
        copy /Y "%%~fF" "{base_dir}\\bin\\%%~nxF" >nul 2>&1
    )
)

echo Launching updated version...
start "" "{base_dir}\\{exe_name}"

REM Self-cleanup temporary update directory
timeout /t 2 /nobreak >nul
rmdir /S /Q "{temp_dir}" >nul 2>&1
exit /b 0
"""
    bat_path.write_text(script, encoding="utf-8")
    return bat_path


def download_and_prepare_update(
    download_url: str,
    base_dir: Path,
    progress_cb: Optional[Callable[[int, float, float, str], None]] = None,
) -> dict:
    """
    Download release ZIP with live progress callbacks, extract & verify,
    and prepare the self-replace script.
    progress_cb(percent, downloaded_mb, total_mb, stage_text)
    """
    if not download_url:
        return {"success": False, "message": "No downloadable ZIP asset found in this GitHub release."}

    temp_dir = Path(base_dir) / "_temp_update"
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    zip_path = temp_dir / "release_update.zip"
    extracted_dir = temp_dir / "extracted"

    try:
        if progress_cb:
            progress_cb(0, 0.0, 0.0, "Connecting to GitHub Releases...")

        req = urllib.request.Request(download_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as resp:
            total_bytes = int(resp.headers.get("Content-Length") or 0)
            total_mb = round(total_bytes / (1024 * 1024), 1) if total_bytes else 0.0
            downloaded = 0
            last_pct = -1

            with open(zip_path, "wb") as out_f:
                while True:
                    chunk = resp.read(256 * 1024)
                    if not chunk:
                        break
                    out_f.write(chunk)
                    downloaded += len(chunk)
                    dl_mb = round(downloaded / (1024 * 1024), 1)
                    pct = int((downloaded * 100) / total_bytes) if total_bytes > 0 else 50
                    if pct != last_pct:
                        last_pct = pct
                        if progress_cb:
                            progress_cb(min(95, pct), dl_mb, total_mb, f"Downloading... {dl_mb} / {total_mb} MB")

        if progress_cb:
            progress_cb(96, total_mb, total_mb, "Extracting update archive...")

        extracted_dir.mkdir(parents=True, exist_ok=True)
        _safe_extract_zip(zip_path, extracted_dir)
        src_root = _find_extracted_root(extracted_dir)

        if progress_cb:
            progress_cb(99, total_mb, total_mb, "Preparing installer & restarting launcher...")

        bat_path = build_apply_update_script(Path(base_dir), src_root, temp_dir, os.getpid())
        return {
            "success": True,
            "bat_path": str(bat_path),
            "message": "Update downloaded and verified. Restarting launcher to apply update...",
        }
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return {"success": False, "message": f"Auto-update failed: {e}"}


def launch_updater_script(bat_path: str):
    """Spawn the detached update script on Windows."""
    if sys.platform == "win32":
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        subprocess.Popen(["cmd.exe", "/c", bat_path], creationflags=flags, close_fds=True)
