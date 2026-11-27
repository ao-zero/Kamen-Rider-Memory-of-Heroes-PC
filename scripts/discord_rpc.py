# SPDX-License-Identifier: GPL-2.0-or-later
r"""
Zero-Dependency Discord Rich Presence (IPC) Client for Windows.
Communicates directly with local Discord desktop client via \\.\pipe\discord-ipc-0..9.
Fails silently if Discord is not running — never blocks or crashes the launcher.
"""

import json
import os
import struct
import sys
import threading
import time
import uuid

# Standard Discord Application ID (can be overridden via launcher.ini if desired)
DEFAULT_CLIENT_ID = "1274824899621523508"


class DiscordRPC:
    def __init__(self, client_id: str = DEFAULT_CLIENT_ID):
        self.client_id = client_id
        self.enabled = True
        self._pipe = None
        self._lock = threading.Lock()
        self._connected = False

    def _send_frame(self, opcode: int, payload: dict) -> bool:
        if not self._pipe:
            return False
        try:
            data = json.dumps(payload).encode("utf-8")
            header = struct.pack("<II", opcode, len(data))
            self._pipe.write(header + data)
            self._pipe.flush()
            return True
        except Exception:
            self._close_locked()
            return False

    def _read_frame(self):
        if not self._pipe:
            return None
        try:
            hdr = self._pipe.read(8)
            if not hdr or len(hdr) < 8:
                return None
            _op, length = struct.unpack("<II", hdr)
            if length <= 0 or length > 65536:
                return None
            body = self._pipe.read(length)
            return json.loads(body.decode("utf-8", errors="ignore"))
        except Exception:
            self._close_locked()
            return None

    def _close_locked(self):
        if self._pipe:
            try:
                self._pipe.close()
            except Exception:
                pass
        self._pipe = None
        self._connected = False

    def _connect_locked(self) -> bool:
        if self._connected and self._pipe:
            return True
        if sys.platform != "win32" or not self.enabled:
            return False
        for i in range(10):
            pipe_path = rf"\\.\pipe\discord-ipc-{i}"
            try:
                f = open(pipe_path, "r+b", buffering=0)
                self._pipe = f
                if self._send_frame(0, {"v": 1, "client_id": self.client_id}):
                    _ = self._read_frame()
                    self._connected = True
                    return True
            except Exception:
                self._close_locked()
        return False

    def set_enabled(self, enabled: bool):
        self.enabled = bool(enabled)
        if not self.enabled:
            self.clear()

    def update(self, details: str, state: str, start_ts: int = None):
        if not self.enabled or sys.platform != "win32":
            return

        def _worker():
            with self._lock:
                if not self._connect_locked():
                    return
                activity = {
                    "details": details,
                    "state": state,
                }
                if start_ts:
                    activity["timestamps"] = {"start": int(start_ts)}
                payload = {
                    "cmd": "SET_ACTIVITY",
                    "args": {
                        "pid": os.getpid(),
                        "activity": activity,
                    },
                    "nonce": str(uuid.uuid4()),
                }
                if self._send_frame(1, payload):
                    self._read_frame()

        threading.Thread(target=_worker, daemon=True).start()

    def set_launcher_status(self, version: str = "v1.3.2"):
        self.update(
            details="Kamen Rider: Memory of Heroes",
            state=f"In Launcher · PC Native {version}",
            start_ts=int(time.time()),
        )

    def set_playing_status(self, resolution: str = "1080p", fps: str = "60 FPS"):
        res_short = (resolution or "1080p").split(" ")[0]
        fps_short = (fps or "60 FPS").split(" ")[0] + " FPS"
        self.update(
            details="Kamen Rider: Memory of Heroes",
            state=f"Playing · {res_short} · {fps_short} (PC Native)",
            start_ts=int(time.time()),
        )

    def clear(self):
        def _worker():
            with self._lock:
                if self._connected and self._pipe:
                    payload = {
                        "cmd": "SET_ACTIVITY",
                        "args": {"pid": os.getpid(), "activity": None},
                        "nonce": str(uuid.uuid4()),
                    }
                    self._send_frame(1, payload)
                self._close_locked()

        threading.Thread(target=_worker, daemon=True).start()

    def close(self):
        with self._lock:
            self._close_locked()
