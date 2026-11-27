# SPDX-License-Identifier: GPL-2.0-or-later
"""
Playtime & Last Session Tracker for Kamen Rider: Memory of Heroes PC Native Edition.
Persists total playtime, session count, last played timestamp, and exit status to
bin/user/session_stats.json.
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path


def _stats_path(base_dir: Path) -> Path:
    return Path(base_dir) / "bin" / "user" / "session_stats.json"


def _atomic_write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def load_stats(base_dir: Path) -> dict:
    p = _stats_path(base_dir)
    default = {
        "total_seconds": 0,
        "sessions": 0,
        "last_played_ts": 0,
        "last_duration_sec": 0,
        "last_exit_code": None,
    }
    if not p.is_file():
        return default
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
        default.update(raw)
        return default
    except Exception:
        return default


def record_session(base_dir: Path, duration_sec: float, exit_code: int) -> dict:
    stats = load_stats(base_dir)
    dur = max(0, int(round(duration_sec)))
    stats["total_seconds"] = int(stats.get("total_seconds", 0)) + dur
    stats["sessions"] = int(stats.get("sessions", 0)) + 1
    stats["last_played_ts"] = int(time.time())
    stats["last_duration_sec"] = dur
    stats["last_exit_code"] = int(exit_code) if exit_code is not None else 0
    _atomic_write_json(_stats_path(base_dir), stats)
    return format_stats(stats)


def _format_duration(sec: int) -> str:
    if sec < 60:
        return f"{sec}s"
    mins = sec // 60
    if mins < 60:
        return f"{mins}m"
    hours = sec / 3600.0
    return f"{hours:.1f}h"


def _format_relative(ts: int) -> str:
    if not ts:
        return "Never"
    diff = max(0, int(time.time()) - int(ts))
    if diff < 60:
        return "Just now"
    if diff < 3600:
        return f"{diff // 60}m ago"
    if diff < 86400:
        return f"{diff // 3600}h ago"
    days = diff // 86400
    if days == 1:
        return "Yesterday"
    if days < 14:
        return f"{days}d ago"
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def format_stats(stats: dict) -> dict:
    total_sec = int(stats.get("total_seconds", 0))
    last_ts = int(stats.get("last_played_ts", 0))
    last_dur = int(stats.get("last_duration_sec", 0))
    code = stats.get("last_exit_code")
    sessions = int(stats.get("sessions", 0))

    if sessions == 0:
        playtime_text = "0m played"
        last_result = "Ready to launch"
        last_when = "Never played yet"
    else:
        playtime_text = f"{_format_duration(total_sec)} played"
        if code in (0, None, -15, 1, 3221225786):
            # Normal close or user window close on Windows
            last_result = f"Exited cleanly · ran {_format_duration(last_dur)}"
        else:
            last_result = f"Exit code {code} · ran {_format_duration(last_dur)}"
        last_when = _format_relative(last_ts)

    return {
        "total_seconds": total_sec,
        "sessions": sessions,
        "playtime_text": playtime_text,
        "last_played_text": last_when,
        "last_result": last_result,
    }


def get_formatted_stats(base_dir: Path) -> dict:
    return format_stats(load_stats(base_dir))
