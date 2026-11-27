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
        user32.IsWindow.argtypes = [wintypes.HWND]
        user32.IsWindow.restype = wintypes.BOOL
        user32.IsWindowVisible.argtypes = [wintypes.HWND]
        user32.IsWindowVisible.restype = wintypes.BOOL
        user32.IsIconic.argtypes = [wintypes.HWND]
        user32.IsIconic.restype = wintypes.BOOL
        user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        user32.GetClientRect.restype = wintypes.BOOL
        user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
        user32.ClientToScreen.restype = wintypes.BOOL
        user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        user32.GetWindowTextLengthW.restype = ctypes.c_int
        user32.GetForegroundWindow.restype = wintypes.HWND
        user32.SetWindowRgn.argtypes = [wintypes.HWND, wintypes.HRGN, wintypes.BOOL]
        user32.SetWindowRgn.restype = ctypes.c_int
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
        gdi32.CreatePen.argtypes = [ctypes.c_int, ctypes.c_int, wintypes.COLORREF]
        gdi32.CreatePen.restype = wintypes.HPEN
        gdi32.CreateRoundRectRgn.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        gdi32.CreateRoundRectRgn.restype = wintypes.HRGN
        gdi32.RoundRect.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        gdi32.RoundRect.restype = wintypes.BOOL
        gdi32.CreateFontW.restype = wintypes.HFONT
        gdi32.SetBkMode.argtypes = [wintypes.HDC, ctypes.c_int]
        gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
        gdi32.SelectObject.restype = wintypes.HGDIOBJ
        gdi32.SetTextColor.argtypes = [wintypes.HDC, wintypes.COLORREF]
        gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]

        mon = _SystemMonitor(game_pid=getattr(self.proc, "pid", 0))
        t_start = time.time()

        HUD_W, HUD_H = 236, 118
        rows = [
            ("CPU", "--%"),
            ("GPU", "Detecting..."),
            ("RAM", "-- / -- GB"),
            ("Game", "-- MB"),
            ("Mode", f"{self.res_short} · {self.fps_short}"),
        ]
        timer_str = "00:00"

        # Match the engine FPS pill: dark matte #121315 + subtle gray border #45484E + Segoe UI
        bg_brush = gdi32.CreateSolidBrush(0x00151312)       # BGR #121315
        border_pen = gdi32.CreatePen(0, 1, 0x004E4845)      # BGR #45484E
        font_hdr = gdi32.CreateFontW(-13, 0, 0, 0, 600, 0, 0, 0, 1, 0, 0, 5, 0, "Segoe UI")
        font_lbl = gdi32.CreateFontW(-12, 0, 0, 0, 400, 0, 0, 0, 1, 0, 0, 5, 0, "Segoe UI")
        font_val = gdi32.CreateFontW(-12, 0, 0, 0, 600, 0, 0, 0, 1, 0, 0, 5, 0, "Segoe UI")

        WM_PAINT = 0x000F
        WM_TIMER = 0x0113
        WM_DESTROY = 0x0002
        HWND_TOPMOST = wintypes.HWND(-1)
        SWP_NOSIZE = 0x0001
        SWP_NOACTIVATE = 0x0010
        SW_HIDE = 0
        SW_SHOWNOACTIVATE = 4

        game_pid = getattr(self.proc, "pid", 0)
        game_hwnd = None
        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def _find_game_hwnd():
            nonlocal game_hwnd
            if not game_pid:
                return None
            if game_hwnd and user32.IsWindow(game_hwnd) and user32.IsWindowVisible(game_hwnd):
                return game_hwnd
            found = [None]
            def _cb(h, lp):
                if not user32.IsWindowVisible(h):
                    return True
                pid = wintypes.DWORD(0)
                user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
                if pid.value == game_pid and user32.GetWindowTextLengthW(h) > 0:
                    found[0] = h
                    return False
                return True
            user32.EnumWindows(WNDENUMPROC(_cb), 0)
            game_hwnd = found[0]
            return game_hwnd

        tick_count = 0

        def wnd_proc(hwnd, msg, wparam, lparam):
            nonlocal rows, timer_str, tick_count
            if msg == WM_TIMER:
                if self._stop_evt.is_set() or (self.proc is not None and self.proc.poll() is not None):
                    user32.DestroyWindow(hwnd)
                    return 0

                # Anchor strictly inside the top-left corner of the game's client area
                if game_pid:
                    gh = _find_game_hwnd()
                    if not gh or user32.IsIconic(gh):
                        user32.ShowWindow(hwnd, SW_HIDE)
                        return 0
                    pt = wintypes.POINT(0, 0)
                    if user32.ClientToScreen(gh, ctypes.byref(pt)):
                        # Hide if user switched to another window (so HUD never floats over other apps)
                        fg = user32.GetForegroundWindow()
                        if fg and fg != gh and fg != hwnd:
                            user32.ShowWindow(hwnd, SW_HIDE)
                            return 0
                        user32.SetWindowPos(hwnd, HWND_TOPMOST, pt.x + 12, pt.y + 12, 0, 0, SWP_NOSIZE | SWP_NOACTIVATE)
                        user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)

                tick_count += 1
                # Refresh heavy metrics every ~0.8s (4 ticks of 200ms)
                if tick_count == 1 or tick_count % 4 == 0:
                    elapsed = int(time.time() - t_start)
                    mm, ss = divmod(elapsed, 60)
                    cpu = mon.get_cpu_percent()
                    r_used, r_tot, r_pct = mon.get_ram_info()
                    g_mb = mon.get_game_ram_mb()
                    timer_str = f"{mm:02d}:{ss:02d}"
                    rows = [
                        ("CPU", f"{cpu:.1f}%"),
                        ("GPU", mon._gpu_text.replace(" | ", " · ")),
                        ("RAM", f"{r_used:.1f} / {r_tot:.0f} GB ({r_pct}%)"),
                        ("Game", f"{g_mb:,.0f} MB"),
                        ("Mode", f"{self.res_short} · {self.fps_short}"),
                    ]
                    user32.InvalidateRect(hwnd, None, True)
                return 0
            elif msg == WM_PAINT:
                ps = _PAINTSTRUCT()
                hdc = user32.BeginPaint(hwnd, ctypes.byref(ps))
                if hdc:
                    gdi32.SelectObject(hdc, bg_brush)
                    gdi32.SelectObject(hdc, border_pen)
                    gdi32.RoundRect(hdc, 0, 0, HUD_W, HUD_H, 16, 16)
                    gdi32.SetBkMode(hdc, 1)  # TRANSPARENT

                    # Header row: subtle title left, timer right
                    gdi32.SelectObject(hdc, font_hdr)
                    gdi32.SetTextColor(hdc, 0x00EFECE9)  # crisp white
                    r_hdr = wintypes.RECT(12, 8, HUD_W - 56, 26)
                    user32.DrawTextW(hdc, "Performance", -1, ctypes.byref(r_hdr), 0)

                    gdi32.SelectObject(hdc, font_lbl)
                    gdi32.SetTextColor(hdc, 0x00A6A19B)  # muted gray
                    r_tm = wintypes.RECT(HUD_W - 54, 9, HUD_W - 12, 26)
                    user32.DrawTextW(hdc, timer_str, -1, ctypes.byref(r_tm), 0x0002)  # DT_RIGHT

                    # Metric rows
                    y = 28
                    for lbl, val in rows:
                        gdi32.SelectObject(hdc, font_lbl)
                        gdi32.SetTextColor(hdc, 0x00A6A19B)
                        r_l = wintypes.RECT(12, y, 56, y + 17)
                        user32.DrawTextW(hdc, lbl, -1, ctypes.byref(r_l), 0)

                        gdi32.SelectObject(hdc, font_val)
                        gdi32.SetTextColor(hdc, 0x00EFECE9)
                        r_v = wintypes.RECT(56, y, HUD_W - 12, y + 17)
                        user32.DrawTextW(hdc, val, -1, ctypes.byref(r_v), 0x0002)  # DT_RIGHT
                        y += 16

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
                16, 16, HUD_W, HUD_H, None, None, hinst, None
            )
            if not hwnd:
                return

            # Apply smooth rounded window region matching the FPS counter pill
            rgn = gdi32.CreateRoundRectRgn(0, 0, HUD_W + 1, HUD_H + 1, 16, 16)
            if rgn:
                user32.SetWindowRgn(hwnd, rgn, True)

            # 86% opacity (220/255); start hidden until game window appears if tracking a PID
            user32.SetLayeredWindowAttributes(hwnd, 0, 220, 0x00000002)
            if not game_pid:
                user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)
                user32.UpdateWindow(hwnd)
            user32.SetTimer(hwnd, 1, 200, None)

            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        except Exception as e:
            print(f"[PERF HUD] Win32 overlay notice: {e}")
        finally:
            mon.stop()
            for obj in (bg_brush, border_pen, font_hdr, font_lbl, font_val):
                try:
                    gdi32.DeleteObject(obj)
                except Exception:
                    pass
            try:
                user32.UnregisterClassW(cls_name, hinst)
            except Exception:
                pass
