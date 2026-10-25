# SPDX-License-Identifier: GPL-2.0-or-later
"""
Persistent INI Configuration Manager for Kamen Rider: Memory of Heroes Launcher.
Modeled after CTR-NitroFueled-PC (launcher.ini).
"""

import os
import re
import sys
import threading
import configparser
from pathlib import Path

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
INI_PATH = BASE_DIR / "launcher.ini"

# pywebview executes every JS API call on its own thread; serialise file writes
# and write atomically so two quick saves can never leave a half-written file.
_WRITE_LOCK = threading.Lock()

def _atomic_write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)

DEFAULT_CONFIG = {
    "game_dir": "CUSA17374",
    "update_dir": "",
    "resolution": "1080p (Native FHD)",
    "fps": "60 FPS (Native Unlock)",
    "upscaler": "Off (Native)",
    "upscaler_quality": "Quality (67%)",
    "fullscreen": "false",
    "borderless": "true",
    "show_fps": "true",
    "show_perf_hud": "false",
    "aspect_ratio": "16:9",
    "compile_shaders_bg": "true",
    "vsync_mode": "Mailbox (Fastest / Unlocked)",
    "audio_volume": "100",
    "hide_launcher_on_play": "true",
    "close_launcher_on_exit": "false",
    "check_updates_startup": "true",
    "auto_install_updates": "false",
    "language": "id",
    "player_name": "AO Zero",
    "gamepad_name": "Auto Detect",
}

def load_launcher_config() -> dict:
    """Load configuration from launcher.ini or create default."""
    cfg = configparser.ConfigParser(interpolation=None)
    result = dict(DEFAULT_CONFIG)
    
    if INI_PATH.is_file():
        try:
            cfg.read(INI_PATH, encoding="utf-8")
            if "Launcher" in cfg:
                for k, v in cfg["Launcher"].items():
                    result[k] = v
        except Exception as e:
            print(f"[CONFIG] Warning: Could not read launcher.ini: {e}")
            
    raw_game_dir = result.get("game_dir", "CUSA17374")
    game_path = Path(raw_game_dir)
    if not game_path.is_absolute():
        game_path = BASE_DIR / game_path
    if not game_path.is_dir() and (BASE_DIR / "CUSA17374").is_dir():
        game_path = BASE_DIR / "CUSA17374"
    result["game_dir"] = str(game_path)
        
    res_aliases = {
        "480p": "480p (Potato PC)",
        "720p": "720p (Low-End PC)",
        "1080p": "1080p (Native FHD)",
        "1440p": "1440p (2K QHD)",
        "4k": "4K (Ultra UHD)",
        "4K": "4K (Ultra UHD)",
    }
    # Targets MUST match the <option value> strings in ui/index.html, otherwise
    # the dropdown shows blank and the next save writes an empty value.
    fps_aliases = {
        "30": "30 FPS (Locked)",
        "30 fps": "30 FPS (Locked)",
        "30 FPS": "30 FPS (Locked)",
        "30 FPS (Console Default)": "30 FPS (Locked)",
        "30 FPS (Console)": "30 FPS (Locked)",
        "60": "60 FPS (Native Unlock)",
        "60 fps": "60 FPS (Native Unlock)",
        "60 FPS": "60 FPS (Native Unlock)",
        "120": "120 FPS (High Refresh)",
        "120 fps": "120 FPS (High Refresh)",
        "120 FPS": "120 FPS (High Refresh)",
        "120 FPS (High-Refresh)": "120 FPS (High Refresh)",
        "144": "144 FPS (Ultra Refresh)",
        "144 FPS": "144 FPS (Ultra Refresh)",
    }
    upscaler_aliases = {
        "AMD FSR 3.1 (Recommended)": "AMD FSR 3.1 (High Quality)",
        "AMD FSR 3.1": "AMD FSR 3.1 (High Quality)",
        "AMD FSR 1": "AMD FSR 1 (Potato PC / Fastest)",
        "NVIDIA DLSS": "NVIDIA DLSS (RTX Only)",
        "": "Off (Native)",
    }
    if result.get("resolution") in res_aliases:
        result["resolution"] = res_aliases[result["resolution"]]
    if result.get("fps") in fps_aliases:
        result["fps"] = fps_aliases[result["fps"]]
    if result.get("upscaler") in upscaler_aliases:
        result["upscaler"] = upscaler_aliases[result["upscaler"]]
    for bool_key in ("fullscreen", "borderless", "show_fps", "show_perf_hud", "compile_shaders_bg",
                     "hide_launcher_on_play", "close_launcher_on_exit", "check_updates_startup",
                     "auto_install_updates"):
        result[bool_key] = str(result.get(bool_key, DEFAULT_CONFIG[bool_key])).strip().lower()

    return result

def save_launcher_config(config_dict: dict):
    """Save configuration dictionary to launcher.ini."""
    import io
    cfg = configparser.ConfigParser(interpolation=None)
    cfg["Launcher"] = {k: str(v) for k, v in config_dict.items()}
    try:
        buf = io.StringIO()
        cfg.write(buf)
        with _WRITE_LOCK:
            _atomic_write_text(INI_PATH, buf.getvalue())
        print(f"[CONFIG] Saved settings to {INI_PATH.name}")
    except Exception as e:
        print(f"[CONFIG] Error saving launcher.ini: {e}")

DEFAULT_KEYBINDS = {
    # --- Keyboard & Mouse Bindings (kept identical to README / launcher labels) ---
    "square": "leftbutton",          # Light Attack (Left Mouse Button)
    "triangle": "rightbutton",       # Heavy Attack (Right Mouse Button)
    "cross": "space",                # Jump / Confirm
    "circle": "lshift",              # Dodge / Cancel
    "l1": "q",                       # Guard / Lock-On
    "r1": "e",                       # Rider Power Stance
    "r2": "middlebutton",            # Special Finish Skill (Middle Mouse Button)
    "l2": "f",                       # Form Change
    "touchpad": "tab",               # Touchpad / Map
    "left_stick_up": "w",            # Move Forward
    "left_stick_down": "s",          # Move Backward
    "left_stick_left": "a",          # Move Left
    "left_stick_right": "d",         # Move Right
    "axis_left_y_minus": "w",
    "axis_left_y_plus": "s",
    "axis_left_x_minus": "a",
    "axis_left_x_plus": "d",
    "touchpad_center": "tab",
    "options": "escape",
    "mouse_to_joystick": "right",    # Mouse Look
    "mouse_sensitivity": 30,         # Slider value (25 = 1.0x, 30 = 1.2x)

    # --- Gamepad / Controller Bindings ---
    "pad_square": "square",          # Normal Attack (Square □ / Xbox X)
    "pad_triangle": "triangle",      # Form Skill (Triangle △ / Xbox Y)
    "pad_cross": "cross",            # Jump (Cross ✕ / Xbox A)
    "pad_circle": "circle",          # Evade / Dash (Circle ○ / Xbox B)
    "pad_l1": "l1",                  # Form Select (L1 / LB)
    "pad_r1": "r1",                  # Lock-On / Guard (R1 / RB)
    "pad_l2": "l2",                  # Gadget Assist (L2 / LT)
    "pad_r2": "r2",                  # Finisher / Max Drive (R2 / RT)
    "pad_l3": "l3",                  # Thumbstick Click Left (L3 / LS)
    "pad_r3": "r3",                  # Thumbstick Click Right (R3 / RS)
    "pad_options": "options",        # Start / Options
    "pad_touchpad": "back",          # Touchpad / Select / Back
    "pad_dpad_up": "pad_up",         # D-Pad Up
    "pad_dpad_down": "pad_down",     # D-Pad Down
    "pad_dpad_left": "pad_left",     # D-Pad Left
    "pad_dpad_right": "pad_right",   # D-Pad Right
    "pad_deadzone": 5,               # Analog stick deadzone (1-30)
    "deadzone": 5,
}

# Bidirectional mapping between UI action keys and INI setting keys
KBM_UI_TO_INI = {
    "left_stick_up": "axis_left_y_minus",
    "left_stick_down": "axis_left_y_plus",
    "left_stick_left": "axis_left_x_minus",
    "left_stick_right": "axis_left_x_plus",
    "touchpad": "touchpad_center",
}
KBM_INI_TO_UI = {v: k for k, v in KBM_UI_TO_INI.items()}

def get_input_config_path() -> Path:
    p = BASE_DIR / "bin" / "user" / "input_config" / "CUSA17374.ini"
    if not p.is_file():
        p = BASE_DIR / "bin" / "user" / "input_config" / "default.ini"
    return p

def load_keybinds() -> dict:
    """Read keybind configuration for both Keyboard/Mouse and Gamepad from ini file."""
    res = dict(DEFAULT_KEYBINDS)
    path = get_input_config_path()
    if path.is_file():
        try:
            current_section = "kbm"
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if "Gamepad" in line or "Controller" in line:
                        current_section = "pad"
                        continue
                    elif "Keyboard" in line:
                        current_section = "kbm"
                        continue
                    if line.startswith("#"):
                        continue

                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip()
                        first_val = v.split(",")[0].strip() if "," in v else v

                        if current_section == "kbm":
                            if k in res:
                                res[k] = first_val
                            if k in KBM_INI_TO_UI:
                                res[KBM_INI_TO_UI[k]] = first_val
                            if k == "touchpad_center":
                                res["touchpad"] = first_val
                            elif k == "mouse_movement_params":
                                parts = [p.strip() for p in v.split(",")]
                                if len(parts) >= 2:
                                    try:
                                        sens_float = float(parts[1])
                                        res["mouse_sensitivity"] = max(10, min(60, int(round(sens_float * 25.0))))
                                    except ValueError:
                                        res["mouse_sensitivity"] = 30
                        else:  # current_section == "pad"
                            pad_key = "pad_" + k
                            if k == "touchpad_center":
                                pad_key = "pad_touchpad"
                            elif k == "pad_up":
                                pad_key = "pad_dpad_up"
                            elif k == "pad_down":
                                pad_key = "pad_dpad_down"
                            elif k == "pad_left":
                                pad_key = "pad_dpad_left"
                            elif k == "pad_right":
                                pad_key = "pad_dpad_right"

                            if pad_key in res:
                                res[pad_key] = first_val
                            elif k == "analog_deadzone":
                                parts = [p.strip() for p in v.split(",")]
                                if len(parts) >= 2 and parts[0] == "leftjoystick":
                                    try:
                                        dz = int(parts[1])
                                        res["pad_deadzone"] = dz
                                        res["deadzone"] = dz
                                    except ValueError:
                                        pass
        except Exception as e:
            print(f"[KEYBINDS] Warning reading keybinds: {e}")

    # Synchronize UI aliases
    for ui_k, ini_k in KBM_UI_TO_INI.items():
        if ini_k in res:
            res[ui_k] = res[ini_k]
    if "touchpad_center" in res:
        res["touchpad"] = res["touchpad_center"]
    if "deadzone" not in res:
        res["deadzone"] = res.get("pad_deadzone", 5)

    return res

def save_keybinds(binds: dict):
    """Save keybind configuration for both Keyboard/Mouse and Gamepad to ini files."""
    data = dict(DEFAULT_KEYBINDS)
    data.update(binds)

    # Convert UI action names back to INI keys if provided
    for ui_k, ini_k in KBM_UI_TO_INI.items():
        if ui_k in binds and binds[ui_k]:
            data[ini_k] = binds[ui_k]
    if "touchpad" in binds and binds["touchpad"]:
        data["touchpad_center"] = binds["touchpad"]

    # Calculate mouse sensitivity float
    sens = data.get("mouse_sensitivity", 30)
    try:
        sens_num = float(sens)
        if sens_num > 5.0:
            sens_val = round(sens_num / 25.0, 2)
        else:
            sens_val = round(sens_num, 2)
    except Exception:
        sens_val = 1.2

    mouse_mode = data.get("mouse_to_joystick", "right")
    if mouse_mode not in ["right", "left", "none"]:
        mouse_mode = "right"

    deadzone_raw = binds.get("deadzone", binds.get("pad_deadzone", 5))
    try:
        deadzone_val = max(1, min(30, int(deadzone_raw)))
    except Exception:
        deadzone_val = 5

    def get_val(action, default_val):
        v = str(data.get(action, default_val)).strip()
        if "," in v:
            v = v.split(",")[0].strip()
        return v if v else default_val

    ini_content = f"""# ==============================================================================
# KAMEN RIDER: MEMORY OF HEROES - NATIVE PC INPUT CONFIGURATION
# Simultaneous Support: Keyboard & Mouse + Gamepad (Xbox / PlayStation)
# Port Lead: AO Zero | Partner: Bakka Sub (www.bakkasub.my.id)
# ==============================================================================

# --- Keyboard & Mouse Bindings ---
axis_left_y_minus = {get_val("axis_left_y_minus", "w")}
axis_left_y_plus = {get_val("axis_left_y_plus", "s")}
axis_left_x_minus = {get_val("axis_left_x_minus", "a")}
axis_left_x_plus = {get_val("axis_left_x_plus", "d")}

# --- Camera Look (Mouse Look via Right Analog Stick) ---
mouse_to_joystick = {mouse_mode}
mouse_movement_params = 0.5, {sens_val}, 0.1

# Keyboard fallback for camera
axis_right_x_minus = left
axis_right_x_plus = right
axis_right_y_minus = up
axis_right_y_plus = down

# --- Core Action Buttons (Mouse & Keyboard) ---
square = {get_val("square", "leftbutton")}
triangle = {get_val("triangle", "rightbutton")}
cross = {get_val("cross", "space")}
circle = {get_val("circle", "lshift")}

# --- Shoulder & Trigger Buttons (Keyboard) ---
l1 = {get_val("l1", "q")}
r1 = {get_val("r1", "e")}
l2 = {get_val("l2", "f")}
r2 = {get_val("r2", "middlebutton")}
l3 = x
r3 = z

# --- System & D-Pad (Keyboard) ---
options = {get_val("options", "escape")}
touchpad_center = {get_val("touchpad_center", "tab")}

pad_up = up
pad_down = down
pad_left = left
pad_right = right


# --- Gamepad / Controller Bindings ---
square = {get_val("pad_square", "square")}
triangle = {get_val("pad_triangle", "triangle")}
cross = {get_val("pad_cross", "cross")}
circle = {get_val("pad_circle", "circle")}

l1 = {get_val("pad_l1", "l1")}
r1 = {get_val("pad_r1", "r1")}
l2 = {get_val("pad_l2", "l2")}
r2 = {get_val("pad_r2", "r2")}
l3 = {get_val("pad_l3", "l3")}
r3 = {get_val("pad_r3", "r3")}

options = {get_val("pad_options", "options")}
touchpad_center = {get_val("pad_touchpad", "back")}

pad_up = {get_val("pad_dpad_up", "pad_up")}
pad_down = {get_val("pad_dpad_down", "pad_down")}
pad_left = {get_val("pad_dpad_left", "pad_left")}
pad_right = {get_val("pad_dpad_right", "pad_right")}

# --- Direct Controller Axes Pass-Through ---
axis_left_x = axis_left_x
axis_left_y = axis_left_y
axis_right_x = axis_right_x
axis_right_y = axis_right_y

# Range of deadzones: 1 (almost none) to 127 (max)
analog_deadzone = leftjoystick, {deadzone_val}, 127
analog_deadzone = rightjoystick, {deadzone_val}, 127

override_controller_color = false, 0, 0, 255
"""
    input_dir = BASE_DIR / "bin" / "user" / "input_config"
    input_dir.mkdir(parents=True, exist_ok=True)
    with _WRITE_LOCK:
        for fname in ["default.ini", "CUSA17374.ini"]:
            _atomic_write_text(input_dir / fname, ini_content)
    print(f"[KEYBINDS] Saved updated keybinds (KBM + Gamepad) to input configs.")

if __name__ == "__main__":
    c = load_launcher_config()
    print("Loaded config:", c)
    save_launcher_config(c)
    kb = load_keybinds()
    print("Loaded keybinds:", kb)
    save_keybinds(kb)

