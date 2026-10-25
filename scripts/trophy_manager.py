# SPDX-License-Identifier: GPL-2.0-or-later
"""
PlayStation 4 Trophy / Achievement Manager for Kamen Rider: Memory of Heroes (CUSA17374)
Provides authentic 50-trophy catalog (1 Platinum, 1 Gold, 10 Silver, 38 Bronze)
matching CUSA17374/sce_sys/trophy/trophy00.trp with bilingual metadata (English & Bahasa Indonesia).
"""

import json
from pathlib import Path

# Complete Official 50 PS4 Trophies matching CUSA17374 trophy00.trp (trop000.png to trop049.png)
TROPHIES_DB = [
    {
        "id": 0,
        "icon_idx": 0,
        "type": "platinum",
        "name_en": "Total Conquest",
        "name_id": "Penaklukan Mutlak",
        "desc_en": "Acquired all trophies in Kamen Rider: Memory of Heroes.",
        "desc_id": "Membuka seluruh piala/prestasi di Kamen Rider: Memory of Heroes.",
        "points": 100
    },
    {
        "id": 1,
        "icon_idx": 1,
        "type": "gold",
        "name_en": "Case Closed",
        "name_id": "Kasus Ditutup",
        "desc_en": "Completed the entire story from Prologue through the Grand Finale.",
        "desc_id": "Menyelesaikan seluruh babak cerita dari Prolog hingga Babak Final.",
        "points": 50
    },
    {
        "id": 2,
        "icon_idx": 2,
        "type": "silver",
        "name_en": "Battle Master",
        "name_id": "Ahli Pertarungan",
        "desc_en": "Achieved an evaluation of SSS in battle 100 times.",
        "desc_id": "Mendapatkan evaluasi peringkat SSS dalam pertarungan sebanyak 100 kali.",
        "points": 30
    },
    {
        "id": 3,
        "icon_idx": 3,
        "type": "silver",
        "name_en": "Finishing Move Master",
        "name_id": "Ahli Jurus Pamungkas",
        "desc_en": "Executed a Finishing Move with all playable Kamen Riders.",
        "desc_id": "Melancarkan jurus pamungkas Finisher dengan semua Kamen Rider.",
        "points": 30
    },
    {
        "id": 4,
        "icon_idx": 4,
        "type": "silver",
        "name_en": "Counterattack Master",
        "name_id": "Ahli Serangan Balik",
        "desc_en": "Used a counterattack for the 100th time in combat.",
        "desc_id": "Melakukan serangan balik (counterattack) sebanyak 100 kali.",
        "points": 30
    },
    {
        "id": 5,
        "icon_idx": 5,
        "type": "silver",
        "name_en": "Form Chain Master",
        "name_id": "Ahli Rantai Form",
        "desc_en": "Used a Form Chain combo for the 100th time.",
        "desc_id": "Menggunakan kombo pergantian wujud Form Chain sebanyak 100 kali.",
        "points": 30
    },
    {
        "id": 6,
        "icon_idx": 6,
        "type": "silver",
        "name_en": "Enemy Hunter",
        "name_id": "Pemburu Musuh",
        "desc_en": "Defeated 1,000 enemy combatants across Sector City.",
        "desc_id": "Mengalahkan 1.000 musuh di seluruh kawasan Pulau Sektor.",
        "points": 30
    },
    {
        "id": 7,
        "icon_idx": 7,
        "type": "silver",
        "name_en": "Chain Master",
        "name_id": "Ahli Rentetan Kombo",
        "desc_en": "Achieved a continuous combo chain of 200 hits.",
        "desc_id": "Mencapai rentetan kombo tanpa putus hingga 200 hit.",
        "points": 30
    },
    {
        "id": 8,
        "icon_idx": 8,
        "type": "silver",
        "name_en": "Enemy Code Collector",
        "name_id": "Kolektor Kode Musuh",
        "desc_en": "Acquired a total of 100,000 Enemy Codes.",
        "desc_id": "Mengumpulkan total 100.000 Enemy Code dari pertempuran.",
        "points": 30
    },
    {
        "id": 9,
        "icon_idx": 9,
        "type": "silver",
        "name_en": "Master Searcher",
        "name_id": "Pencari Handal",
        "desc_en": "Acquired 20 Accelerator blueprints hidden across the island.",
        "desc_id": "Menemukan 20 cetak biru (blueprint) Accelerator di Pulau Sektor.",
        "points": 30
    },
    {
        "id": 10,
        "icon_idx": 10,
        "type": "silver",
        "name_en": "Master Developer",
        "name_id": "Pengembang Handal",
        "desc_en": "Developed 20 different Accelerators.",
        "desc_id": "Mengembangkan 20 variasi perlengkapan Accelerator.",
        "points": 30
    },
    {
        "id": 11,
        "icon_idx": 11,
        "type": "silver",
        "name_en": "DOUBLE's Awakening",
        "name_id": "Kebangkitan DOUBLE",
        "desc_en": "Acquired all Skill Gains and upgrades for Kamen Rider DOUBLE.",
        "desc_id": "Membuka seluruh perolehan Skill dan peningkatan untuk Kamen Rider DOUBLE.",
        "points": 30
    },
    {
        "id": 12,
        "icon_idx": 12,
        "type": "bronze",
        "name_en": "Infiltrating the City Sector",
        "name_id": "Menyusup ke Sektor Kota",
        "desc_en": "Began investigating the City Sector.",
        "desc_id": "Memulai investigasi rahasia di Sektor Kota.",
        "points": 15
    },
    {
        "id": 13,
        "icon_idx": 13,
        "type": "bronze",
        "name_en": "Infiltrating the Forest Sector",
        "name_id": "Menyusup ke Sektor Hutan",
        "desc_en": "Began investigating the Forest Sector.",
        "desc_id": "Memulai investigasi rahasia di Sektor Hutan.",
        "points": 15
    },
    {
        "id": 14,
        "icon_idx": 14,
        "type": "bronze",
        "name_en": "Infiltrating the Water Purification Sector",
        "name_id": "Menyusup ke Sektor Pengolahan Air",
        "desc_en": "Began investigating the Water Purification Sector.",
        "desc_id": "Memulai investigasi rahasia di Sektor Pengolahan Air.",
        "points": 15
    },
    {
        "id": 15,
        "icon_idx": 15,
        "type": "bronze",
        "name_en": "Infiltrating the Harbor Sector",
        "name_id": "Menyusup ke Sektor Pelabuhan",
        "desc_en": "Began investigating the Harbor Sector.",
        "desc_id": "Memulai investigasi rahasia di Sektor Pelabuhan.",
        "points": 15
    },
    {
        "id": 16,
        "icon_idx": 16,
        "type": "bronze",
        "name_en": "Infiltrating the Waste Disposal Sector",
        "name_id": "Menyusup ke Sektor Pembuangan Limbah",
        "desc_en": "Began investigating the Waste Disposal Sector.",
        "desc_id": "Memulai investigasi rahasia di Sektor Pembuangan Limbah.",
        "points": 15
    },
    {
        "id": 17,
        "icon_idx": 17,
        "type": "bronze",
        "name_en": "Infiltrating the Desert Sector",
        "name_id": "Menyusup ke Sektor Gurun",
        "desc_en": "Began investigating the Desert Sector.",
        "desc_id": "Memulai investigasi rahasia di Sektor Gurun.",
        "points": 15
    },
    {
        "id": 18,
        "icon_idx": 18,
        "type": "bronze",
        "name_en": "Infiltrating the Swamp Sector",
        "name_id": "Menyusup ke Sektor Rawa",
        "desc_en": "Began investigating the Swamp Sector.",
        "desc_id": "Memulai investigasi rahasia di Sektor Rawa.",
        "points": 15
    },
    {
        "id": 19,
        "icon_idx": 19,
        "type": "bronze",
        "name_en": "Infiltrating the Refining Sector",
        "name_id": "Menyusup ke Sektor Kilang",
        "desc_en": "Began investigating the Refining Sector.",
        "desc_id": "Memulai investigasi rahasia di Sektor Kilang.",
        "points": 15
    },
    {
        "id": 20,
        "icon_idx": 20,
        "type": "bronze",
        "name_en": "Infiltrating the Wasteland Sector",
        "name_id": "Menyusup ke Sektor Tanah Gersang",
        "desc_en": "Began investigating the Wasteland Sector.",
        "desc_id": "Memulai investigasi rahasia di Sektor Tanah Gersang.",
        "points": 15
    },
    {
        "id": 21,
        "icon_idx": 21,
        "type": "bronze",
        "name_en": "Infiltrating the Center Tower",
        "name_id": "Menyusup ke Menara Pusat",
        "desc_en": "Began investigating the Center Tower.",
        "desc_id": "Memulai penyerbuan dan investigasi ke Menara Pusat.",
        "points": 15
    },
    {
        "id": 22,
        "icon_idx": 22,
        "type": "bronze",
        "name_en": "DOUBLE Player",
        "name_id": "Pemain DOUBLE",
        "desc_en": "Used Kamen Rider DOUBLE (W) in battle for the first time.",
        "desc_id": "Mengendalikan Kamen Rider DOUBLE (W) dalam pertarungan untuk pertama kali.",
        "points": 15
    },
    {
        "id": 23,
        "icon_idx": 23,
        "type": "bronze",
        "name_en": "OOO Player",
        "name_id": "Pemain OOO",
        "desc_en": "Used Kamen Rider OOO in battle for the first time.",
        "desc_id": "Mengendalikan Kamen Rider OOO dalam pertarungan untuk pertama kali.",
        "points": 15
    },
    {
        "id": 24,
        "icon_idx": 24,
        "type": "bronze",
        "name_en": "ZERO-ONE Player",
        "name_id": "Pemain ZERO-ONE",
        "desc_en": "Used Kamen Rider ZERO-ONE in battle for the first time.",
        "desc_id": "Mengendalikan Kamen Rider ZERO-ONE dalam pertarungan untuk pertama kali.",
        "points": 15
    },
    {
        "id": 25,
        "icon_idx": 25,
        "type": "bronze",
        "name_en": "ACCEL Player",
        "name_id": "Pemain ACCEL",
        "desc_en": "Used Kamen Rider ACCEL in battle for the first time.",
        "desc_id": "Mengendalikan Kamen Rider ACCEL dalam pertarungan untuk pertama kali.",
        "points": 15
    },
    {
        "id": 26,
        "icon_idx": 26,
        "type": "bronze",
        "name_en": "BIRTH Player",
        "name_id": "Pemain BIRTH",
        "desc_en": "Used Kamen Rider BIRTH in battle for the first time.",
        "desc_id": "Mengendalikan Kamen Rider BIRTH dalam pertarungan untuk pertama kali.",
        "points": 15
    },
    {
        "id": 27,
        "icon_idx": 27,
        "type": "bronze",
        "name_en": "PROTOBIRTH Player",
        "name_id": "Pemain PROTOBIRTH",
        "desc_en": "Used Kamen Rider Birth Prototype in battle for the first time.",
        "desc_id": "Mengendalikan Kamen Rider Birth Prototype dalam pertarungan untuk pertama kali.",
        "points": 15
    },
    {
        "id": 28,
        "icon_idx": 28,
        "type": "bronze",
        "name_en": "JOKER Player",
        "name_id": "Pemain JOKER",
        "desc_en": "Used Kamen Rider JOKER in battle for the first time.",
        "desc_id": "Mengendalikan Kamen Rider JOKER dalam pertarungan untuk pertama kali.",
        "points": 15
    },
    {
        "id": 29,
        "icon_idx": 29,
        "type": "bronze",
        "name_en": "FANGJOKER Player",
        "name_id": "Pemain FANGJOKER",
        "desc_en": "Used Kamen Rider DOUBLE FangJoker in battle for the first time.",
        "desc_id": "Mengendalikan Kamen Rider DOUBLE FangJoker dalam pertarungan untuk pertama kali.",
        "points": 15
    },
    {
        "id": 30,
        "icon_idx": 30,
        "type": "bronze",
        "name_en": "DOUBLE the Mighty",
        "name_id": "Ketangguhan DOUBLE",
        "desc_en": "Strengthened Kamen Rider DOUBLE to Max Level.",
        "desc_id": "Meningkatkan status Kamen Rider DOUBLE hingga Level Maksimal.",
        "points": 15
    },
    {
        "id": 31,
        "icon_idx": 31,
        "type": "bronze",
        "name_en": "OOO the Mighty",
        "name_id": "Ketangguhan OOO",
        "desc_en": "Strengthened Kamen Rider OOO to Max Level.",
        "desc_id": "Meningkatkan status Kamen Rider OOO hingga Level Maksimal.",
        "points": 15
    },
    {
        "id": 32,
        "icon_idx": 32,
        "type": "bronze",
        "name_en": "ZERO-ONE the Mighty",
        "name_id": "Ketangguhan ZERO-ONE",
        "desc_en": "Strengthened Kamen Rider ZERO-ONE to Max Level.",
        "desc_id": "Meningkatkan status Kamen Rider ZERO-ONE hingga Level Maksimal.",
        "points": 15
    },
    {
        "id": 33,
        "icon_idx": 33,
        "type": "bronze",
        "name_en": "ACCEL the Mighty",
        "name_id": "Ketangguhan ACCEL",
        "desc_en": "Strengthened Kamen Rider ACCEL to Max Level.",
        "desc_id": "Meningkatkan status Kamen Rider ACCEL hingga Level Maksimal.",
        "points": 15
    },
    {
        "id": 34,
        "icon_idx": 34,
        "type": "bronze",
        "name_en": "BIRTH the Mighty",
        "name_id": "Ketangguhan BIRTH",
        "desc_en": "Strengthened Kamen Rider BIRTH to Max Level.",
        "desc_id": "Meningkatkan status Kamen Rider BIRTH hingga Level Maksimal.",
        "points": 15
    },
    {
        "id": 35,
        "icon_idx": 35,
        "type": "bronze",
        "name_en": "PROTOBIRTH the Mighty",
        "name_id": "Ketangguhan PROTOBIRTH",
        "desc_en": "Strengthened Birth Prototype to Max Level.",
        "desc_id": "Meningkatkan status Birth Prototype hingga Level Maksimal.",
        "points": 15
    },
    {
        "id": 36,
        "icon_idx": 36,
        "type": "bronze",
        "name_en": "JOKER the Mighty",
        "name_id": "Ketangguhan JOKER",
        "desc_en": "Strengthened Kamen Rider JOKER to Max Level.",
        "desc_id": "Meningkatkan status Kamen Rider JOKER hingga Level Maksimal.",
        "points": 15
    },
    {
        "id": 37,
        "icon_idx": 37,
        "type": "bronze",
        "name_en": "OOO's Awakening",
        "name_id": "Kebangkitan OOO",
        "desc_en": "Acquired all Skill Gains and abilities for Kamen Rider OOO.",
        "desc_id": "Membuka seluruh perolehan Skill dan kemampuan untuk Kamen Rider OOO.",
        "points": 15
    },
    {
        "id": 38,
        "icon_idx": 38,
        "type": "bronze",
        "name_en": "ZERO-ONE's Awakening",
        "name_id": "Kebangkitan ZERO-ONE",
        "desc_en": "Acquired all Skill Gains and abilities for Kamen Rider ZERO-ONE.",
        "desc_id": "Membuka seluruh perolehan Skill dan kemampuan untuk Kamen Rider ZERO-ONE.",
        "points": 15
    },
    {
        "id": 39,
        "icon_idx": 39,
        "type": "bronze",
        "name_en": "ACCEL's Awakening",
        "name_id": "Kebangkitan ACCEL",
        "desc_en": "Acquired all Skill Gains and abilities for Kamen Rider ACCEL.",
        "desc_id": "Membuka seluruh perolehan Skill dan kemampuan untuk Kamen Rider ACCEL.",
        "points": 15
    },
    {
        "id": 40,
        "icon_idx": 40,
        "type": "bronze",
        "name_en": "Form Chain Beginner",
        "name_id": "Pemula Rantai Form",
        "desc_en": "Used a Form Chain in battle for the first time.",
        "desc_id": "Menggunakan kombo pertukaran form dalam aksi untuk pertama kali.",
        "points": 15
    },
    {
        "id": 41,
        "icon_idx": 41,
        "type": "bronze",
        "name_en": "Battle Beginner",
        "name_id": "Pemula Pertarungan",
        "desc_en": "Achieved an evaluation of SSS in battle for the first time.",
        "desc_id": "Mencapai evaluasi peringkat SSS dalam pertarungan untuk pertama kali.",
        "points": 15
    },
    {
        "id": 42,
        "icon_idx": 42,
        "type": "bronze",
        "name_en": "Finishing Move Beginner",
        "name_id": "Pemula Jurus Pamungkas",
        "desc_en": "Used a Finishing Move to defeat an enemy for the first time.",
        "desc_id": "Menumbangkan musuh menggunakan serangan pamungkas Finisher pertama kali.",
        "points": 15
    },
    {
        "id": 43,
        "icon_idx": 43,
        "type": "bronze",
        "name_en": "Counterattack Beginner",
        "name_id": "Pemula Serangan Balik",
        "desc_en": "Used a counterattack timing in battle for the first time.",
        "desc_id": "Berhasil mengeksekusi serangan balik (counterattack) untuk pertama kali.",
        "points": 15
    },
    {
        "id": 44,
        "icon_idx": 44,
        "type": "bronze",
        "name_en": "Beginner Searcher",
        "name_id": "Pencari Pemula",
        "desc_en": "Acquired 5 Accelerator blueprints.",
        "desc_id": "Menemukan 5 cetak biru (blueprint) Accelerator di lapangan.",
        "points": 15
    },
    {
        "id": 45,
        "icon_idx": 45,
        "type": "bronze",
        "name_en": "Beginner Developer",
        "name_id": "Pengembang Pemula",
        "desc_en": "Developed an Accelerator item for the first time.",
        "desc_id": "Mengembangkan perlengkapan Accelerator untuk pertama kali.",
        "points": 15
    },
    {
        "id": 46,
        "icon_idx": 46,
        "type": "bronze",
        "name_en": "Gadget Detective",
        "name_id": "Detektif Gadget Memori",
        "desc_en": "Utilized Memory Gadgets (Bat Shot, Spider Shock, Denden Sensor) 25 times in exploration.",
        "desc_id": "Menggunakan Gadget Memori 25 kali dalam eksplorasi dan penyelidikan.",
        "points": 15
    },
    {
        "id": 47,
        "icon_idx": 47,
        "type": "bronze",
        "name_en": "Critical Counter Master",
        "name_id": "Ahli Serangan Balik Kritis",
        "desc_en": "Successfully performed 30 perfect dodges and counter attacks.",
        "desc_id": "Berhasil melakukan 30 kali hindaran sempurna dan serangan balik kritis.",
        "points": 15
    },
    {
        "id": 48,
        "icon_idx": 48,
        "type": "bronze",
        "name_en": "Tri-Rider Tag Synergy",
        "name_id": "Sinergi Tiga Kamen Rider",
        "desc_en": "Executed a continuous chain attack involving Double, OOO, and Zero-One.",
        "desc_id": "Melakukan serangan berantai bersama Double, OOO, dan Zero-One.",
        "points": 15
    },
    {
        "id": 49,
        "icon_idx": 49,
        "type": "bronze",
        "name_en": "Survival Instinct",
        "name_id": "Insting Bertahan Hidup",
        "desc_en": "Defeated a stage boss while having less than 10% health remaining.",
        "desc_id": "Mengalahkan bos area saat darah (HP) Anda tersisa di bawah 10%.",
        "points": 15
    }
]

def get_trophies_path(base_dir: Path) -> Path:
    return base_dir / "bin" / "user" / "trophies_state.json"

def load_trophies(base_dir: Path) -> list:
    """Load trophies with unlocked status."""
    state_file = get_trophies_path(base_dir)
    unlocked_map = {}
    
    if state_file.is_file():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                unlocked_map = json.load(f)
        except Exception:
            pass

    save_dir = base_dir / "bin" / "user" / "home" / "1000" / "savedata" / "CUSA17374"
    has_save = save_dir.exists() and any(save_dir.iterdir())
    
    result = []
    for item in TROPHIES_DB:
        t_id = str(item["id"])
        is_unlocked = unlocked_map.get(t_id, False)
        
        # Default unlock some early trophies if user has an active savegame
        if not unlocked_map and has_save and item["id"] in [12, 13, 22, 40, 41, 42]:
            is_unlocked = True
            unlocked_map[t_id] = True
            
        t_copy = dict(item)
        t_copy["unlocked"] = is_unlocked
        result.append(t_copy)
        
    return result

def toggle_trophy_unlock(base_dir: Path, trophy_id: int) -> bool:
    """Toggle a trophy for user testing/unlocking."""
    state_file = get_trophies_path(base_dir)
    unlocked_map = {}
    if state_file.is_file():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                unlocked_map = json.load(f)
        except Exception:
            pass
            
    t_id = str(trophy_id)
    curr = unlocked_map.get(t_id, False)
    unlocked_map[t_id] = not curr
    
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(unlocked_map, f, indent=2)
        
    return unlocked_map[t_id]
