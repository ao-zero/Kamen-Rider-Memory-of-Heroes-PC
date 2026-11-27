# SPDX-License-Identifier: GPL-2.0-or-later
"""
Pure-Win32 Click-Through Real-Time Performance HUD Overlay (Zero Dependencies)
for Kamen Rider: Memory of Heroes — PC Native Edition.

Uses native Win32 CreateWindowExW + GDI DrawTextW + SetLayeredWindowAttributes.
No tkinter / Tcl/Tk required — works 100% reliably inside PyInstaller .exe!
Displays live CPU %, GPU % / Temp / VRAM, System RAM, Game RAM, and Session Timer.
"""

import ctypes
import os
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


class _PAINTSTRUCT(ctypes.Structure):
    _fields_ = [
        ("hdc", wintypes.HDC),
        ("fErase", wintypes.BOOL),
        ("rcPaint", wintypes.RECT),
        ("fRestore", wintypes.BOOL),
        ("fIncUpdate", wintypes.BOOL),
        ("rgbReserved", ctypes.c_byte * 32),
    ]


WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_longlong, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)


class _WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HCURSOR),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", wintypes.HICON),
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
        h = ctypes.windll.kernel32.OpenProcess(0x1010, False, self.game_pid)
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
                            util, temp = parts[0], parts[1]
                            v_used = float(parts[2]) / 1024.0
                            v_tot = float(parts[3]) / 1024.0
                            self._gpu_text = f"{util}% | {temp}C | {v_used:.1f}/{v_tot:.1f} GB"
                    else:
                        nvidia_ok = False
                except Exception:
                    nvidia_ok = False
            self._gpu_stop.wait(1.5)

    def stop(self):
        self._gpu_stop.set()


class PerfOverlay:
    """Pure-Win32 non-blocking, click-through transparent corner HUD."""

    def __init__(self, proc, resolution: str = "1080p", fps: str = "60 FPS"):
        self.proc = proc
        self.res_short = (resolution or "1080p").split(" ")[0]
        self.fps_short = (fps or "60 FPS").split(" ")[0] + " FPS"
        self._stop_evt = threading.Event()
        self._thread = None

    def start(self):
        if sys.platform != "win32":
            return
        self._thread = threading.Thread(target=self._run_win32, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_evt.set()

    def _run_win32(self):
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32
        kernel32 = ctypes.windll.kernel32

        user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.DefWindowProcW.restype = ctypes.c_longlong
        user32.RegisterClassExW.argtypes = [ctypes.POINTER(_WNDCLASSEXW)]
        user32.RegisterClassExW.restype = wintypes.ATOM
        user32.UnregisterClassW.argtypes = [wintypes.LPCWSTR, wintypes.HINSTANCE]
        user32.UnregisterClassW.restype = wintypes.BOOL
        user32.CreateWindowExW.argtypes = [
            wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
            wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID
        ]
        user32.CreateWindowExW.restype = wintypes.HWND
        user32.SetLayeredWindowAttributes.argtypes = [wintypes.HWND, wintypes.COLORREF, ctypes.c_ubyte, wintypes.DWORD]
        user32.SetLayeredWindowAttributes.restype = wintypes.BOOL
        user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.UpdateWindow.argtypes = [wintypes.HWND]
        user32.SetTimer.argtypes = [wintypes.HWND, ctypes.c_size_t, wintypes.UINT, ctypes.c_void_p]
        user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
        user32.InvalidateRect.argtypes = [wintypes.HWND, ctypes.c_void_p, wintypes.BOOL]
        user32.DestroyWindow.argtypes = [wintypes.HWND]
        user32.BeginPaint.argtypes = [wintypes.HWND, ctypes.POINTER(_PAINTSTRUCT)]
        user32.BeginPaint.restype = wintypes.HDC
        user32.EndPaint.argtypes = [wintypes.HWND, ctypes.POINTER(_PAINTSTRUCT)]
        user32.FillRect.argtypes = [wintypes.HDC, ctypes.POINTER(wintypes.RECT), wintypes.HBRUSH]
        user32.FrameRect.argtypes = [wintypes.HDC, ctypes.POINTER(wintypes.RECT), wintypes.HBRUSH]
        user32.DrawTextW.argtypes = [wintypes.HDC, wintypes.LPCWSTR, ctypes.c_int, ctypes.POINTER(wintypes.RECT), wintypes.UINT]
        kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        kernel32.GetModuleHandleW.restype = wintypes.HMODULE
        gdi32.CreateSolidBrush.argtypes = [wintypes.COLORREF]
        gdi32.CreateSolidBrush.restype = wintypes.HBRUSH
        gdi32.CreateFontW.restype = wintypes.HFONT
        gdi32.SetBkMode.argtypes = [wintypes.HDC, ctypes.c_int]
        gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
        gdi32.SelectObject.restype = wintypes.HGDIOBJ
        gdi32.SetTextColor.argtypes = [wintypes.HDC, wintypes.COLORREF]
        gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]

        mon = _SystemMonitor(game_pid=getattr(self.proc, "pid", 0))
        t_start = time.time()

        hdr_text = "KR PERF HUD  00:00"
        body_text = (
            "CPU  : --%\n"
            "GPU  : Detecting...\n"
            "RAM  : -- / -- GB\n"
            "GAME : -- MB\n"
            f"MODE : {self.res_short} | {self.fps_short}"
        )

        bg_brush = gdi32.CreateSolidBrush(0x0014100D)       # BGR #0D1014
        border_brush = gdi32.CreateSolidBrush(0x003C312A)   # BGR #2A313C
        font_hdr = gdi32.CreateFontW(-13, 0, 0, 0, 700, 0, 0, 0, 1, 0, 0, 5, 0x31, "Consolas")
        font_body = gdi32.CreateFontW(-12, 0, 0, 0, 400, 0, 0, 0, 1, 0, 0, 5, 0x31, "Consolas")

        WM_PAINT = 0x000F
        WM_TIMER = 0x0113
        WM_DESTROY = 0x0002
        HWND_TOPMOST = wintypes.HWND(-1)
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_NOACTIVATE = 0x0010

        def wnd_proc(hwnd, msg, wparam, lparam):
            nonlocal hdr_text, body_text
            if msg == WM_TIMER:
                if self._stop_evt.is_set() or (self.proc is not None and self.proc.poll() is not None):
                    user32.DestroyWindow(hwnd)
                    return 0
                elapsed = int(time.time() - t_start)
                mm, ss = divmod(elapsed, 60)
                cpu = mon.get_cpu_percent()
                r_used, r_tot, r_pct = mon.get_ram_info()
                g_mb = mon.get_game_ram_mb()
                hdr_text = f"KR PERF HUD  {mm:02d}:{ss:02d}"
                body_text = (
                    f"CPU  : {cpu:4.1f}%\n"
                    f"GPU  : {mon._gpu_text}\n"
                    f"RAM  : {r_used:.1f}/{r_tot:.0f} GB ({r_pct}%)\n"
                    f"GAME : {g_mb:,.0f} MB\n"
                    f"MODE : {self.res_short} | {self.fps_short}"
                )
                user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
                user32.InvalidateRect(hwnd, None, True)
                return 0
            elif msg == WM_PAINT:
                ps = _PAINTSTRUCT()
                hdc = user32.BeginPaint(hwnd, ctypes.byref(ps))
                if hdc:
                    rc = wintypes.RECT(0, 0, 260, 114)
                    user32.FillRect(hdc, ctypes.byref(rc), bg_brush)
                    user32.FrameRect(hdc, ctypes.byref(rc), border_brush)
                    gdi32.SetBkMode(hdc, 1)  # TRANSPARENT

                    gdi32.SelectObject(hdc, font_hdr)
                    gdi32.SetTextColor(hdc, 0x0080DE4A)  # BGR #4ADE80 (green)
                    r_hdr = wintypes.RECT(10, 8, 250, 26)
                    user32.DrawTextW(hdc, hdr_text, -1, ctypes.byref(r_hdr), 0)

                    gdi32.SelectObject(hdc, font_body)
                    gdi32.SetTextColor(hdc, 0x00F3EDE6)  # BGR #E6EDF3 (off-white)
                    r_body = wintypes.RECT(10, 28, 250, 108)
                    user32.DrawTextW(hdc, body_text, -1, ctypes.byref(r_body), 0)

                    user32.EndPaint(hwnd, ctypes.byref(ps))
                return 0
            elif msg == WM_DESTROY:
                user32.PostQuitMessage(0)
                return 0
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        wnd_proc_cb = WNDPROC(wnd_proc)
        hinst = kernel32.GetModuleHandleW(None)
        cls_name = f"KRPerfHudOverlay_{os.getpid()}_{int(time.time()*1000)}"

        wc = _WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(_WNDCLASSEXW)
        wc.lpfnWndProc = wnd_proc_cb
        wc.hInstance = hinst
        wc.hbrBackground = bg_brush
        wc.lpszClassName = cls_name

        try:
            user32.RegisterClassExW(ctypes.byref(wc))
            ex_style = 0x00080000 | 0x00000020 | 0x00000080 | 0x08000000 | 0x00000008
            # WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE | WS_EX_TOPMOST
            ws_popup = 0x80000000
            hwnd = user32.CreateWindowExW(
                ex_style, cls_name, "KR Perf HUD", ws_popup,
                16, 16, 260, 114, None, None, hinst, None
            )
            if not hwnd:
                return

            # 85% opacity (217/255)
            user32.SetLayeredWindowAttributes(hwnd, 0, 217, 0x00000002)
            user32.ShowWindow(hwnd, 4)  # SW_SHOWNOACTIVATE
            user32.UpdateWindow(hwnd)
            user32.SetTimer(hwnd, 1, 900, None)

            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        except Exception as e:
            print(f"[PERF HUD] Win32 overlay notice: {e}")
        finally:
            mon.stop()
            for obj in (bg_brush, border_brush, font_hdr, font_body):
                try:
                    gdi32.DeleteObject(obj)
                except Exception:
                    pass
            try:
                user32.UnregisterClassW(cls_name, hinst)
            except Exception:
                pass
