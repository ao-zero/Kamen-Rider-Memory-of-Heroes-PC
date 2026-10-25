/* ==========================================================================
   KAMEN RIDER: MEMORY OF HEROES - PC NATIVE EDITION LAUNCHER JAVASCRIPT
   Two-Way IPC Bridge via window.pywebview.api
   Features: Bilingual (ID/EN), Saves Manager, Trophy Tracker, Auto-Update
   Port Lead: AO Zero | Partner: Bakka Sub (www.bakkasub.my.id)
   ========================================================================== */

// Bilingual Translation Dictionary
const I18N = {
  id: {
    menu_header: "MAIN MENU",
    tab_play: "Mulai Main",
    tab_settings: "Pengaturan",
    tab_gamepad: "Kontrol Stik",
    tab_keyboard: "Keyboard & Mouse",
    tab_saves: "Custom Save",
    tab_pkg: "DLC & Update",
    tab_achievements: "Prestasi (Trophy)",
    tab_tools: "Alat & Update",
    tab_community: "Komunitas",
    system_ready: "Sistem Siap 60 FPS",
    port_lead: "Port Lead:",
    partner: "Partner:",
    section_game: "Informasi Game",
    profile: "Profil:",
    mode: "Mode:",
    btn_change_folder: "Change game folder...",
    btn_play: "PLAY GAME",
    btn_create_shortcut: "Create Desktop Shortcut",
    btn_open_game_folder: "Buka Folder Game",
    btn_open_saves: "Buka Folder Save",
    section_log: "Log & Status Engine",
    section_presets: "1-Click Optimization Presets",
    section_perf: "— Performance —",
    lbl_fps: "Target Frame Rate (FPS Limit):",
    lbl_vsync: "VSync & Presentation:",
    chk_async_shaders: "Compile shaders in the background (Fast Math & Async Pipelines)",
    chk_show_fps: "FPS counter in the corner",
    chk_show_hud: "Performance & Frame Time HUD in the corner",
    section_display: "— Display & Resolution —",
    lbl_res: "Internal Resolution / Render Scale:",
    lbl_aspect: "Aspect Ratio:",
    lbl_upscaler: "Upscaling Engine:",
    lbl_upscaler_qual: "Upscaler Quality:",
    chk_fullscreen: "Fullscreen",
    chk_borderless: "Borderless window (Seamless Alt-Tab)",
    chk_hide_launcher: "Sembunyikan launcher saat game berjalan",
    section_sound: "— Sound & Audio —",
    lbl_volume: "Master Audio Volume:",
    section_pad_mapping: "— Gamepad Button Mapping —",
    pad_desc: "Mendukung Xbox, PlayStation (DualShock / DualSense), Switch Pro, dan Controller Universal. Klik 'Ubah' untuk memetakan tombol.",
    lbl_deadzone: "Analog Stick Deadzone:",
    th_action: "Aksi Game",
    th_assigned: "Tombol Stik",
    th_remap: "Atur",
    btn_remap: "Ubah",
    btn_restore_pad: "Kembalikan Default Controller",
    section_kbm_mapping: "— Keyboard & Mouse Controls (Auto-Sync) —",
    mouse_sync_title: "Zero-Touch Mouse Aim Aktif Otomatis!",
    mouse_sync_desc: "Kamera mouse langsung sinkron secara otomatis saat game dijalankan. Tidak perlu menekan tombol F7 secara manual. Kursor mouse akan terkunci di dalam game.",
    lbl_mouse_sens: "Sensitivitas Kamera Mouse (Look Sensitivity):",
    btn_restore_kbm: "Kembalikan Default Keyboard & Mouse",
    section_saves: "Custom Savegame Manager",
    saves_desc: "Kelola slot penyimpanan game, backup data simpanan, pasang preset save 100% tamat, atau pulihkan backup sebelumnya.",
    btn_backup_saves: "Backup Semua Save",
    btn_load_100: "Pasang Save 100% Tamat",
    btn_open_saves_folder: "Buka Folder Savegame",
    btn_refresh: "Segarkan",
    hdr_detected_saves: "Slot Save Terdeteksi (CUSA17374):",
    hdr_restore_backup: "Pulihkan Backup Tersimpan:",
    opt_no_backups: "Belum ada file backup tersimpan...",
    btn_restore: "Pulihkan Backup",
    section_dlc: "— DLC & Update Installer —",
    dlc_desc: "Pasang file paket update v1.01 atau DLC PS4 (.pkg) secara otomatis ke dalam folder game.",
    hdr_pkgs_found: "File .PKG Terdeteksi di Folder:",
    btn_browse_pkg: "Pilih File PKG Manual...",
    section_achievements: "Prestasi & Trophy PlayStation",
    filter_all: "Semua (50)",
    filter_unlocked: "Terbuka",
    filter_locked: "Terkunci",
    btn_test_trophy: "Tes Notifikasi",
    section_updates: "— Updates & Versi —",
    installed_ver: "Versi Terpasang: v1.0.0-PC-Native",
    btn_check_updates: "Check for Updates",
    chk_update_startup: "Check for updates when the launcher opens",
    section_installation: "— Pengaturan & Migrasi Instalasi —",
    btn_import_settings: "Bring settings from another installation...",
    btn_reset_settings: "Reset Semua Pengaturan ke Default Pabrik",
    section_folders: "— Folders and Log —",
    btn_open_log: "Open last run log",
    btn_open_port: "Open the port folder",
    btn_open_game: "Open the game folder",
    chk_detailed_log: "Save a detailed log (with frame statistics)",
    section_diagnostics: "— Diagnosa Hardware & Integritas Game —",
    btn_run_gpu_diag: "Cek Kemampuan GPU & Driver Vulkan",
    btn_verify_files: "Verifikasi Integritas File Game (eboot.bin)",
    btn_clean_temp: "Bersihkan File Sementara & Crash Dump",
    section_desktop: "— Desktop Shortcut —",
    section_shader: "— Shader Cache —",
    shader_desc: "Shader disimpan agar sesi berikutnya berjalan mulus. Hapus cache jika Anda baru saja update driver GPU atau mengalami glitch grafis.",
    btn_clear_shader: "Clear the shader cache",
    section_lang: "— Launcher Language / Bahasa —",
    section_community: "Komunitas & Pengembang",
    lead_desc: "Pengembang utama Native PC Port Launcher, optimasi Vulkan 1.3 60 FPS, Auto-Sync Mouse Look, dan Remapper Input.",
    partner_desc: "Penyedia takarir (fansub) Tokusatsu Indonesia terdepan. Kunjungi www.bakkasub.my.id untuk update Kamen Rider terbaru!",
    modal_hint: "Klik tombol yang diinginkan pada stik controller Anda di bawah ini:"
  },
  en: {
    menu_header: "MAIN MENU",
    tab_play: "Play",
    tab_settings: "Settings",
    tab_gamepad: "Gamepad",
    tab_keyboard: "Keyboard",
    tab_saves: "Saves",
    tab_pkg: "DLC & Patches",
    tab_achievements: "Achievements",
    tab_tools: "Tools",
    tab_community: "Community",
    system_ready: "System Ready (60 FPS)",
    port_lead: "Port Lead:",
    partner: "Partner:",
    section_game: "Game Information",
    profile: "Profile:",
    mode: "Mode:",
    btn_change_folder: "Change game folder...",
    btn_play: "PLAY GAME",
    btn_create_shortcut: "Create Desktop Shortcut",
    btn_open_game_folder: "Open Game Folder",
    btn_open_saves: "Open Saves Folder",
    section_log: "Engine Log & Status",
    section_presets: "1-Click Optimization Presets",
    section_perf: "— Performance —",
    lbl_fps: "Target Frame Rate (FPS Limit):",
    lbl_vsync: "VSync & Presentation:",
    chk_async_shaders: "Compile shaders in the background (Fast Math & Async Pipelines)",
    chk_show_fps: "FPS counter in the corner",
    chk_show_hud: "Performance & Frame Time HUD in the corner",
    section_display: "— Display & Resolution —",
    lbl_res: "Internal Resolution / Render Scale:",
    lbl_aspect: "Aspect Ratio:",
    lbl_upscaler: "Upscaling Engine:",
    lbl_upscaler_qual: "Upscaler Quality:",
    chk_fullscreen: "Fullscreen",
    chk_borderless: "Borderless window (Seamless Alt-Tab)",
    chk_hide_launcher: "Hide launcher during gameplay",
    section_sound: "— Sound & Audio —",
    lbl_volume: "Master Audio Volume:",
    section_pad_mapping: "— Gamepad Button Mapping —",
    pad_desc: "Supports Xbox, PlayStation (DualShock / DualSense), Switch Pro, and generic controllers. Press 'Change' to map buttons.",
    lbl_deadzone: "Analog Stick Deadzone:",
    th_action: "Game Action",
    th_assigned: "Controller Button",
    th_remap: "Remap",
    btn_remap: "Change",
    btn_restore_pad: "Restore Controller Defaults",
    section_kbm_mapping: "— Keyboard & Mouse Controls (Auto-Sync) —",
    mouse_sync_title: "Zero-Touch Mouse Aim Auto-Engaged!",
    mouse_sync_desc: "Mouse camera aim synchronizes automatically upon boot. No manual F7 press required. Cursor locks seamlessly inside the game.",
    lbl_mouse_sens: "Mouse Camera Look Sensitivity:",
    btn_restore_kbm: "Restore Keyboard & Mouse Defaults",
    section_saves: "Custom Savegame Manager",
    saves_desc: "Manage game save slots, backup save files, apply 100% completed save presets, or restore prior backups.",
    btn_backup_saves: "Backup All Saves",
    btn_load_100: "Load 100% Complete Save Preset",
    btn_open_saves_folder: "Open Saves Folder",
    btn_refresh: "Refresh",
    hdr_detected_saves: "Detected Save Slots (CUSA17374):",
    hdr_restore_backup: "Restore Existing Backup:",
    opt_no_backups: "No backup archives found...",
    btn_restore: "Restore Backup",
    section_dlc: "— DLC & Update Installer —",
    dlc_desc: "Install v1.01 update or PS4 DLC package (.pkg) files directly into your game directory.",
    hdr_pkgs_found: "Detected .PKG Files in Root:",
    btn_browse_pkg: "Browse Manual PKG...",
    section_achievements: "PlayStation Trophies & Achievements",
    filter_all: "All (50)",
    filter_unlocked: "Unlocked",
    filter_locked: "Locked",
    btn_test_trophy: "Test Notification",
    section_updates: "— Updates & Version —",
    installed_ver: "Installed Version: v1.0.0-PC-Native",
    btn_check_updates: "Check for Updates",
    chk_update_startup: "Check for updates when the launcher opens",
    section_installation: "— Settings & Installation Migration —",
    btn_import_settings: "Bring settings from another installation...",
    btn_reset_settings: "Reset All Settings to Factory Default",
    section_folders: "— Folders and Log —",
    btn_open_log: "Open last run log",
    btn_open_port: "Open the port folder",
    btn_open_game: "Open the game folder",
    chk_detailed_log: "Save a detailed log (with frame statistics)",
    section_diagnostics: "— Hardware Diagnostics & File Integrity —",
    btn_run_gpu_diag: "Check GPU & Vulkan Driver Capabilities",
    btn_verify_files: "Verify Game File Integrity (eboot.bin)",
    btn_clean_temp: "Clean Temporary Files & Crash Traces",
    section_desktop: "— Desktop Shortcut —",
    section_shader: "— Shader Cache —",
    shader_desc: "Shaders are preserved for smooth future sessions. Clear shader cache only after GPU driver updates or graphic glitches.",
    btn_clear_shader: "Clear the shader cache",
    section_lang: "— Launcher Language —",
    section_community: "Community & Credits",
    lead_desc: "Lead developer of the Native PC Port Launcher, Vulkan 1.3 60 FPS optimizer, Zero-Touch Mouse Aim, and Input Remapper.",
    partner_desc: "Leading Indonesian Tokusatsu fansub provider. Visit www.bakkasub.my.id for the latest Kamen Rider subtitle releases!",
    modal_hint: "Click the desired gamepad button from the options below:"
  }
};

let currentLang = 'id';
let cachedKeybinds = {};
let cachedTrophies = [];
let activeTrophyFilter = 'all';
let currentMappingAction = null;

// ==========================================================================
// LANGUAGE SWITCHER
// ==========================================================================
function setLanguage(lang) {
  currentLang = lang;
  const dict = I18N[lang] || I18N.id;

  // Update elements with data-i18n
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (dict[key]) {
      el.textContent = dict[key];
    }
  });

  // Update quick button flag
  const flag = document.getElementById('langFlag');
  if (flag) flag.textContent = lang === 'id' ? '🇮🇩' : '🇬🇧';
  
  const label = document.getElementById('langLabel');
  if (label) label.textContent = lang === 'id' ? 'ID' : 'EN';

  const select = document.getElementById('selectLang');
  if (select) select.value = lang;

  // Re-render keybind tables so button labels ('Ubah' / 'Change') update dynamically
  if (cachedKeybinds && Object.keys(cachedKeybinds).length > 0) {
    renderKeybindTables(cachedKeybinds);
  }

  // Re-render trophies to update localized descriptions
  renderTrophies(cachedTrophies, activeTrophyFilter);

  // Persist language setting
  onSettingChanged();
}

function toggleLanguage() {
  setLanguage(currentLang === 'id' ? 'en' : 'id');
}

function onLanguageSelect(val) {
  setLanguage(val);
}

// ==========================================================================
// TAB SWITCHING
// ==========================================================================
document.querySelectorAll('.nav-tab').forEach(button => {
  button.addEventListener('click', () => {
    const tabKey = button.getAttribute('data-tab');
    document.querySelectorAll('.nav-tab').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

    button.classList.add('active');
    const targetPane = document.getElementById(`tab-${tabKey}`);
    if (targetPane) targetPane.classList.add('active');
  });
});

// ==========================================================================
// TERMINAL LOG HELPER
// ==========================================================================
function appendLog(message) {
  const terminal = document.getElementById('terminalLog');
  if (terminal) {
    terminal.textContent += `\n${message}`;
    terminal.scrollTop = terminal.scrollHeight;
  }
}
window.onInstallLog = appendLog;

function clearLog() {
  const terminal = document.getElementById('terminalLog');
  if (terminal) terminal.textContent = '[LOG CLEARED]';
}

// Gamepad changed notification
window.onGamepadChanged = function(name) {
  const badge = document.getElementById('badgeGamepad');
  if (badge) badge.textContent = `🎮 ${name}`;

  const cbox = document.getElementById('controllerStatusBox');
  if (cbox) {
    cbox.textContent = name.toLowerCase().includes('keyboard') 
      ? `○ ACTIVE: ${name} (Connect Xbox or PlayStation controller anytime)`
      : `● CONNECTED: ${name}`;
    cbox.style.color = name.toLowerCase().includes('keyboard') ? '#94A3B8' : '#34D399';
  }
};

window.onGameExited = function() {
  const btn = document.getElementById('btnLaunch');
  if (btn) {
    btn.disabled = false;
    btn.querySelector('#txtLaunchBtn').textContent = I18N[currentLang].btn_play;
  }
  const status = document.getElementById('footerStatus');
  if (status) status.textContent = "STATUS: READY TO PLAY (60 FPS NATIVE)";
  const dot = document.getElementById('statusDot');
  if (dot) dot.style.background = "#10B981";
};

// ==========================================================================
// INITIALIZATION
// ==========================================================================
function initLauncher() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.get_initial_data().then(data => {
      // 1. Language
      if (data.language) {
        setLanguage(data.language);
      }

      // 2. Paths & Player Name
      document.getElementById('inputGameDir').value = data.game_dir || '';
      if (data.player_name) {
        const pName = document.getElementById('lblPlayerName');
        if (pName) pName.textContent = data.player_name;
      }

      // 3. Settings controls
      document.getElementById('selectRes').value = data.resolution || '1080p (Native FHD)';
      document.getElementById('selectFps').value = data.fps || '60 FPS (Native Unlock)';
      document.getElementById('selectUpscaler').value = data.upscaler || 'Off (Native)';
      document.getElementById('selectUpscalerQuality').value = data.upscaler_quality || 'Quality (67%)';
      document.getElementById('selectAspect').value = data.aspect_ratio || '16:9';
      document.getElementById('selectVsync').value = data.vsync_mode || 'Mailbox (Fastest / Unlocked)';
      
      document.getElementById('chkFullscreen').checked = (data.fullscreen === 'true' || data.fullscreen === true);
      document.getElementById('chkBorderless').checked = (data.borderless === 'true' || data.borderless === true || data.borderless === undefined);
      document.getElementById('chkShowFps').checked = (data.show_fps === 'true' || data.show_fps === true);
      document.getElementById('chkShowPerfHud').checked = (data.show_perf_hud === 'true' || data.show_perf_hud === true);
      document.getElementById('chkCompileShaders').checked = (data.compile_shaders_bg === 'true' || data.compile_shaders_bg === true || data.compile_shaders_bg === undefined);
      document.getElementById('chkHideLauncher').checked = (data.hide_launcher_on_play === 'true' || data.hide_launcher_on_play === true);
      document.getElementById('chkUpdateStartup').checked = (data.check_updates_startup === 'true' || data.check_updates_startup === true || data.check_updates_startup === undefined);
      
      const vol = data.audio_volume || '100';
      document.getElementById('rngVolume').value = vol;
      document.getElementById('lblVolumeVal').textContent = `${vol}%`;

      // 4. Badges & Gamepad
      if (data.app_ver) {
        document.getElementById('badgeVer').textContent = `● UPDATE v${data.app_ver}`;
        document.getElementById('gameReadyText').textContent = `Ready: CUSA17374 v${data.app_ver} (PS4 Base Game Dump)`;
      }
      if (data.gamepad) {
        window.onGamepadChanged(data.gamepad);
      }

      // 5. PKGs, Saves, Trophies
      renderPkgList(data.detected_pkgs || []);
      renderSaveSlots(data.saves || []);
      renderBackups(data.backups || []);
      
      cachedTrophies = data.trophies || [];
      renderTrophies(cachedTrophies, 'all');

      loadKeybinds();
      appendLog('[READY] System configuration & engine shaders synchronized.');
    }).catch(err => {
      console.error("Failed to load initial data:", err);
      loadKeybinds();
    });
  } else {
    setTimeout(initLauncher, 100);
  }
}

window.addEventListener('pywebviewready', initLauncher);
window.addEventListener('DOMContentLoaded', initLauncher);

// ==========================================================================
// SETTINGS PERSISTENCE
// ==========================================================================
function onSettingChanged() {
  if (!window.pywebview || !window.pywebview.api) return;
  const settings = {
    game_dir: document.getElementById('inputGameDir').value,
    resolution: document.getElementById('selectRes').value,
    fps: document.getElementById('selectFps').value,
    upscaler: document.getElementById('selectUpscaler').value,
    upscaler_quality: document.getElementById('selectUpscalerQuality').value,
    aspect_ratio: document.getElementById('selectAspect').value,
    vsync_mode: document.getElementById('selectVsync').value,
    fullscreen: document.getElementById('chkFullscreen').checked,
    borderless: document.getElementById('chkBorderless').checked,
    show_fps: document.getElementById('chkShowFps').checked,
    show_perf_hud: document.getElementById('chkShowPerfHud').checked,
    compile_shaders_bg: document.getElementById('chkCompileShaders').checked,
    hide_launcher_on_play: document.getElementById('chkHideLauncher').checked,
    check_updates_startup: document.getElementById('chkUpdateStartup').checked,
    audio_volume: document.getElementById('rngVolume').value,
    language: currentLang
  };
  window.pywebview.api.save_settings(settings);
}

function onVolumeSlider(val) {
  document.getElementById('lblVolumeVal').textContent = `${val}%`;
  onSettingChanged();
}

// 1-Click Presets
function applyPreset(type) {
  if (type === 'potato') {
    document.getElementById('selectRes').value = '720p (Low-End PC)';
    document.getElementById('selectUpscaler').value = 'AMD FSR 1 (Potato PC / Fastest)';
    document.getElementById('selectUpscalerQuality').value = 'Performance (50%)';
    document.getElementById('selectFps').value = '60 FPS (Native Unlock)';
    appendLog('[OPTIMIZATION] Potato PC Preset Applied: 720p + AMD FSR Performance (50%) + 60 FPS Native');
  } else if (type === 'balanced') {
    document.getElementById('selectRes').value = '1080p (Native FHD)';
    document.getElementById('selectUpscaler').value = 'AMD FSR 3.1 (High Quality)';
    document.getElementById('selectUpscalerQuality').value = 'Quality (67%)';
    document.getElementById('selectFps').value = '60 FPS (Native Unlock)';
    appendLog('[OPTIMIZATION] Balanced Preset Applied: 1080p + AMD FSR 3.1 Quality + 60 FPS Native');
  } else if (type === 'fidelity') {
    document.getElementById('selectRes').value = '1080p (Native FHD)';
    document.getElementById('selectUpscaler').value = 'Off (Native)';
    document.getElementById('selectUpscalerQuality').value = 'Quality (67%)';
    document.getElementById('selectFps').value = '60 FPS (Native Unlock)';
    appendLog('[OPTIMIZATION] Native Ultra Fidelity Applied: 1080p Native + 60 FPS Locked');
  }
  onSettingChanged();
}

// ==========================================================================
// GAME DIRECTORY & LAUNCH
// ==========================================================================
function browseGameDir() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.browse_game_dir().then(res => {
      if (res && res.path) {
        document.getElementById('inputGameDir').value = res.path;
        if (res.app_ver) {
          document.getElementById('badgeVer').textContent = `● UPDATE v${res.app_ver}`;
          document.getElementById('gameReadyText').textContent = `Ready: CUSA17374 v${res.app_ver} (PS4 Base Game Dump)`;
        }
        appendLog(`[DIRECTORY] Game folder set to: ${res.path}`);
      }
    });
  }
}

function launchGame() {
  const btn = document.getElementById('btnLaunch');
  btn.disabled = true;
  btn.querySelector('#txtLaunchBtn').textContent = "HENSHIN IN PROGRESS...";

  const status = document.getElementById('footerStatus');
  if (status) status.textContent = "STATUS: GAME EXECUTING NATIVE (60 FPS)...";
  const dot = document.getElementById('statusDot');
  if (dot) dot.style.background = "#D8F800";

  onSettingChanged();

  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.launch_game().then(res => {
      if (res === "NO_GAME") {
        window.onGameExited();
      }
    }).catch(err => {
      alert("Launch Error: " + err);
      window.onGameExited();
    });
  }
}

// ==========================================================================
// SAVES MANAGER
// ==========================================================================
function renderSaveSlots(slots) {
  const container = document.getElementById('saveSlotsContainer');
  if (!container) return;
  container.innerHTML = '';

  if (slots.length === 0) {
    container.innerHTML = `<div style="grid-column: 1/-1; font-size: 12px; color: var(--text-dim); padding: 12px 0;">No save data detected in the user folder. Launch the game once to create saves.</div>`;
    return;
  }

  slots.forEach(slot => {
    const card = document.createElement('div');
    card.className = `save-slot-card ${slot.has_data ? 'active-save' : ''}`;
    card.innerHTML = `
      <div class="save-icon">${slot.folder === 'KmrSave' ? '⚙️' : '🎮'}</div>
      <div class="save-details">
        <div class="save-title">${slot.title}</div>
        <div class="save-meta">${slot.folder} • ${slot.size_kb} KB • ${slot.last_modified}</div>
      </div>
      <div class="save-badge">${slot.has_data ? 'DATA READY' : 'EMPTY'}</div>
    `;
    container.appendChild(card);
  });
}

function renderBackups(backups) {
  const select = document.getElementById('selectBackups');
  if (!select) return;
  select.innerHTML = '';

  if (backups.length === 0) {
    select.innerHTML = `<option value="">${I18N[currentLang].opt_no_backups}</option>`;
    return;
  }

  backups.forEach(b => {
    const opt = document.createElement('option');
    opt.value = b.name;
    opt.textContent = `📦 ${b.name} (${b.size_kb} KB - ${b.date})`;
    select.appendChild(opt);
  });
}

function refreshSavesList() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.get_saves().then(slots => renderSaveSlots(slots));
    window.pywebview.api.list_backups().then(backups => renderBackups(backups));
    appendLog('[SAVES] Save slots and backup archives refreshed.');
  }
}

function backupSaves() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.backup_saves().then(res => {
      alert(res.message);
      appendLog(`[BACKUP] ${res.message}`);
      refreshSavesList();
    });
  }
}

function restoreSelectedBackup() {
  const select = document.getElementById('selectBackups');
  const zip = select ? select.value : '';
  if (!zip) {
    alert("Please select a backup archive to restore.");
    return;
  }
  if (confirm(`Are you sure you want to restore saves from ${zip}? (Your current saves will be backed up automatically)`)) {
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.restore_backup(zip).then(res => {
        alert(res.message);
        appendLog(`[RESTORE] ${res.message}`);
        refreshSavesList();
      });
    }
  }
}

function install100SavePreset() {
  if (confirm("Install 100% Completed Save Preset? This unlocks all Riders, forms, and maximum upgrades. (Current saves will be safely backed up).")) {
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.install_100_save().then(res => {
        alert(res.message);
        appendLog(`[PRESET] ${res.message}`);
        refreshSavesList();
      });
    }
  }
}

function openSavesFolder() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.open_saves_folder();
  }
}

// ==========================================================================
// PLAYSTATION TROPHY / ACHIEVEMENTS TRACKER
// ==========================================================================
function renderTrophies(trophies, filter) {
  const container = document.getElementById('trophyListContainer');
  if (!container) return;
  container.innerHTML = '';

  let plat = 0, gold = 0, silver = 0, bronze = 0;

  trophies.forEach(t => {
    if (t.type === 'platinum') plat++;
    else if (t.type === 'gold') gold++;
    else if (t.type === 'silver') silver++;
    else if (t.type === 'bronze') bronze++;
  });

  const sP = document.getElementById('statPlatinum');
  const sG = document.getElementById('statGold');
  const sS = document.getElementById('statSilver');
  const sB = document.getElementById('statBronze');
  if (sP) sP.textContent = plat;
  if (sG) sG.textContent = gold;
  if (sS) sS.textContent = silver;
  if (sB) sB.textContent = bronze;

  const filtered = trophies.filter(t => {
    if (filter === 'unlocked') return t.unlocked;
    if (filter === 'locked') return !t.unlocked;
    return true;
  });

  filtered.forEach(t => {
    const card = document.createElement('div');
    card.className = `trophy-card ${t.unlocked ? 'unlocked' : 'locked'}`;
    const name = currentLang === 'id' ? (t.name_id || t.name_en) : t.name_en;
    const desc = currentLang === 'id' ? (t.desc_id || t.desc_en) : t.desc_en;
    const iconNum = String(t.icon_idx !== undefined ? t.icon_idx : t.id).padStart(3, '0');
    const artSrc = `assets/trophies/trop${iconNum}.png`;
    const cupSrc = `assets/custom_trophy/${t.type}.png`;

    card.innerHTML = `
      <div class="trophy-card-art-box">
        <img src="${artSrc}" alt="${name}" class="trophy-card-img" onerror="this.src='${cupSrc}'">
        <img src="${cupSrc}" alt="${t.type}" class="trophy-tier-badge" title="${t.type.toUpperCase()}">
      </div>
      <div class="trophy-card-info" onclick="previewTrophyPopup(${t.id})">
        <div class="trophy-card-title">${name}</div>
        <div class="trophy-card-desc">${desc}</div>
      </div>
      <div class="trophy-card-right">
        <div class="trophy-badge-pill ${t.type}">${t.type} • ${t.points} PTS</div>
        <button class="btn-trophy-test" onclick="previewTrophyPopup(${t.id})" title="Test Achievement Notification Popup">${currentLang === 'id' ? 'Tes Notif' : 'Test'}</button>
      </div>
    `;
    container.appendChild(card);
  });
}

let toastTimer = null;

function previewTrophyPopup(trophyId) {
  const trophy = cachedTrophies.find(x => x.id === trophyId) || cachedTrophies[0];
  if (!trophy) return;

  const toast = document.getElementById('ps4TrophyToast');
  if (!toast) return;

  const name = currentLang === 'id' ? (trophy.name_id || trophy.name_en) : trophy.name_en;
  const desc = currentLang === 'id' ? (trophy.desc_id || trophy.desc_en) : trophy.desc_en;
  const iconNum = String(trophy.icon_idx !== undefined ? trophy.icon_idx : trophy.id).padStart(3, '0');

  const art = document.getElementById('ps4ToastArt');
  const cup = document.getElementById('ps4ToastCup');
  const tier = document.getElementById('ps4ToastTier');
  const title = document.getElementById('ps4ToastTitle');
  const descEl = document.getElementById('ps4ToastDesc');

  if (art) art.src = `assets/trophies/trop${iconNum}.png`;
  if (cup) cup.src = `assets/custom_trophy/${trophy.type}.png`;
  if (tier) tier.textContent = trophy.type.toUpperCase();
  if (title) title.textContent = name;
  if (descEl) descEl.textContent = desc;
  const badgeEl = toast.querySelector('.ps4-toast-badge');
  if (badgeEl) badgeEl.textContent = '🏆 ACHIEVEMENT UNLOCKED';

  // Play authentic PlayStation trophy unlock chime
  try {
    const chime = document.getElementById('trophyChime');
    if (chime) {
      chime.currentTime = 0;
      chime.play().catch(() => {});
    }
  } catch (e) {}

  toast.classList.remove('hide');
  toast.classList.add('show');

  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    dismissTrophyToast();
  }, 5500);
}

function testPs4Toast() {
  previewTrophyPopup(0);
}

function dismissTrophyToast() {
  const toast = document.getElementById('ps4TrophyToast');
  if (!toast) return;
  toast.classList.add('hide');
  setTimeout(() => {
    toast.classList.remove('show');
    toast.classList.remove('hide');
  }, 320);
}

function filterTrophies(type) {
  activeTrophyFilter = type;
  document.querySelectorAll('.btn-filter').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  renderTrophies(cachedTrophies, type);
}

// ==========================================================================
// AUTO UPDATER & LOGS
// ==========================================================================
function checkForUpdates() {
  const status = document.getElementById('updateStatusText');
  if (status) status.textContent = "Checking GitHub Releases...";
  
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.check_updates().then(res => {
      if (res.up_to_date) {
        if (status) status.textContent = `● You are running the latest version (${res.current})`;
        alert(`You are up to date! Installed: ${res.current}`);
      } else {
        if (status) status.textContent = `● New update available: ${res.latest}`;
        if (confirm(`New update available: ${res.latest}\nWould you like to open the GitHub Releases page?`)) {
          window.pywebview.api.open_external(res.url);
        }
      }
    });
  }
}

function openLastRunLog() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.open_last_log();
  }
}

function openGameFolder() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.open_game_folder();
  }
}

function openPortFolder() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.open_port_folder();
  }
}

function verifyGameFiles() {
  appendLog('[INTEGRITY] Verifying game executable and assets...');
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.verify_game_files().then(res => {
      alert(res.message);
      appendLog(`[INTEGRITY] ${res.message}`);
    });
  }
}

function runGpuDiagnostic() {
  appendLog('[HARDWARE] Running GPU & Vulkan Driver capabilities check...');
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.run_gpu_diagnostic().then(res => {
      alert(`GPU & Vulkan Diagnostic:\n\n${res.details}`);
      appendLog(`[HARDWARE] Diagnostic results:\n${res.details}`);
    });
  }
}

function cleanTempFiles() {
  if (confirm("Clean temporary files, crash traces, and stale cache buffers?")) {
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.clean_temp_files().then(msg => {
        alert(msg);
        appendLog(`[CLEANUP] ${msg}`);
      });
    }
  }
}

function importSettings() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.import_settings().then(res => {
      alert(res.message);
      if (res.success) {
        initLauncher();
      }
    });
  }
}

function resetAllSettings() {
  if (confirm("Reset ALL launcher graphics profiles, settings, and keybinds to factory default?")) {
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.reset_all_settings().then(msg => {
        alert(msg);
        appendLog(`[RESET] ${msg}`);
        initLauncher();
      });
    }
  }
}

function clearShaderCache() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.clear_shader_cache().then(msg => alert(msg));
  }
}

function createDesktopShortcut() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.create_desktop_shortcut().then(msg => alert(msg));
  }
}

function openExternal(url) {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.open_external(url);
  } else {
    window.open(url, '_blank');
  }
}

// ==========================================================================
// REMAPPING ENGINE (KEYBOARD & GAMEPAD)
// ==========================================================================
const ACTION_LABELS = {
  id: {
    cross: "✕ Lompat / Konfirmasi",
    circle: "○ Menghindar / Batal",
    square: "□ Serangan Ringan (Light)",
    triangle: "△ Serangan Berat (Heavy)",
    l1: "L1 Bertahan / Kunci Target",
    r1: "R1 Kuda-kuda Rider Power",
    l2: "L2 Pemilihan Ganti Form",
    r2: "R2 Jurus Pamungkas (Finisher)",
    l3: "L3 Lari Cepat (Sprint)",
    r3: "R3 Reset Sudut Kamera",
    options: "Options / Jeda Menu",
    touchpad: "Touchpad / Peta",
    left_stick_up: "Gerak Maju",
    left_stick_down: "Gerak Mundur",
    left_stick_left: "Gerak Kiri",
    left_stick_right: "Gerak Kanan"
  },
  en: {
    cross: "✕ Jump / Confirm",
    circle: "○ Dodge / Form Cancel",
    square: "□ Light Attack",
    triangle: "△ Heavy Attack",
    l1: "L1 Guard / Target Lock-On",
    r1: "R1 Rider Power Stance",
    l2: "L2 Form Change Selection",
    r2: "R2 Special Finish Skill",
    l3: "L3 Sprint / Left Stick Click",
    r3: "R3 Reset Camera / Right Stick Click",
    options: "Options / Pause Menu",
    touchpad: "Touchpad / Map",
    left_stick_up: "Move Forward",
    left_stick_down: "Move Backward",
    left_stick_left: "Move Left",
    left_stick_right: "Move Right"
  }
};

function getActionLabel(act) {
  const dict = ACTION_LABELS[currentLang] || ACTION_LABELS.en;
  return dict[act] || ACTION_LABELS.en[act] || act;
}

function loadKeybinds() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.get_keybinds().then(binds => {
      cachedKeybinds = binds;
      renderKeybindTables(binds);
    });
  }
}

function renderKeybindTables(binds) {
  const padTable = document.getElementById('padKeybindList');
  const kbmTable = document.getElementById('kbmKeybindList');
  if (!padTable || !kbmTable) return;

  padTable.innerHTML = '';
  kbmTable.innerHTML = '';

  const remapBtnText = currentLang === 'id' ? 'Ubah' : 'Change';

  const padActions = ['cross', 'circle', 'square', 'triangle', 'l1', 'r1', 'l2', 'r2', 'l3', 'r3', 'options', 'touchpad'];
  const kbmActions = ['left_stick_up', 'left_stick_down', 'left_stick_left', 'left_stick_right', 'square', 'triangle', 'cross', 'circle', 'r1', 'l1', 'r2', 'l2', 'options', 'touchpad'];

  padActions.forEach(act => {
    const tr = document.createElement('tr');
    const val = binds[`pad_${act}`] || 'auto';
    tr.innerHTML = `
      <td><strong>${getActionLabel(act)}</strong></td>
      <td><span class="key-badge">${val.toUpperCase()}</span></td>
      <td style="text-align: right;">
        <button class="btn-remap-sm" onclick="openPadPicker('${act}')">${remapBtnText}</button>
        <button class="btn-clear-sm" onclick="clearBinding('pad_${act}')">✕</button>
      </td>
    `;
    padTable.appendChild(tr);
  });

  kbmActions.forEach(act => {
    const tr = document.createElement('tr');
    const val = binds[act] || '';
    tr.innerHTML = `
      <td><strong>${getActionLabel(act)}</strong></td>
      <td><span class="key-badge">${val.toUpperCase()}</span></td>
      <td style="text-align: right;">
        <button class="btn-remap-sm" onclick="startKbmListen('${act}')">${remapBtnText}</button>
      </td>
    `;
    kbmTable.appendChild(tr);
  });

  if (binds.mouse_sensitivity) {
    const s = document.getElementById('sliderSensitivity');
    const l = document.getElementById('valSensitivity');
    if (s) s.value = binds.mouse_sensitivity;
    if (l) l.textContent = `${(binds.mouse_sensitivity / 25).toFixed(1)}x (${binds.mouse_sensitivity})`;
  }
  if (binds.deadzone) {
    const d = document.getElementById('sliderDeadzone');
    const dl = document.getElementById('valDeadzone');
    if (d) d.value = binds.deadzone;
    if (dl) dl.textContent = `${binds.deadzone}%`;
  }
}

function onSensitivityChange(val) {
  document.getElementById('valSensitivity').textContent = `${(val / 25).toFixed(1)}x (${val})`;
  cachedKeybinds.mouse_sensitivity = parseInt(val);
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.save_keybinds(cachedKeybinds);
  }
}

function onDeadzoneChange(val) {
  document.getElementById('valDeadzone').textContent = `${val}%`;
  cachedKeybinds.deadzone = parseInt(val);
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.save_keybinds(cachedKeybinds);
  }
}

function restorePadDefaults() {
  if (confirm("Restore default controller button mapping?")) {
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.reset_keybinds().then(binds => {
        cachedKeybinds = binds;
        renderKeybindTables(binds);
      });
    }
  }
}

function restoreKbmDefaults() {
  if (confirm("Restore default Keyboard & Mouse mapping?")) {
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.reset_keybinds().then(binds => {
        cachedKeybinds = binds;
        renderKeybindTables(binds);
      });
    }
  }
}

function clearBinding(key) {
  cachedKeybinds[key] = '';
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.save_keybinds(cachedKeybinds).then(() => renderKeybindTables(cachedKeybinds));
  }
}

// Modal Pad Picker
const PAD_BUTTON_OPTIONS = [
  { id: "a", name: "A (Cross / South)" },
  { id: "b", name: "B (Circle / East)" },
  { id: "x", name: "X (Square / West)" },
  { id: "y", name: "Y (Triangle / North)" },
  { id: "leftshoulder", name: "LB / L1" },
  { id: "rightshoulder", name: "RB / R1" },
  { id: "lefttrigger", name: "LT / L2 Trigger" },
  { id: "righttrigger", name: "RT / R2 Trigger" },
  { id: "leftstick", name: "L3 (Left Stick Click)" },
  { id: "rightstick", name: "R3 (Right Stick Click)" },
  { id: "start", name: "Start / Options" },
  { id: "back", name: "Back / Select / Touchpad" },
  { id: "dpup", name: "D-Pad Up" },
  { id: "dpdown", name: "D-Pad Down" },
  { id: "dpleft", name: "D-Pad Left" },
  { id: "dpright", name: "D-Pad Right" }
];

function openPadPicker(actionKey) {
  currentMappingAction = `pad_${actionKey}`;
  const modal = document.getElementById('modalPadPicker');
  const title = document.getElementById('modalActionTitle');
  if (title) title.textContent = `Map Action: ${getActionLabel(actionKey)}`;

  const grid = document.getElementById('padButtonsGrid');
  if (grid) {
    grid.innerHTML = '';
    PAD_BUTTON_OPTIONS.forEach(opt => {
      const b = document.createElement('div');
      b.className = 'btn-pad-option';
      b.textContent = opt.name;
      b.onclick = () => selectPadButton(opt.id);
      grid.appendChild(b);
    });
  }
  if (modal) modal.classList.add('open');
}

function closePadPicker() {
  const modal = document.getElementById('modalPadPicker');
  if (modal) modal.classList.remove('open');
  currentMappingAction = null;
}

function selectPadButton(btnId) {
  if (currentMappingAction) {
    cachedKeybinds[currentMappingAction] = btnId;
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.save_keybinds(cachedKeybinds).then(() => {
        renderKeybindTables(cachedKeybinds);
        closePadPicker();
      });
    }
  }
}

// KBM Key Listener
function startKbmListen(actionKey) {
  const btn = event ? event.target : document.activeElement;
  const original = btn ? btn.textContent : "Ubah";
  if (btn) {
    btn.textContent = currentLang === 'id' ? "Tekan Tombol / Klik..." : "Press Key / Click...";
    btn.style.background = "#FFB703";
    btn.style.color = "#000";
  }

  let finished = false;
  function cleanup() {
    if (finished) return;
    finished = true;
    window.removeEventListener('keydown', onKeyDown, true);
    window.removeEventListener('mousedown', onMouseDown, true);
  }

  function commitKey(keyName) {
    cleanup();
    cachedKeybinds[actionKey] = keyName;
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.save_keybinds(cachedKeybinds).then(() => renderKeybindTables(cachedKeybinds));
    } else {
      renderKeybindTables(cachedKeybinds);
    }
  }

  function onKeyDown(e) {
    e.preventDefault();
    e.stopPropagation();

    let keyName = e.key.toLowerCase();
    if (e.code === 'Space') keyName = 'space';
    else if (e.code === 'ShiftLeft') keyName = 'lshift';
    else if (e.code === 'ShiftRight') keyName = 'rshift';
    else if (e.code === 'ControlLeft') keyName = 'lctrl';
    else if (e.code === 'ControlRight') keyName = 'rctrl';
    else if (e.code === 'AltLeft') keyName = 'lalt';
    else if (e.code === 'AltRight') keyName = 'ralt';
    else if (e.code === 'Escape') keyName = 'escape';
    else if (e.code === 'Tab') keyName = 'tab';
    else if (e.code === 'Backspace') keyName = 'backspace';
    else if (e.code === 'Enter') keyName = 'return';
    else if (e.code && e.code.startsWith('Key')) keyName = e.code.substring(3).toLowerCase();
    else if (e.code && e.code.startsWith('Digit')) keyName = e.code.substring(5);

    commitKey(keyName);
  }

  function onMouseDown(e) {
    // Only capture if clicking inside document, and after initial click
    e.preventDefault();
    e.stopPropagation();
    let btnName = 'leftbutton';
    if (e.button === 0) btnName = 'leftbutton';
    else if (e.button === 1) btnName = 'middlebutton';
    else if (e.button === 2) btnName = 'rightbutton';
    commitKey(btnName);
  }

  setTimeout(() => {
    window.addEventListener('keydown', onKeyDown, { once: true, capture: true });
    window.addEventListener('mousedown', onMouseDown, { once: true, capture: true });
  }, 100);
}

// ==========================================================================
// PKG INSTALLATION
// ==========================================================================
function renderPkgList(pkgs) {
  const container = document.getElementById('pkgListContainer');
  if (!container) return;
  container.innerHTML = '';

  if (pkgs.length === 0) {
    container.innerHTML = `<div style="font-size: 11px; color: var(--text-muted); padding: 8px 0;">Tidak ada file .pkg di folder root. Gunakan tombol 'Pilih File PKG Manual' di bawah.</div>`;
    return;
  }

  pkgs.forEach(pkg => {
    const item = document.createElement('div');
    item.className = 'pkg-item';
    item.style.cssText = "display: flex; align-items: center; justify-content: space-between; background: rgba(0,0,0,0.2); padding: 10px 14px; border-radius: 8px; margin-bottom: 8px; border: 1px solid var(--border-subtle);";
    item.innerHTML = `
      <div style="font-size: 13px; font-weight: 600;">📦 ${pkg.name} (${pkg.size_mb} MB)</div>
      <button class="btn-secondary" style="padding: 6px 14px; font-size: 11px;" onclick="installTargetPkg('${pkg.path.replace(/\\/g, '\\\\')}')">INSTALL</button>
    `;
    container.appendChild(item);
  });
}

function browseManualPkg() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.browse_manual_pkg().then(path => {
      if (path) installTargetPkg(path);
    });
  }
}

function installTargetPkg(pkgPath) {
  if (confirm(`Install package update: ${pkgPath}?`)) {
    appendLog(`[PKG] Starting installation of: ${pkgPath}`);
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.install_pkg(pkgPath);
    }
  }
}
