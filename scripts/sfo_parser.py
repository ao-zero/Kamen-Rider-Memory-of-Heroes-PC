# SPDX-License-Identifier: GPL-2.0-or-later
"""
PlayStation 4 SFO Parser
"""
import struct
from pathlib import Path

def parse_sfo(data: bytes) -> dict:
    header = struct.Struct("<4sIIII")
    entry = struct.Struct("<HHIII")
    if len(data) < header.size:
        return {}
    magic, ver, key_off, data_off, count = header.unpack_from(data, 0)
    if magic != b"\0PSF":
        return {}
    res = {}
    for i in range(count):
        pos = header.size + i * entry.size
        if pos + entry.size > len(data):
            break
        koff, fmt, used, cap, doff = entry.unpack_from(data, pos)
        kstart = key_off + koff
        kend = data.find(b"\0", kstart)
        if kend < 0:
            continue
        key = data[kstart:kend].decode("utf-8", "replace")
        val_raw = data[data_off + doff : data_off + doff + used]
        if fmt == 0x0404:
            res[key] = struct.unpack("<I", val_raw[:4])[0] if len(val_raw) >= 4 else 0
        else:
            res[key] = val_raw.decode("utf-8", "replace").rstrip("\0")
    return res

def get_game_info(game_dir: Path) -> dict:
    sfo_file = game_dir / "sce_sys" / "param.sfo"
    if sfo_file.is_file():
        return parse_sfo(sfo_file.read_bytes())
    return {}
