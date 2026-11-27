# SPDX-License-Identifier: GPL-2.0-or-later
"""
Built-in Indonesian Subtitle Patcher for Kamen Rider: Memory of Heroes (CUSA17374)
Pure-Python Unity 2017.4.40f1 SerializedFile Patcher (Zero External Dependencies)
Project Lead: AO Zero | Community Partner: Bakka Sub (https://www.bakkasub.my.id)

Safely patches Media/sharedassets0.assets MonoBehaviour localization tables:
  - path_id 351: help_list     (tutorials, form/item help)
  - path_id 353: menu_text     (UI menus, skills, descriptions, system text)
  - path_id 358: mission_talk  (story & in-game dialogue subtitles)
  - path_id 359: name_text     (character, Rider, form, and enemy names)

Always maintains an untouched vanilla backup in bin/user/vanilla_backup/ so the
user can toggle between Bahasa Indonesia (Bakka Sub) and Original (EN/JP) anytime.
"""

import os
import json
import struct
import shutil
import hashlib
from pathlib import Path
from typing import Callable, Optional


TARGET_REL = Path("Media") / "sharedassets0.assets"
TEXT_PATH_IDS = {
    351: "help_list",
    353: "menu_text",
    358: "mission_talk",
    359: "name_text",
}


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _align4(n: int) -> int:
    return (n + 3) & ~3


def _align8(n: int) -> int:
    return (n + 7) & ~7


def _read_u_str(buf: bytes, off: int):
    slen, = struct.unpack_from("<I", buf, off)
    off += 4
    s = buf[off:off + slen].decode("utf-8", "strict")
    off += _align4(slen)
    return s, off


def _write_u_str(out: bytearray, s: str):
    raw = s.encode("utf-8")
    out += struct.pack("<I", len(raw))
    out += raw
    pad = _align4(len(raw)) - len(raw)
    if pad:
        out += b"\x00" * pad


def _patch_kv5(buf: bytes, mapping: dict) -> tuple[bytes, int]:
    """Patch menu_text (353) or name_text (359): key + string[5]."""
    out = bytearray(buf[:28])
    name, off = _read_u_str(buf, 28)
    _write_u_str(out, name)
    count, = struct.unpack_from("<I", buf, off)
    off += 4
    out += struct.pack("<I", count)

    replaced = 0
    for _ in range(count):
        key, off = _read_u_str(buf, off)
        lcnt, = struct.unpack_from("<I", buf, off)
        off += 4
        langs = []
        for _ in range(lcnt):
            s, off = _read_u_str(buf, off)
            langs.append(s)
        if len(langs) > 1 and key in mapping and mapping[key]:
            langs[1] = mapping[key]
            replaced += 1
        _write_u_str(out, key)
        out += struct.pack("<I", len(langs))
        for s in langs:
            _write_u_str(out, s)

    if off != len(buf):
        raise ValueError(f"kv5 parse mismatch for {name}: {off} != {len(buf)}")
    return bytes(out), replaced


def _patch_mission_talk(buf: bytes, mapping: dict) -> tuple[bytes, int]:
    """Patch mission_talk (358): talk_id + speaker + uint32 + uint32 + string[5]."""
    out = bytearray(buf[:28])
    name, off = _read_u_str(buf, 28)
    _write_u_str(out, name)
    count, = struct.unpack_from("<I", buf, off)
    off += 4
    out += struct.pack("<I", count)

    replaced = 0
    for _ in range(count):
        tid, off = _read_u_str(buf, off)
        spk, off = _read_u_str(buf, off)
        f1, f2 = struct.unpack_from("<II", buf, off)
        off += 8
        lcnt, = struct.unpack_from("<I", buf, off)
        off += 4
        langs = []
        for _ in range(lcnt):
            s, off = _read_u_str(buf, off)
            langs.append(s)
        if len(langs) > 1 and tid in mapping and mapping[tid]:
            langs[1] = mapping[tid]
            replaced += 1
        _write_u_str(out, tid)
        _write_u_str(out, spk)
        out += struct.pack("<II", f1, f2)
        out += struct.pack("<I", len(langs))
        for s in langs:
            _write_u_str(out, s)

    if off != len(buf):
        raise ValueError(f"mission_talk parse mismatch: {off} != {len(buf)}")
    return bytes(out), replaced


def _patch_help_list(buf: bytes, mapping: dict) -> tuple[bytes, int]:
    """Patch help_list (351): hid + uint32 + uint32 + sub_array(skey + string[5])."""
    out = bytearray(buf[:28])
    name, off = _read_u_str(buf, 28)
    _write_u_str(out, name)
    count, = struct.unpack_from("<I", buf, off)
    off += 4
    out += struct.pack("<I", count)

    replaced = 0
    for _ in range(count):
        hid, off = _read_u_str(buf, off)
        f1, f2 = struct.unpack_from("<II", buf, off)
        off += 8
        scnt, = struct.unpack_from("<I", buf, off)
        off += 4
        _write_u_str(out, hid)
        out += struct.pack("<III", f1, f2, scnt)
        for _ in range(scnt):
            skey, off = _read_u_str(buf, off)
            lcnt, = struct.unpack_from("<I", buf, off)
            off += 4
            langs = []
            for _ in range(lcnt):
                s, off = _read_u_str(buf, off)
                langs.append(s)
            full_key = f"{hid}:{skey}"
            if len(langs) > 1 and full_key in mapping and mapping[full_key]:
                langs[1] = mapping[full_key]
                replaced += 1
            _write_u_str(out, skey)
            out += struct.pack("<I", len(langs))
            for s in langs:
                _write_u_str(out, s)

    if off != len(buf):
        raise ValueError(f"help_list parse mismatch: {off} != {len(buf)}")
    return bytes(out), replaced


def _rebuild_unity_serialized_file(raw: bytes, patch_tables: dict) -> tuple[bytes, int]:
    """
    Parse Unity 2017.4 SerializedFile (v17), patch target MonoBehaviour objects,
    and rebuild the object table + data block with updated byte_start / byte_size / file_size.
    """
    metadata_size, file_size, version, data_offset = struct.unpack_from(">IIII", raw, 0)
    if version != 17:
        raise ValueError(f"Unsupported Unity SerializedFile version: {version} (expected 17)")

    pos = 16
    endian = raw[pos]
    pos += 4
    fmt = "<" if endian == 0 else ">"

    # unity_version string
    end_str = raw.index(b"\x00", pos)
    pos = end_str + 1
    target_platform, enable_type_tree = struct.unpack_from(fmt + "i?", raw, pos)
    pos += 5
    type_count, = struct.unpack_from(fmt + "i", raw, pos)
    pos += 4

    for _ in range(type_count):
        class_id, _is_stripped, _script_idx = struct.unpack_from(fmt + "i?h", raw, pos)
        pos += 7
        if class_id == 114:
            pos += 16
        pos += 16
        if enable_type_tree:
            num_nodes, str_buf_len = struct.unpack_from(fmt + "ii", raw, pos)
            pos += 8 + num_nodes * 24 + str_buf_len

    obj_count, = struct.unpack_from(fmt + "i", raw, pos)
    pos += 4
    obj_table_start = _align4(pos)

    objects = []
    pos = obj_table_start
    for _ in range(obj_count):
        pos = _align4(pos)
        entry_off = pos
        path_id, byte_start, byte_size, type_id = struct.unpack_from(fmt + "qIII", raw, pos)
        pos += 20
        objects.append({
            "entry_off": entry_off,
            "path_id": path_id,
            "byte_start": byte_start,
            "byte_size": byte_size,
            "type_id": type_id,
        })

    # Copy header + metadata verbatim (we will patch file_size and object entries in place)
    header_meta = bytearray(raw[:data_offset])

    # Sort objects by original byte_start to preserve exact layout order
    ordered = sorted(range(len(objects)), key=lambda i: objects[i]["byte_start"])
    data_blob = bytearray()
    total_replaced = 0

    for idx in ordered:
        obj = objects[idx]
        pid = obj["path_id"]
        orig_abs = data_offset + obj["byte_start"]
        chunk = raw[orig_abs:orig_abs + obj["byte_size"]]

        if pid in TEXT_PATH_IDS:
            table_name = TEXT_PATH_IDS[pid]
            mapping = patch_tables.get(table_name, {})
            if mapping:
                if pid == 351:
                    chunk, rep = _patch_help_list(chunk, mapping)
                elif pid in (353, 359):
                    chunk, rep = _patch_kv5(chunk, mapping)
                elif pid == 358:
                    chunk, rep = _patch_mission_talk(chunk, mapping)
                else:
                    rep = 0
                total_replaced += rep

        # Align each object in data block to 8 bytes (Unity 2017.4 standard)
        aligned_start = _align8(len(data_blob))
        if aligned_start > len(data_blob):
            data_blob += b"\x00" * (aligned_start - len(data_blob))

        obj["new_byte_start"] = aligned_start
        obj["new_byte_size"] = len(chunk)
        data_blob += chunk

    # Patch ObjectInfo table in header_meta
    for obj in objects:
        struct.pack_into(
            fmt + "qIII",
            header_meta,
            obj["entry_off"],
            obj["path_id"],
            obj["new_byte_start"],
            obj["new_byte_size"],
            obj["type_id"],
        )

    new_file_size = data_offset + len(data_blob)
    struct.pack_into(">I", header_meta, 4, new_file_size)

    return bytes(header_meta) + bytes(data_blob), total_replaced


def get_backup_dir(base_dir: Path) -> Path:
    return Path(base_dir) / "bin" / "user" / "vanilla_backup"


def get_patch_file(patches_dir: Path) -> Path:
    return Path(patches_dir) / "id_patch.json"


def get_indo_patch_status(game_dir: Path, base_dir: Path, patches_dir: Path) -> dict:
    game_dir = Path(game_dir)
    base_dir = Path(base_dir)
    patch_file = get_patch_file(patches_dir)
    backup_dir = get_backup_dir(base_dir)
    target_file = game_dir / TARGET_REL
    backup_file = backup_dir / TARGET_REL
    state_file = backup_dir / "patch_state.json"

    patch_available = patch_file.is_file()
    version = "1.0.0"
    author = "AO Zero & Bakka Sub"
    translated_count = 0

    if patch_available:
        try:
            meta = json.loads(patch_file.read_text(encoding="utf-8"))
            version = meta.get("patch_version", version)
            author = meta.get("author", author)
            tables = meta.get("tables", {})
            translated_count = sum(len(v) for v in tables.values() if isinstance(v, dict))
        except Exception:
            pass

    applied = False
    if state_file.is_file():
        try:
            st = json.loads(state_file.read_text(encoding="utf-8"))
            applied = bool(st.get("applied", False))
        except Exception:
            pass

    return {
        "applied": applied and target_file.is_file(),
        "patch_available": patch_available,
        "game_found": target_file.is_file(),
        "backup_exists": backup_file.is_file(),
        "version": version,
        "author": author,
        "translated_count": translated_count,
    }


def apply_indo_patch(
    game_dir: Path,
    base_dir: Path,
    patches_dir: Path,
    progress_cb: Optional[Callable[[str], None]] = None,
) -> dict:
    def log(msg: str):
        if progress_cb:
            progress_cb(msg)

    game_dir = Path(game_dir)
    base_dir = Path(base_dir)
    patch_file = get_patch_file(patches_dir)
    target_file = game_dir / TARGET_REL
    backup_dir = get_backup_dir(base_dir)
    backup_file = backup_dir / TARGET_REL
    manifest_file = backup_dir / "vanilla_manifest.json"
    state_file = backup_dir / "patch_state.json"

    if not target_file.is_file():
        return {"success": False, "message": f"File game tidak ditemukan: {target_file}"}
    if not patch_file.is_file():
        return {"success": False, "message": f"File patch built-in tidak ditemukan: {patch_file}"}

    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_file.parent.mkdir(parents=True, exist_ok=True)

    # 1. Create untouched vanilla backup ONCE
    if not backup_file.is_file():
        log("[PATCH-ID] Membuat backup file original (vanilla) pertama kali...")
        tmp_bak = backup_file.with_suffix(".assets.tmp")
        shutil.copy2(target_file, tmp_bak)
        os.replace(tmp_bak, backup_file)
        sha = _sha256_file(backup_file)
        manifest_file.write_text(
            json.dumps({"target": str(TARGET_REL), "sha256": sha, "size": backup_file.stat().st_size}, indent=2),
            encoding="utf-8",
        )
        log(f"[PATCH-ID] Backup vanilla aman tersimpan (SHA-256: {sha[:12]}...).")

    # 2. Load patch dictionary
    log("[PATCH-ID] Memuat kamus terjemahan Bahasa Indonesia (Bakka Sub x AO Zero)...")
    patch_data = json.loads(patch_file.read_text(encoding="utf-8"))
    tables = patch_data.get("tables", {})
    version = patch_data.get("patch_version", "1.0.0")

    # 3. Always patch from pristine vanilla backup (idempotent!)
    log("[PATCH-ID] Menyuntikkan subtitle Bahasa Indonesia ke sharedassets0.assets...")
    vanilla_raw = backup_file.read_bytes()
    patched_raw, replaced_count = _rebuild_unity_serialized_file(vanilla_raw, tables)

    # 4. Atomic write to game directory
    tmp_target = target_file.with_suffix(".assets.tmp")
    tmp_target.write_bytes(patched_raw)
    os.replace(tmp_target, target_file)

    state_file.write_text(
        json.dumps({
            "applied": True,
            "version": version,
            "replaced_count": replaced_count,
        }, indent=2),
        encoding="utf-8",
    )
    log(f"[PATCH-ID] Sukses! {replaced_count} baris teks & subtitle berhasil diterjemahkan ke Bahasa Indonesia.")
    return {
        "success": True,
        "applied": True,
        "replaced_count": replaced_count,
        "version": version,
        "message": f"Patch Bahasa Indonesia v{version} aktif ({replaced_count} baris teks diterapkan)!",
    }


def restore_vanilla(
    game_dir: Path,
    base_dir: Path,
    progress_cb: Optional[Callable[[str], None]] = None,
) -> dict:
    def log(msg: str):
        if progress_cb:
            progress_cb(msg)

    game_dir = Path(game_dir)
    base_dir = Path(base_dir)
    target_file = game_dir / TARGET_REL
    backup_dir = get_backup_dir(base_dir)
    backup_file = backup_dir / TARGET_REL
    state_file = backup_dir / "patch_state.json"

    if not backup_file.is_file():
        if state_file.is_file():
            state_file.write_text(json.dumps({"applied": False}, indent=2), encoding="utf-8")
        return {
            "success": True,
            "applied": False,
            "message": "Game sudah dalam kondisi Original (EN/JP).",
        }

    if not target_file.parent.is_dir():
        return {"success": False, "message": f"Folder Media game tidak ditemukan: {target_file.parent}"}

    log("[PATCH-ID] Mengembalikan file game original (EN/JP) dari backup vanilla...")
    tmp_target = target_file.with_suffix(".assets.tmp")
    shutil.copy2(backup_file, tmp_target)
    os.replace(tmp_target, target_file)

    state_file.write_text(json.dumps({"applied": False}, indent=2), encoding="utf-8")
    log("[PATCH-ID] File game berhasil dikembalikan ke Original (EN/JP) 100% utuh.")
    return {
        "success": True,
        "applied": False,
        "message": "Subtitle game berhasil dikembalikan ke Original (EN/JP).",
    }
