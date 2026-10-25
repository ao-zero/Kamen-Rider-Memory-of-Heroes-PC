# SPDX-License-Identifier: GPL-2.0-or-later
"""
Kamen Rider: Memory of Heroes - Smart PKG Installer Module
Author / Lead: AO Zero
Community: Bakka Sub (https://www.bakkasub.my.id)
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent

def _find_pkg_extractor(base: Path) -> Path:
    candidates = [
        base / "ShadPs4Plus-PkgExtractor-1.1-windows" / "pkg_extractor.exe",
        base / "bin" / "pkg_extractor.exe",
        base / "pkg_extractor.exe",
    ]
    for c in candidates:
        if c.is_file():
            return c
    raise FileNotFoundError(f"pkg_extractor.exe tidak ditemukan di: {candidates[0]}")

def inspect_pkg(pkg_path: Path) -> dict:
    """Check PKG type: 101=base, 102=update/patch, 103=dlc"""
    base = get_base_dir()
    pkg_extractor = _find_pkg_extractor(base)
        
    cmd = [str(pkg_extractor), str(pkg_path), "--check-type"]
    flags = 0x08000000 if sys.platform == "win32" else 0
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=str(base), creationflags=flags)
    code = p.returncode
    category_map = {
        101: "BASE_GAME (Game Pokok)",
        102: "GAME_UPDATE (Update Patch v1.01)",
        103: "DLC_ADDON (Konten Tambahan DLC)"
    }
    return {
        "code": code,
        "type": category_map.get(code, f"UNKNOWN (Kode: {code})"),
        "stdout": p.stdout.strip()
    }

def extract_and_merge_update(pkg_path: Path, target_game_dir: Path, progress_callback=None) -> bool:
    """Extract update pkg and merge over target base game directory."""
    base = get_base_dir()
    pkg_extractor = _find_pkg_extractor(base)

    temp_extract = base / "_temp_update_extract"
    temp_extract.mkdir(parents=True, exist_ok=True)
    try:
        if progress_callback:
            progress_callback(f"[EKSTRAKSI] Memulai ekstraksi paket {pkg_path.name}...")
        cmd = [str(pkg_extractor), str(pkg_path), str(temp_extract)]
        flags = 0x08000000 if sys.platform == "win32" else 0
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(base),
            creationflags=flags
        )
        for line in process.stdout:
            line_str = line.strip()
            if line_str and progress_callback:
                if any(k in line_str.lower() for k in ["extracting", "open", "file", "progress", "done"]):
                    progress_callback(line_str)
        process.wait()
        if process.returncode != 0:
            raise RuntimeError(f"Gagal mengekstrak PKG: kode keluar {process.returncode}")
        
        # Find extracted patch directory
        patch_dirs = [p for p in temp_extract.iterdir() if p.is_dir() and "patch" in p.name.lower()]
        if not patch_dirs:
            patch_dirs = [p for p in temp_extract.iterdir() if p.is_dir()]
        if not patch_dirs:
            raise FileNotFoundError("Direktori hasil ekstraksi patch tidak ditemukan!")
        
        patch_dir = patch_dirs[0]
        if progress_callback:
            progress_callback(f"[MERGE] Menggabungkan file patch {patch_dir.name} ke folder game {target_game_dir.name}...")
        
        # Merge patch files over target_game_dir
        for src_path in patch_dir.rglob("*"):
            rel = src_path.relative_to(patch_dir)
            dest_path = target_game_dir / rel
            if src_path.is_dir():
                dest_path.mkdir(parents=True, exist_ok=True)
            else:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dest_path)
                
        if progress_callback:
            progress_callback("[SELESAI] Patch update berhasil digabungkan ke data game!")
        return True
    finally:
        shutil.rmtree(temp_extract, ignore_errors=True)

if __name__ == "__main__":
    base = get_base_dir()
    test_pkg = base / "[PS4ID]-KAMEN.RIDER.memory.of.heroez.update.v1.01bp-CUSA17374.pkg"
    info = inspect_pkg(test_pkg)
    print("PKG Info:", info)
