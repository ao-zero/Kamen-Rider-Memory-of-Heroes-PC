# SPDX-License-Identifier: GPL-2.0-or-later
"""
Lightweight Click-Through Real-Time Performance HUD Overlay (MangoHud-style)
for Kamen Rider: Memory of Heroes — PC Native Edition.

Displays live CPU %, GPU % / Temp / VRAM, System RAM, Game Process RAM,
and Session Timer in a compact top-left corner overlay when FPS Overlay is
set to "Detailed". Zero external pip dependencies (pure Win32 ctypes + tkinter).
"""

import ctypes
import subprocess
import sys
import threading
import time
from ctypes import wintypes


class _FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]


class _MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


class _PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def _ft_to_int(ft: _FILETIME) -> int:
    return (ft.dwHighDateTime << 32) | ft.dwLowDateTime


class _SystemMonitor:
    def __init__(self, game_pid: int = 0):
        self.game_pid = game_pid
        self._prev_idle = 0
        self._prev_kernel = 0
        self._prev_user = 0
        self._gpu_text = "Vulkan 1.3 Active"
        self._gpu_stop = threading.Event()
        self._init_cpu()
        self._gpu_thread = threading.Thread(target=self._poll_gpu_loop, daemon=True)
        self._gpu_thread.start()

    def _init_cpu(self):
        if sys.platform != "win32":
            return
        idle, kernel, user = _FILETIME(), _FILETIME(), _FILETIME()
        if ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
            self._prev_idle = _ft_to_int(idle)
            self._prev_kernel = _ft_to_int(kernel)
            self._prev_user = _ft_to_int(user)

    def get_cpu_percent(self) -> float:
        if sys.platform != "win32":
            return 0.0
        idle, kernel, user = _FILETIME(), _FILETIME(), _FILETIME()
        if not ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
            return 0.0
        cur_idle = _ft_to_int(idle)
        cur_kernel = _ft_to_int(kernel)
        cur_user = _ft_to_int(user)

        d_idle = cur_idle - self._prev_idle
        d_total = (cur_kernel - self._prev_kernel) + (cur_user - self._prev_user)
        self._prev_idle, self._prev_kernel, self._prev_user = cur_idle, cur_kernel, cur_user

        if d_total <= 0:
            return 0.0
        return max(0.0, min(100.0, (1.0 - (d_idle / d_total)) * 100.0))

    def get_ram_info(self) -> tuple:
        if sys.platform != "win32":
            return (0.0, 0.0, 0)
        mem = _MEMORYSTATUSEX()
        mem.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem)):
            total_gb = mem.ullTotalPhys / (1024 ** 3)
            used_gb = (mem.ullTotalPhys - mem.ullAvailPhys) / (1024 ** 3)
            return (used_gb, total_gb, int(mem.dwMemoryLoad))
        return (0.0, 0.0, 0)

    def get_game_ram_mb(self) -> float:
        if sys.platform != "win32" or not self.game_pid:
            return 0.0
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        PROCESS_VM_READ = 0x0010
        h = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ, False, self.game_pid)
        if not h:
            return 0.0
        try:
            pmc = _PROCESS_MEMORY_COUNTERS()
            pmc.cb = ctypes.sizeof(_PROCESS_MEMORY_COUNTERS)
            if ctypes.windll.psapi.GetProcessMemoryInfo(h, ctypes.byref(pmc), pmc.cb):
                return pmc.WorkingSetSize / (1024 * 1024)
        except Exception:
            pass
        finally:
            ctypes.windll.kernel32.CloseHandle(h)
        return 0.0

    def _poll_gpu_loop(self):
        flags = 0x08000000 if sys.platform == "win32" else 0
        nvidia_ok = True
        while not self._gpu_stop.is_set():
            if nvidia_ok:
                try:
                    r = subprocess.run(
                        [
                            "nvidia-smi",
                            "--query-gpu=utilization.gpu,temperature.gpu,memory.used,memory.total",
                            "--format=csv,noheader,nounits",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=2,
                        creationflags=flags,
                    )
                    if r.returncode == 0 and r.stdout.strip():
                        parts = [p.strip() for p in r.stdout.strip().splitlines()[0].split(",")]
                        if len(parts) >= 4:
                            util, temp, v_used, v_tot = parts[0], parts[1], float(parts[2]) / 1024.0, float(parts[3]) / 1024.0
                            self._gpu_text = f"{util}% · {temp}°C · {v_used:.1f}/{v_tot:.1f} GB"
                    else:
                        nvidia_ok = False
                except Exception:
                    nvidia_ok = False
            self._gpu_stop.wait(1.5)

    def stop(self):
        self._gpu_stop.set()


class PerfOverlay:
    """Non-blocking, click-through transparent corner HUD attached to a game process."""

    def __init__(self, proc, resolution: str = "1080p", fps: str = "60 FPS"):
        self.proc = proc
        self.res_short = (resolution or "1080p").split(" ")[0]
        self.fps_short = (fps or "60 FPS").split(" ")[0] + " FPS"
        self._stop_evt = threading.Event()
        self._thread = None

    def start(self):
        if sys.platform != "win32":
            return
        self._thread = threading.Thread(target=self._run_ui, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_evt.set()

    def _run_ui(self):
        try:
            import tkinter as tk
        except Exception:
            return

        mon = _SystemMonitor(game_pid=getattr(self.proc, "pid", 0))
        t_start = time.time()

        try:
            root = tk.Tk()
            root.overrideredirect(True)
            root.attributes("-topmost", True)
            root.attributes("-alpha", 0.84)
            root.configure(bg="#0D1014")
            root.geometry("+14+14")

            # Make window click-through, non-focusable, and hidden from Alt+Tab/Taskbar
            root.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(root.winfo_id()) or root.winfo_id()
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_TOOLWINDOW = 0x00000080
            WS_EX_NOACTIVATE = 0x08000000
            ex = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(
                hwnd, GWL_EXSTYLE, ex | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
            )

            frame = tk.Frame(root, bg="#0D1014", highlightbackground="#2A313C", highlightthickness=1, padx=10, pady=7)
            frame.pack()

            lbl_hdr = tk.Label(
                frame,
                text="● KR PERF HUD  00:00",
                fg="#4ADE80",
                bg="#0D1014",
                font=("Consolas", 9, "bold"),
                anchor="w",
            )
            lbl_hdr.pack(fill="x")

            lbl_body = tk.Label(
                frame,
                text="CPU   : --%\nGPU   : Detecting...\nRAM   : -- / -- GB\nGAME  : -- MB\nMODE  : " + f"{self.res_short} · {self.fps_short}",
                fg="#E6EDF3",
                bg="#0D1014",
                font=("Consolas", 9),
                justify="left",
                anchor="w",
            )
            lbl_body.pack(fill="x", pady=(3, 0))

            def refresh():
                if self._stop_evt.is_set() or (self.proc is not None and self.proc.poll() is not None):
                    mon.stop()
                    try:
                        root.destroy()
                    except Exception:
                        pass
                    return

                elapsed = int(time.time() - t_start)
                mm, ss = divmod(elapsed, 60)
                cpu = mon.get_cpu_percent()
                r_used, r_tot, r_pct = mon.get_ram_info()
                g_mb = mon.get_game_ram_mb()

                lbl_hdr.config(text=f"● KR PERF HUD  {mm:02d}:{ss:02d}")
                lbl_body.config(
                    text=(
                        f"CPU   : {cpu:4.1f}%\n"
                        f"GPU   : {mon._gpu_text}\n"
                        f"RAM   : {r_used:.1f}/{r_tot:.0f} GB ({r_pct}%)\n"
                        f"GAME  : {g_mb:,.0f} MB\n"
                        f"MODE  : {self.res_short} · {self.fps_short}"
                    )
                )
                # Keep topmost without stealing focus
                root.attributes("-topmost", True)
                root.after(900, refresh)

            root.after(400, refresh)
            root.mainloop()
        except Exception as e:
            print(f"[PERF HUD] Overlay notice: {e}")
        finally:
            mon.stop()
