# SPDX-License-Identifier: GPL-2.0-or-later
r"""
Zero-Dependency Discord Rich Presence (IPC) Client for Windows.
Uses Win32 CreateFileW / WriteFile / ReadFile on \\.\pipe\discord-ipc-0..9
for 100% reliable local Discord communication (Python's built-in open() fails
on Windows named pipes with Errno 22).
Fails silently if Discord is not running — never blocks or crashes the launcher.
"""

import ctypes
import json
import os
import struct
import sys
import threading
import time
import uuid
from ctypes import wintypes

# Default Discord Application ID (can be overridden via launcher.ini -> discord_client_id)
DEFAULT_CLIENT_ID = "1274824899621523508"

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
OPEN_EXISTING = 3
INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value


class DiscordRPC:
    def __init__(self, client_id: str = DEFAULT_CLIENT_ID):
        self.client_id = (client_id or DEFAULT_CLIENT_ID).strip()
        self.enabled = True
        self._handle = None
        self._lock = threading.Lock()
        self._connected = False
        self._last_activity = None

    def _close_locked(self):
        if self._handle is not None and self._handle != INVALID_HANDLE_VALUE:
            try:
                ctypes.windll.kernel32.CloseHandle(self._handle)
            except Exception:
                pass
        self._handle = None
        self._connected = False

    def _write_exact(self, data: bytes) -> bool:
        if not self._handle or self._handle == INVALID_HANDLE_VALUE:
            return False
        written = wintypes.DWORD(0)
        ok = ctypes.windll.kernel32.WriteFile(
            self._handle, data, len(data), ctypes.byref(written), None
        )
        return bool(ok) and written.value == len(data)

    def _read_exact(self, n: int) -> bytes:
        if not self._handle or self._handle == INVALID_HANDLE_VALUE:
            return b""
        buf = ctypes.create_string_buffer(n)
        read_bytes = wintypes.DWORD(0)
        ok = ctypes.windll.kernel32.ReadFile(
            self._handle, buf, n, ctypes.byref(read_bytes), None
        )
        if not ok or read_bytes.value < n:
            return b""
        return buf.raw[: read_bytes.value]

    def _send_frame(self, opcode: int, payload: dict) -> bool:
        try:
            body = json.dumps(payload).encode("utf-8")
            header = struct.pack("<II", opcode, len(body))
            if not self._write_exact(header + body):
                self._close_locked()
                return False
            return True
        except Exception:
            self._close_locked()
            return False

    def _read_frame(self):
        try:
            hdr = self._read_exact(8)
            if len(hdr) < 8:
                self._close_locked()
                return None
            _op, length = struct.unpack("<II", hdr)
            if length <= 0 or length > 65536:
                return None
            body = self._read_exact(length)
            if not body:
                self._close_locked()
                return None
            return json.loads(body.decode("utf-8", errors="ignore"))
        except Exception:
            self._close_locked()
            return None

    def _connect_locked(self) -> bool:
        if self._connected and self._handle:
            return True
        if sys.platform != "win32" or not self.enabled:
            return False
        kernel32 = ctypes.windll.kernel32
        kernel32.CreateFileW.restype = wintypes.HANDLE
        for i in range(10):
            pipe_path = rf"\\.\pipe\discord-ipc-{i}"
            h = kernel32.CreateFileW(
                pipe_path,
                GENERIC_READ | GENERIC_WRITE,
                0,
                None,
                OPEN_EXISTING,
                0,
                None,
            )
            if h and h != INVALID_HANDLE_VALUE:
                self._handle = h
                if self._send_frame(0, {"v": 1, "client_id": self.client_id}):
                    resp = self._read_frame()
                    if resp is not None:
                        self._connected = True
                        return True
                self._close_locked()
        return False

    def set_enabled(self, enabled: bool):
        self.enabled = bool(enabled)
        if not self.enabled:
            self.clear()

    def update(self, details: str, state: str, start_ts: int = None):
        self._last_activity = (details, state, start_ts)
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

    def set_launcher_status(self, version: str = "v1.3.2-PC-Native"):
        self.update(
            details="Kamen Rider: Memory of Heroes",
            state=f"In Launcher · PC Native ({version})",
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
                if self._connected and self._handle:
                    payload = {
                        "cmd": "SET_ACTIVITY",
                        "args": {"pid": os.getpid(), "activity": None},
                        "nonce": str(uuid.uuid4()),
                    }
                    if self._send_frame(1, payload):
                        self._read_frame()
                self._close_locked()

        threading.Thread(target=_worker, daemon=True).start()

    def close(self):
        with self._lock:
            self._close_locked()
