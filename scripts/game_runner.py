# SPDX-License-Identifier: GPL-2.0-or-later
"""
Kamen Rider: Memory of Heroes - Native PC Game Execution Runner
Project Lead / Admin: AO Zero
Community Partner: Bakka Sub (https://www.bakkasub.my.id)
"""

import os
import sys
import time
import json
import ctypes
import threading
import subprocess
from pathlib import Path
from ctypes import wintypes

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
BIN_DIR = BASE_DIR / "bin"
CORE_EXE = BIN_DIR / "kr_core.exe"
CONFIG_JSON = BIN_DIR / "user" / "config.json"
LOG_DIR = BIN_DIR / "user" / "log"

# Serialises every read-modify-write of config.json. pywebview runs each JS API
# call on its own thread, so concurrent saves used to interleave and corrupt the
# file (e.g. a trailing "}}"), which silently disabled every launcher setting.
_CONFIG_LOCK = threading.Lock()

# Internal Render Resolutions (Includes Potato PC / Low-End presets)
RES_MAP = {
    "480p (Potato PC)": (854, 480, 1280, 720),
    "720p (Low-End PC)": (1280, 720, 1920, 1080),
    "1080p (Native FHD)": (1920, 1080, 1920, 1080),
    "1440p (2K QHD)": (2560, 1440, 2560, 1440),
    "4K (Ultra UHD)": (3840, 2160, 3840, 2160),
    # Fallback keys
    "480p": (854, 480, 1280, 720),
    "720p": (1280, 720, 1920, 1080),
    "1080p": (1920, 1080, 1920, 1080),
    "1440p": (2560, 1440, 2560, 1440),
    "4k": (3840, 2160, 3840, 2160),
    "4K": (3840, 2160, 3840, 2160),
}

# Unity PS4 engine flip rate is 2 vblanks per frame.
# 120 Hz vblank produces TRUE 60 FPS, 240 Hz produces 120 FPS.
# Keys MUST match the <option value="..."> strings in ui/index.html, otherwise
# the lookup silently falls back to 60 FPS (this was the "30/120/144 FPS does
# nothing" bug).
FPS_VBLANK_MAP = {
    "30 FPS (Locked)": 60,
    "60 FPS (Native Unlock)": 120,
    "120 FPS (High Refresh)": 240,
    "144 FPS (Ultra Refresh)": 288,
    "Uncapped": 360,
    # Legacy / fallback keys
    "30 FPS (Console Default)": 60,
    "30 FPS (Console)": 60,
    "120 FPS (High-Refresh)": 240,
    "30 FPS": 60,
    "60 FPS": 120,
    "120 FPS": 240,
    "144 FPS": 288,
    "30": 60,
    "60": 120,
    "120": 240,
    "144": 288,
}

# DLSS / FSR Scale Factors
UPSCALER_SCALE = {
    "Quality (67%)": 0.67,
    "Balanced (58%)": 0.58,
    "Performance (50%)": 0.50,
    "Ultra Performance (33%)": 0.33,
    "DLAA (100%)": 1.0,
}

def _present_mode(vsync_mode: str) -> str:
    """Map the launcher VSync option to the engine's GPU.present_mode value."""
    v = (vsync_mode or "").lower()
    if v.startswith("fifo"):
        return "Fifo"
    if v.startswith("immediate"):
        return "Immediate"
    return "Mailbox"

def _read_config_tolerant(path: Path) -> dict:
    """Read config.json, recovering from trailing garbage left by an interrupted write."""
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        obj, _end = json.JSONDecoder().raw_decode(text.lstrip())
        print("[ENGINE CONFIG] Repaired corrupted config.json (trailing data removed).")
        return obj

def _write_json_atomic(path: Path, data: dict):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)

def sync_engine_config(
    resolution: str = "1080p (Native FHD)",
    fps: str = "60 FPS (Native Unlock)",
    fullscreen: bool = False,
    upscaler: str = "Off (Native)",
    upscaler_quality: str = "Quality (67%)",
    show_fps: bool = True,
    borderless: bool = True,
    show_perf_hud: bool = False,
    aspect_ratio: str = "16:9",
    compile_shaders_bg: bool = True,
    vsync_mode: str = "Mailbox (Fastest / Unlocked)",
    audio_volume: int = 100
):
    """Sync graphics and display settings directly to engine config.json with maximum optimization."""
    if not CONFIG_JSON.is_file():
        return

    with _CONFIG_LOCK:
        try:
            cfg = _read_config_tolerant(CONFIG_JSON)

            int_w, int_h, win_w, win_h = RES_MAP.get(resolution, (1920, 1080, 1920, 1080))
            target_vblank = FPS_VBLANK_MAP.get(fps, 120)

            # Apply Upscaler Scale if FSR or DLSS is selected
            use_fsr = "FSR" in upscaler or "Potato" in resolution
            if "DLSS" in upscaler or "FSR" in upscaler:
                scale = UPSCALER_SCALE.get(upscaler_quality, 0.67)
                int_w = int(win_w * scale)
                int_h = int(win_h * scale)
                use_fsr = True

            gpu = cfg.setdefault("GPU", {})
            gpu["window_width"] = win_w
            gpu["window_height"] = win_h
            gpu["internal_screen_width"] = int_w
            gpu["internal_screen_height"] = int_h
            gpu["full_screen"] = fullscreen
            gpu["full_screen_mode"] = "Borderless" if (borderless or fullscreen) else "Windowed"
            gpu["vblank_frequency"] = target_vblank
            gpu["present_mode"] = _present_mode(vsync_mode)
            gpu["fsr_enabled"] = use_fsr
            gpu["rcas_enabled"] = True
            gpu["rcas_attenuation"] = 250
            gpu["aspect_ratio"] = aspect_ratio

            # Performance Optimizations (Fast Math, Direct Memory Access, Zero Shader Stutter)
            gpu["fast_shader_math"] = compile_shaders_bg
            gpu["direct_memory_access_enabled"] = True
            gpu["dump_shaders"] = False

            # Vulkan Optimizations: Disable heavy validation layers and enable persistent pipeline caches
            vulkan = cfg.setdefault("Vulkan", {})
            vulkan["vkvalidation_core_enabled"] = False
            vulkan["vkvalidation_enabled"] = False
            vulkan["vkvalidation_gpu_enabled"] = False
            vulkan["vkvalidation_sync_enabled"] = False
            vulkan["pipeline_cache_enabled"] = True
            vulkan["pipeline_cache_archived"] = True

            gen = cfg.setdefault("General", {})
            gen["show_fps_counter"] = show_fps
            gen["show_splash"] = False
            gen["dev_kit_mode"] = False
            try:
                gen["volume_slider"] = max(0, min(100, int(float(audio_volume))))
            except (TypeError, ValueError):
                gen["volume_slider"] = 100
            # Memory Optimization: Allocate extra direct memory pool to eliminate texture paging stalls
            gen["extra_dmem_in_mbytes"] = 2048
            gen["extra_fmem_in_mbytes"] = 1024

            # Logging Optimization: Disable synchronous disk I/O writes during gameplay
            log = cfg.setdefault("Log", {})
            log["sync"] = False
            log["enable"] = False
            log["skip_duplicate"] = True

            # Input Settings: Ensure Keyboard & Mouse translate to virtual controller
            inp = cfg.setdefault("Input", {})
            inp["use_keyboard_as_keyboard"] = False
            inp["use_mice_as_mice"] = False
            inp["use_unified_input_config"] = True
            inp["cursor_hide_timeout"] = 0
            inp["background_controller_input"] = True

            _write_json_atomic(CONFIG_JSON, cfg)

            print(f"[ENGINE CONFIG] Optimized: {int_w}x{int_h} -> {win_w}x{win_h} | VBlank: {target_vblank}Hz ({fps}) | Present: {gpu['present_mode']} | Volume: {gen['volume_slider']}")
        except Exception as e:
            print(f"[ENGINE CONFIG] Warning: Could not sync config.json: {e}")

def monitor_and_sync_game(proc, target_title="KAMEN RIDER: MEMORY OF HEROES - PC EDITION"):
    """
    Zero-Touch Auto-Sync Engine:
    1. Monitors game window creation and sets clean window title.
    2. Automatically engages Mouse Look & Relative Cursor Mode without requiring F7 keypress.
    3. Manages seamless focus and cursor capture.
    """
    if sys.platform != "win32":
        return

    user32 = ctypes.windll.user32
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    target_hwnd = None
    game_pid = proc.pid

    def enum_callback(hwnd, lparam):
        nonlocal target_hwnd
        if not user32.IsWindowVisible(hwnd):
            return True
        # Only accept windows owned by the game process. Matching by title alone
        # used to grab unrelated windows (e.g. an Explorer window showing the
        # CUSA17374 folder) and send F7 to them.
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value != game_pid:
            return True
        if user32.GetWindowTextLengthW(hwnd) > 0:
            target_hwnd = hwnd
            user32.SetWindowTextW(hwnd, target_title)
            return False  # stop enumeration
        return True

    callback = WNDENUMPROC(enum_callback)

    # 1. Wait for game window to be created
    start_time = time.time()
    while time.time() - start_time < 35 and proc.poll() is None and not target_hwnd:
        user32.EnumWindows(callback, 0)
        if not target_hwnd:
            time.sleep(0.1)

    if not target_hwnd or proc.poll() is not None:
        return

    print(f"[AUTO-SYNC] Detected Game Window (HWND: {target_hwnd}). Preparing input sync...")

    # 2. Wait 1.8 seconds for Vulkan presentation surface to be fully active
    time.sleep(1.8)
    if proc.poll() is not None:
        return

    # Check if a physical gamepad / controller is connected
    has_controller = False
    try:
        try:
            from .controller_manager import get_connected_controllers
        except (ImportError, ValueError):
            from controller_manager import get_connected_controllers
        connected_controllers = get_connected_controllers()
        if connected_controllers:
            has_controller = True
            print(f"[AUTO-SYNC] Detected physical controller: {connected_controllers[0]}.")
    except Exception as e:
        print(f"[AUTO-SYNC] Controller check notice: {e}")

    # 3. Bring game window to front
    try:
        user32.ShowWindow(target_hwnd, 9) # SW_RESTORE
        user32.SetForegroundWindow(target_hwnd)
        time.sleep(0.15)

        # If a gamepad is active, do NOT send F7 (mouse-to-joystick)!
        # F7 binds mouse delta to the right analog stick, which causes the mouse and physical
        # controller right thumbstick to battle and produce jerky/buggy camera rotation.
        if has_controller:
            print("[AUTO-SYNC] Physical Controller is active! Skipping auto Mouse Look (F7) to ensure smooth 360° controller camera without mouse conflict.")
            return

        if user32.GetForegroundWindow() != target_hwnd:
            print("[AUTO-SYNC] Game window is not focused; skipping auto F7 (press F7 manually).")
            return

        # Virtual key code for F7 is 0x76, scan code 0x41
        VK_F7 = 0x76
        SCAN_F7 = 0x41
        KEYEVENTF_KEYUP = 0x0002

        user32.keybd_event(VK_F7, SCAN_F7, 0, 0)
        time.sleep(0.06)
        user32.keybd_event(VK_F7, SCAN_F7, KEYEVENTF_KEYUP, 0)

        print("[AUTO-SYNC] Keyboard & Mouse mode active: Successfully engaged Mouse Look & Locked Cursor (F7)!")
    except Exception as e:
        print(f"[AUTO-SYNC] Warning engaging auto mouse look: {e}")

def _find_core_exe(bin_dir: Path) -> Path:
    core_exe = bin_dir / "kr_core.exe"
    if core_exe.is_file():
        return core_exe
    # Never fall back to helper tools such as the GPU capability probe.
    candidates = [p for p in bin_dir.glob("*.exe") if "gpu-capabilities" not in p.name.lower()]
    if candidates:
        return candidates[0]
    raise FileNotFoundError(f"Binary runner not found at: {core_exe}")

def launch_game(
    game_dir: Path = None,
    resolution: str = "1080p (Native FHD)",
    fps: str = "60 FPS (Native Unlock)",
    fullscreen: bool = False,
    upscaler: str = "Off (Native)",
    upscaler_quality: str = "Quality (67%)",
    show_fps: bool = True,
    player_name: str = "AO Zero",
    detached: bool = False,
    **extra_settings
):
    """Launch Kamen Rider: Memory of Heroes seamlessly with native PC Vulkan runner.

    Any additional keyword arguments (borderless, aspect_ratio, vsync_mode,
    audio_volume, ...) are forwarded to sync_engine_config so launching no longer
    resets those settings to their defaults.
    """
    base = get_base_dir()
    bin_dir = base / "bin"
    core_exe = _find_core_exe(bin_dir)

    if game_dir is None:
        game_dir = base / "CUSA17374"
    else:
        game_dir = Path(game_dir)

    eboot = game_dir / "eboot.bin"
    if not eboot.is_file():
        raise FileNotFoundError(f"File eboot.bin not found at: {eboot}")

    # 1. Sync engine settings with performance enhancements
    sync_engine_config(
        resolution=resolution,
        fps=fps,
        fullscreen=fullscreen,
        upscaler=upscaler,
        upscaler_quality=upscaler_quality,
        show_fps=show_fps,
        **extra_settings
    )

    # 2. Build command line
    cmd = [
        str(core_exe),
        "-g", str(eboot.resolve()),
        "-f", "true" if fullscreen else "false"
    ]
    if show_fps:
        cmd.append("--show-fps")

    env = dict(os.environ)
    env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")

    # Prevent ANY console window from appearing and set High CPU Scheduling Priority
    CREATE_NO_WINDOW = 0x08000000
    HIGH_PRIORITY_CLASS = 0x00000080
    flags = CREATE_NO_WINDOW | HIGH_PRIORITY_CLASS
    if detached and sys.platform == "win32":
        flags |= subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

    # High Precision Timer & Prevent Windows power throttling / CPU downclocking
    if sys.platform == "win32":
        try:
            # Set Windows multimedia timer resolution to 1ms for micro-stutter elimination
            ctypes.windll.winmm.timeBeginPeriod(1)
        except Exception:
            pass
        try:
            ES_CONTINUOUS = 0x80000000
            ES_SYSTEM_REQUIRED = 0x00000001
            ES_DISPLAY_REQUIRED = 0x00000002
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)
        except Exception:
            pass

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    session_log = LOG_DIR / "last_session.log"
    log_file = open(session_log, "w", encoding="utf-8", errors="replace")

    print(f"[LAUNCH] Executing Optimized Native PC Core (High Priority): {' '.join(cmd)}")
    try:
        proc = subprocess.Popen(
            cmd,
            env=env,
            cwd=str(bin_dir),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=flags
        )
    except Exception:
        log_file.close()
        end_session()
        raise
    proc._kr_log_file = log_file

    # 3. Start auto-sync mouse and window title daemon
    threading.Thread(target=monitor_and_sync_game, args=(proc,), daemon=True).start()

    return proc

def end_session(proc=None):
    """Release resources acquired by launch_game (log handle, 1ms timer, keep-awake flag)."""
    log_file = getattr(proc, "_kr_log_file", None) if proc is not None else None
    if log_file is not None:
        try:
            log_file.close()
        except Exception:
            pass
    if sys.platform == "win32":
        try:
            ctypes.windll.winmm.timeEndPeriod(1)
        except Exception:
            pass
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)  # ES_CONTINUOUS only = reset
        except Exception:
            pass

if __name__ == "__main__":
    print(f"Base Directory: {get_base_dir()}")
    sync_engine_config()
