# SPDX-License-Identifier: GPL-2.0-or-later
"""
Custom Savegame Manager for Kamen Rider: Memory of Heroes (CUSA17374)
Handles save slot discovery, timestamped backups, instant restore, 100% preset installation, and folder explorer.
"""

import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

def get_save_dir(base_dir: Path) -> Path:
    return base_dir / "bin" / "user" / "home" / "1000" / "savedata" / "CUSA17374"

def get_backup_dir(base_dir: Path) -> Path:
    bdir = base_dir / "saves_backup"
    bdir.mkdir(parents=True, exist_ok=True)
    return bdir

def get_save_slots(base_dir: Path) -> list:
    """List all detected save slots for CUSA17374."""
    sdir = get_save_dir(base_dir)
    if not sdir.exists():
        return []

    slots = []
    # Known folders in KR Memory of Heroes
    friendly_names = {
        "KmrSave": "System Settings & Profile Save",
        "KmrSaveGame0": "Story Progress — Slot 1",
        "KmrSaveGame1": "Story Progress — Slot 2",
        "KmrSaveGame2": "Story Progress — Slot 3",
        "KmrSaveGame3": "Story Progress — Slot 4",
        "KmrSaveGame4": "Story Progress — Slot 5",
        "KmrSaveGame5": "Story Progress — Slot 6",
        "KmrSaveGame6": "Autosave / Checkpoint",
    }

    for item in sorted(sdir.iterdir()):
        if item.is_dir():
            # Calculate total size
            total_bytes = sum(f.stat().st_size for f in item.glob("**/*") if f.is_file())
            mtime = datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            slots.append({
                "folder": item.name,
                "title": friendly_names.get(item.name, item.name),
                "size_kb": round(total_bytes / 1024, 1),
                "last_modified": mtime,
                "has_data": (item / "KmrSaveGame").is_file() or (item / "KmrSaveSys").is_file()
            })
    return slots

def backup_saves(base_dir: Path) -> dict:
    """Create a compressed timestamped zip backup of all saves."""
    sdir = get_save_dir(base_dir)
    bdir = get_backup_dir(base_dir)
    
    if not sdir.exists() or not any(sdir.iterdir()):
        return {"success": False, "message": "No active save data found to backup."}

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"KR_SaveBackup_{timestamp}.zip"
    zip_path = bdir / zip_name

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(sdir):
            for f in files:
                full_path = Path(root) / f
                rel_path = full_path.relative_to(sdir)
                zf.write(full_path, arcname=str(rel_path))

    return {
        "success": True,
        "filename": zip_name,
        "message": f"Backup created successfully: {zip_name} ({round(zip_path.stat().st_size / 1024, 1)} KB)"
    }

def list_backups(base_dir: Path) -> list:
    """List all available backup zip archives."""
    bdir = get_backup_dir(base_dir)
    backups = []
    for f in sorted(bdir.glob("*.zip"), key=lambda x: x.stat().st_mtime, reverse=True):
        mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        backups.append({
            "name": f.name,
            "path": str(f),
            "size_kb": round(f.stat().st_size / 1024, 1),
            "date": mtime
        })
    return backups

def restore_backup(base_dir: Path, zip_name: str) -> dict:
    """Restore savegame from selected backup zip."""
    bdir = get_backup_dir(base_dir)
    zip_path = bdir / zip_name
    sdir = get_save_dir(base_dir)

    if not zip_path.is_file():
        return {"success": False, "message": f"Backup file not found: {zip_name}"}

    try:
        # Create safety backup of current saves first
        backup_saves(base_dir)
        
        # Purge existing save directories in sdir to avoid corrupted slot mixing
        if sdir.exists():
            for item in sdir.iterdir():
                try:
                    if item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                    elif item.is_file():
                        item.unlink(missing_ok=True)
                except Exception:
                    pass
        sdir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(sdir)

        return {"success": True, "message": f"Successfully restored saves from: {zip_name}"}
    except Exception as e:
        return {"success": False, "message": f"Failed to restore backup: {e}"}

def install_100_percent_preset(base_dir: Path) -> dict:
    """Install 100% unlocked savegame preset into Slot 1."""
    sdir = get_save_dir(base_dir)
    slot1_dir = sdir / "KmrSaveGame0"
    
    preset_candidates = [
        base_dir / "assets" / "presets" / "100_percent_save",
        base_dir / "assets" / "presets" / "KmrSaveGame0",
        base_dir / "assets" / "presets" / "100_percent_save.zip"
    ]
    
    source = None
    is_zip = False
    for cand in preset_candidates:
        if cand.is_file() and cand.suffix.lower() == ".zip":
            source = cand
            is_zip = True
            break
        elif cand.is_dir() and any(cand.iterdir()):
            source = cand
            break

    if not source:
        presets_dir = base_dir / "assets" / "presets"
        presets_dir.mkdir(parents=True, exist_ok=True)
        return {
            "success": False,
            "message": "No 100% save preset found in assets/presets. You can place completed save files into assets/presets/100_percent_save or restore from a backup."
        }

    # First create a backup of current saves
    backup_saves(base_dir)
    slot1_dir.mkdir(parents=True, exist_ok=True)

    try:
        if is_zip:
            with zipfile.ZipFile(source, "r") as zf:
                zf.extractall(slot1_dir)
        else:
            for f in source.rglob("*"):
                rel = f.relative_to(source)
                dest = slot1_dir / rel
                if f.is_dir():
                    dest.mkdir(parents=True, exist_ok=True)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, dest)
        return {"success": True, "message": "100% Completed Save Preset applied to Slot 1 (Backed up existing saves)."}
    except Exception as e:
        return {"success": False, "message": f"Failed to apply preset: {e}"}

def open_saves_folder(base_dir: Path) -> str:
    sdir = get_save_dir(base_dir)
    sdir.mkdir(parents=True, exist_ok=True)
    os.startfile(str(sdir))
    return str(sdir)
