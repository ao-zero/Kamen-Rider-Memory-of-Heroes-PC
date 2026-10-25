# SPDX-License-Identifier: GPL-2.0-or-later
"""
Gamepad / Controller Detection Utility
Checks connected controllers via XInput & Windows Multimedia API.
"""

import sys
import ctypes

_XINPUT_DLL = None
_XINPUT_STATE_CLASS = None

def _get_xinput():
    global _XINPUT_DLL, _XINPUT_STATE_CLASS
    if _XINPUT_DLL is not None:
        return _XINPUT_DLL, _XINPUT_STATE_CLASS
    if sys.platform != "win32":
        return None, None

    class XINPUT_GAMEPAD(ctypes.Structure):
        _fields_ = [
            ("wButtons", ctypes.c_ushort),
            ("bLeftTrigger", ctypes.c_ubyte),
            ("bRightTrigger", ctypes.c_ubyte),
            ("sThumbLX", ctypes.c_short),
            ("sThumbLY", ctypes.c_short),
            ("sThumbRX", ctypes.c_short),
            ("sThumbRY", ctypes.c_short),
        ]
    class XINPUT_STATE(ctypes.Structure):
        _fields_ = [
            ("dwPacketNumber", ctypes.c_uint32),
            ("Gamepad", XINPUT_GAMEPAD),
        ]

    for dll_name in ["xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"]:
        try:
            dll = ctypes.windll.LoadLibrary(dll_name)
            if hasattr(dll, "XInputGetState"):
                _XINPUT_DLL = dll
                _XINPUT_STATE_CLASS = XINPUT_STATE
                return _XINPUT_DLL, _XINPUT_STATE_CLASS
        except Exception:
            continue
    return None, None

def get_connected_controllers():
    """Returns a list of connected controllers, or [] if none."""
    if sys.platform != "win32":
        return []
        
    found = []
    
    # 1. Check XInput (Xbox, DualShock 4/DualSense via DS4Windows, etc.)
    xinput, state_class = _get_xinput()
    if xinput and state_class:
        for user_index in range(4):
            try:
                state = state_class()
                res = xinput.XInputGetState(user_index, ctypes.byref(state))
                if res == 0:
                    found.append(f"Xbox / XInput Controller (Slot {user_index + 1})")
            except Exception:
                pass
        if found:
            return found
            
    # 2. Check WinMM joyGetPosEx (DirectInput generic controllers)
    try:
        winmm = ctypes.windll.winmm
        num_joys = winmm.joyGetNumDevs()
        for i in range(min(num_joys, 8)):
            buf = (ctypes.c_uint32 * 13)()
            buf[0] = 52 # dwSize
            buf[1] = 255 # dwFlags
            res = winmm.joyGetPosEx(i, ctypes.byref(buf))
            if res == 0:
                name = f"DirectInput Gamepad #{i + 1}"
                if name not in found:
                    found.append(name)
    except Exception:
        pass
        
    return found

if __name__ == "__main__":
    controllers = get_connected_controllers()
    print("Connected Controllers:", controllers)
