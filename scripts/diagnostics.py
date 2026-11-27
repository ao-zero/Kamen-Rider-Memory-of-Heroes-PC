# SPDX-License-Identifier: GPL-2.0-or-later
"""
Diagnostic Bundle Exporter for Kamen Rider: Memory of Heroes PC Native Edition.
Packages system specs, launcher settings, engine config, imgui overlay config,
session stats, and recent logs into a single shareable .zip archive.
"""

import datetime
import json
import zipfile
from pathlib import Path


def export_diagnostic_bundle(
    base_dir: Path,
    dest_zip: Path,
    hardware_info: dict,
    current_version: str,
    game_dir: Path,
) -> dict:
    """Create a diagnostic .zip archive at dest_zip. Returns {success, path, count, message}."""
    base_dir = Path(base_dir)
    dest_zip = Path(dest_zip)
    game_dir = Path(game_dir)

    try:
        dest_zip.parent.mkdir(parents=True, exist_ok=True)
        eboot = game_dir / "eboot.bin"
        eboot_status = (
            f"FOUND ({round(eboot.stat().st_size / (1024 * 1024), 2)} MB)"
            if eboot.is_file()
            else "MISSING"
        )

        hw = hardware_info or {}
        vram = f" ({hw.get('vram_gb')} GB VRAM)" if hw.get("vram_gb") else ""
        specs_lines = [
            "======================================================================",
            " KAMEN RIDER: MEMORY OF HEROES — PC NATIVE EDITION DIAGNOSTIC REPORT",
            "======================================================================",
            f"Generated At       : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Launcher Version   : {current_version}",
            f"Game Directory     : {game_dir}",
            f"eboot.bin Status   : {eboot_status}",
            "----------------------------------------------------------------------",
            f"CPU                : {hw.get('cpu', 'Unknown')}",
            f"GPU                : {hw.get('gpu', 'Unknown')}{vram}",
            f"RAM                : {hw.get('ram_gb', 0)} GB",
            f"Operating System   : {hw.get('os', 'Windows')}",
            f"Disk Space         : {hw.get('disk_free', 'Unknown')}",
            f"Recommended Preset : {hw.get('recommended', 'Unknown')}",
            "======================================================================",
        ]

        candidates = [
            (base_dir / "launcher.ini", "launcher.ini"),
            (base_dir / "bin" / "user" / "config.json", "engine_config.json"),
            (base_dir / "bin" / "user" / "imgui.ini", "imgui.ini"),
            (base_dir / "bin" / "user" / "session_stats.json", "session_stats.json"),
            (base_dir / "bin" / "user" / "log" / "last_session.log", "logs/last_session.log"),
            (base_dir / "bin" / "user" / "log" / "shadps4.log", "logs/shadps4.log"),
        ]

        included = ["system_specs.txt"]
        with zipfile.ZipFile(dest_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("system_specs.txt", "\n".join(specs_lines) + "\n")
            for src, arcname in candidates:
                if src.is_file():
                    try:
                        zf.write(src, arcname=arcname)
                        included.append(arcname)
                    except Exception:
                        pass
            manifest = {
                "version": current_version,
                "files": included,
                "hardware": hw,
            }
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))

        size_kb = round(dest_zip.stat().st_size / 1024, 1)
        return {
            "success": True,
            "path": str(dest_zip),
            "count": len(included),
            "message": f"Diagnostic bundle exported ({len(included)} files, {size_kb} KB): {dest_zip.name}",
        }
    except Exception as e:
        return {
            "success": False,
            "path": "",
            "count": 0,
            "message": f"Failed to export diagnostic bundle: {e}",
        }
