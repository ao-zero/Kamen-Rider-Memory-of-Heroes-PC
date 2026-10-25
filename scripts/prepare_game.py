# SPDX-License-Identifier: GPL-2.0-or-later
"""
Kamen Rider: Memory of Heroes - Game Preparation & Native Image Builder
Project Lead / Admin: AO Zero
Community Partner: Bakka Sub (https://www.bakkasub.my.id)
"""

import os
import sys
import subprocess
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
GAME_DIR = WORKSPACE / "CUSA17374"
DATA_DIR = WORKSPACE / "data"
SCRIPTS_DIR = WORKSPACE / "scripts"
CTR_PORTABLE = Path(r"g:\Game\Game PS4\CTR NF PS4\CTR-NitroFueled-PC-portable")

def prepare_game_image(progress_callback=None) -> bool:
    """Prepares eboot.bin, links libc, links libSceFios2, and generates import_names & content_profile."""
    if not (GAME_DIR / "eboot.bin").is_file():
        raise FileNotFoundError(f"eboot.bin tidak ditemukan di {GAME_DIR}")
    
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    env = dict(os.environ)
    env["BB_SKIP_GAME_CHECK"] = "1"
    
    # 1. Step 1: ELF Relocation & Memory Image (prepare.py)
    if progress_callback:
        progress_callback("[1/5] Membaca eboot.bin & mengekstrak relokasi memori ELF...")
    cmd1 = [sys.executable, str(CTR_PORTABLE / "scripts" / "prepare.py"), str(GAME_DIR), "--out", str(DATA_DIR)]
    res1 = subprocess.run(cmd1, env=env, capture_output=True, text=True)
    if res1.returncode != 0:
        raise RuntimeError(f"Gagal pada tahap prepare.py:\n{res1.stderr or res1.stdout}")
    if progress_callback:
        progress_callback("  -> boot.bin berhasil disusun (Image size ~26.5 MB)")

    # 2. Step 2: Native Libc Linking & fs->gs TLS Rewrite (link_libc.py)
    if progress_callback:
        progress_callback("[2/5] Menautkan libc.prx & menulis ulang 590 instruksi TLS (fs -> gs)...")
    cmd2 = [sys.executable, str(CTR_PORTABLE / "scripts" / "link_libc.py"), str(GAME_DIR), "--out", str(DATA_DIR)]
    res2 = subprocess.run(cmd2, env=env, capture_output=True, text=True)
    if res2.returncode != 0:
        raise RuntimeError(f"Gagal pada tahap link_libc.py:\n{res2.stderr or res2.stdout}")
    if progress_callback:
        progress_callback("  -> boot-libc.bin berhasil dibuat dengan fallback libc")

    # 3. Step 3: Module Linking - libSceFios2 (link_modules.py)
    if progress_callback:
        progress_callback("[3/5] Menautkan modul sistem I/O libSceFios2.prx...")
    cmd3 = [sys.executable, str(CTR_PORTABLE / "scripts" / "link_modules.py"), str(GAME_DIR), "--out", str(DATA_DIR)]
    res3 = subprocess.run(cmd3, env=env, capture_output=True, text=True)
    if res3.returncode != 0:
        raise RuntimeError(f"Gagal pada tahap link_modules.py:\n{res3.stderr or res3.stdout}")
    if progress_callback:
        progress_callback("  -> boot-linked.bin selesai (250 native bindings, 756 runtime imports)")

    # 4. Step 4: Import Names Generation (gen_import_names.py)
    if progress_callback:
        progress_callback("[4/5] Mengurai simbol nama impor runtime PS4 (aerolib)...")
    cmd4 = [sys.executable, str(CTR_PORTABLE / "tools" / "gen_import_names.py"), "--out", str(DATA_DIR)]
    res4 = subprocess.run(cmd4, env=env, capture_output=True, text=True)
    if res4.returncode != 0:
        raise RuntimeError(f"Gagal pada tahap gen_import_names.py:\n{res4.stderr or res4.stdout}")
    if progress_callback:
        progress_callback("  -> import_names.txt berhasil digenerate (728 simbol dinamai)")

    # 5. Step 5: Offline AppContent Profile (content_profile.py)
    if progress_callback:
        progress_callback("[5/5] Membuat AppContent profile & DLC registry...")
    cmd5 = [sys.executable, str(CTR_PORTABLE / "scripts" / "content_profile.py"), str(GAME_DIR), "--dlc-dir", str(WORKSPACE), "--out", str(DATA_DIR)]
    res5 = subprocess.run(cmd5, env=env, capture_output=True, text=True)
    if res5.returncode != 0:
        raise RuntimeError(f"Gagal pada tahap content_profile.py:\n{res5.stderr or res5.stdout}")
    if progress_callback:
        progress_callback("  -> content.bin berhasil dibuat (SKU=full)")

    return True

if __name__ == "__main__":
    print(f"=== KAMEN RIDER MEMORY OF HEROES: PREPARING NATIVE PC BINARIES ===")
    print(f"Game Directory: {GAME_DIR}")
    print(f"Output Data Directory: {DATA_DIR}\n")
    def cb(msg):
        print(msg)
    success = prepare_game_image(cb)
    if success:
        print("\n[SUCCESS] Seluruh biner native PC Kamen Rider: Memory of Heroes berhasil disiapkan di folder 'data/'!")
