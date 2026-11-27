/* ==========================================================================
   KAMEN RIDER: MEMORY OF HEROES - PC NATIVE EDITION LAUNCHER JAVASCRIPT
   Two-Way IPC Bridge via window.pywebview.api
   Features: Bilingual (ID/EN), Saves Manager, Trophy Tracker, Auto-Update
   Port Lead: AO Zero | Partner: Bakka Sub (www.bakkasub.my.id)
   ========================================================================== */

// Localization dictionary (window.I18N, window.ACTION_LABELS, window.SUPPORTED_LANGS) is loaded from ui/i18n.js
const I18N = window.I18N || {};

let currentLang = 'id';
let currentTheme = 'dark';
let indoPatchEnabled = false;
let indoPatchBusy = false;
let cachedKeybinds = {};
let cachedTrophies = [];
let cachedHardware = null;
let cachedPkgs = [];
let activeTrophyFilter = 'all';
let currentMappingAction = null;
let initStarted = false;
let initDone = false;

// ==========================================================================
// THEME SWITCHER (CLEAN DESKTOP DARK / LIGHT)
// ==========================================================================
function applyTheme(theme, persist) {
  currentTheme = (theme === 'light') ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', currentTheme);
  const lbl = document.getElementById('themeLabel');
  if (lbl) lbl.textContent = currentTheme === 'dark' ? 'Dark' : 'Light';
  if (persist) onSettingChanged();
}

function toggleTheme() {
  applyTheme(currentTheme === 'dark' ? 'light' : 'dark', true);
}

function switchTab(tabKey) {
  document.querySelectorAll('.nav-tab').forEach(b => {
    b.classList.toggle('active', b.getAttribute('data-tab') === tabKey);
  });
  document.querySelectorAll('.tab-pane').forEach(p => {
    p.classList.toggle('active', p.id === `tab-${tabKey}`);
  });
}

function switchControlsSub(sub) {
  const isPad = (sub === 'gamepad');
  const bPad = document.getElementById('subTabBtnPad');
  const bKbm = document.getElementById('subTabBtnKbm');
  const vPad = document.getElementById('sub-gamepad');
  const vKbm = document.getElementById('sub-keyboard');
  if (bPad) bPad.classList.toggle('active', isPad);
  if (bKbm) bKbm.classList.toggle('active', !isPad);
  if (vPad) vPad.classList.toggle('active', isPad);
  if (vKbm) vKbm.classList.toggle('active', !isPad);
}

function syncOverviewSummary() {
  const res = (document.getElementById('selectRes')?.value || '1080p').split(' ')[0];
  const fpsFull = document.getElementById('selectFps')?.value || '60 FPS (Native Unlock)';
  const fpsShort = fpsFull.split(' ')[0] + ' FPS';
  const up = document.getElementById('selectUpscaler')?.value || 'Off (Native)';
  const upShort = up.startsWith('Off') ? 'Native' : up.split('(')[0].trim();

  const kvRender = document.getElementById('kvRenderSummary');
  if (kvRender) kvRender.textContent = `${res} · ${fpsShort} · ${upShort}`;
  const footFps = document.getElementById('footFpsLabel');
  if (footFps) footFps.textContent = fpsShort;

  // Sync Quick Overrides segmented pills
  document.querySelectorAll('#segGroupFps .seg-opt').forEach(b => {
    b.classList.toggle('active', b.getAttribute('data-val') === fpsFull);
  });
  const isFs = document.getElementById('chkFullscreen')?.checked;
  const isBl = document.getElementById('chkBorderless')?.checked;
  const dispMode = isFs ? 'fullscreen' : (isBl ? 'borderless' : 'windowed');
  document.querySelectorAll('#segGroupDisplay .seg-opt').forEach(b => {
    b.classList.toggle('active', b.getAttribute('data-val') === dispMode);
  });
  const showFps = document.getElementById('chkShowFps')?.checked;
  const showHud = document.getElementById('chkShowPerfHud')?.checked;
  const ovMode = showHud ? 'detailed' : (showFps ? 'fps' : 'off');
  document.querySelectorAll('#segGroupHud .seg-opt').forEach(b => {
    b.classList.toggle('active', b.getAttribute('data-val') === ovMode);
  });
}

function setQuickFps(val) {
  const sel = document.getElementById('selectFps');
  if (sel) sel.value = val;
  syncOverviewSummary();
  onSettingChanged();
}

function setQuickDisplay(mode) {
  const fs = document.getElementById('chkFullscreen');
  const bl = document.getElementById('chkBorderless');
  if (fs) fs.checked = (mode === 'fullscreen');
  if (bl) bl.checked = (mode === 'borderless');
  syncOverviewSummary();
  onSettingChanged();
}

function onDisplayCheckboxChanged(which) {
  const fs = document.getElementById('chkFullscreen');
  const bl = document.getElementById('chkBorderless');
  if (which === 'fullscreen' && fs && fs.checked && bl) {
    bl.checked = false;
  } else if (which === 'borderless' && bl && bl.checked && fs) {
    fs.checked = false;
  }
  syncOverviewSummary();
  onSettingChanged();
}

function setQuickFpsOverlay(mode) {
  const chkFps = document.getElementById('chkShowFps');
  const chkHud = document.getElementById('chkShowPerfHud');
  if (chkFps) chkFps.checked = (mode !== 'off');
  if (chkHud) chkHud.checked = (mode === 'detailed');
  syncOverviewSummary();
  onSettingChanged();
}

function onFpsCheckboxChanged(which) {
  const chkFps = document.getElementById('chkShowFps');
  const chkHud = document.getElementById('chkShowPerfHud');
  if (which === 'detailed' && chkHud && chkHud.checked && chkFps) {
    chkFps.checked = true;
  } else if (which === 'fps' && chkFps && !chkFps.checked && chkHud) {
    chkHud.checked = false;
  }
  syncOverviewSummary();
  onSettingChanged();
}

function triggerIndoPatch(wantEnabled) {
  const sel = document.getElementById('selectIndoPatch');
  if (sel) sel.value = wantEnabled ? 'on' : 'off';
  applyIndoPatchNow();
}

function quickToggleIndoPatch() {
  triggerIndoPatch(!indoPatchEnabled);
}

// ==========================================================================
// BUILT-IN INDONESIAN SUBTITLE PATCH (BAKKA SUB X AO ZERO)
// ==========================================================================
function updateIndoPatchUI(status) {
  const pill = document.getElementById('patchStatusPill');
  const sel = document.getElementById('selectIndoPatch');
  const subTag = document.getElementById('lblSubStatus');
  const meta = document.getElementById('indoPatchMeta');
  const btn = document.getElementById('btnApplyIndoPatch');
  const heroTxt = document.getElementById('txtHeroIndo');
  const navBadge = document.getElementById('navIndoBadge');
  const segOrig = document.getElementById('segSubOrig');
  const segIndo = document.getElementById('segSubIndo');

  if (!status) return;
  indoPatchEnabled = !!status.applied;

  if (sel) sel.value = indoPatchEnabled ? 'on' : 'off';
  if (segOrig) segOrig.classList.toggle('active', !indoPatchEnabled);
  if (segIndo) segIndo.classList.toggle('active', indoPatchEnabled);
  if (heroTxt) heroTxt.textContent = indoPatchEnabled ? 'Patch Indo: Active' : 'Patch Indo: Off';
  if (navBadge) {
    navBadge.textContent = indoPatchEnabled ? 'ID' : 'EN';
    navBadge.className = indoPatchEnabled ? 'nav-badge' : 'nav-badge muted';
  }

  if (pill) {
    pill.classList.remove('neutral', 'working', 'error');
    if (!status.game_found) {
      pill.classList.add('error');
      pill.textContent = currentLang === 'id' ? 'Game tidak ditemukan' : 'Game not found';
    } else if (indoPatchEnabled) {
      pill.innerHTML = `<span class="dot-green"></span> Active · v${status.version || '1.0.0'}`;
    } else {
      pill.classList.add('neutral');
      pill.textContent = 'Original (EN/JP)';
    }
  }

  if (subTag) {
    subTag.className = indoPatchEnabled ? 'spec-value green' : 'spec-value';
    subTag.textContent = indoPatchEnabled ? 'Bahasa Indonesia (Bakka Sub)' : 'Original (EN/JP)';
  }

  if (meta) {
    const cnt = status.translated_count || 0;
    const bak = status.backup_exists
      ? (currentLang === 'id' ? 'Backup vanilla aman' : 'Vanilla backup safe')
      : (currentLang === 'id' ? 'Auto-backup saat pertama aktif' : 'Auto-backup on first apply');
    meta.textContent = `patches/id_patch.json · v${status.version || '1.0.0'} · ${cnt} strings · ${bak}`;
  }

  if (btn) btn.disabled = indoPatchBusy || !status.game_found;
}

function onIndoPatchSelect(val) {
  // Auto-apply when user changes dropdown
  applyIndoPatchNow();
}

function applyIndoPatchNow() {
  if (indoPatchBusy || !window.pywebview || !window.pywebview.api) return;
  const sel = document.getElementById('selectIndoPatch');
  const wantEnabled = sel ? (sel.value === 'on') : false;

  indoPatchBusy = true;
  const pill = document.getElementById('patchStatusPill');
  const btn = document.getElementById('btnApplyIndoPatch');
  if (pill) {
    pill.className = 'patch-status-pill working';
    pill.textContent = wantEnabled
      ? (currentLang === 'id' ? 'MEMASANG PATCH...' : 'APPLYING PATCH...')
      : (currentLang === 'id' ? 'MENGEMBALIKAN ORIGINAL...' : 'RESTORING ORIGINAL...');
  }
  if (btn) btn.disabled = true;

  window.pywebview.api.set_indo_patch(wantEnabled).catch(err => {
    indoPatchBusy = false;
    alert('Patch Error: ' + err);
    if (btn) btn.disabled = false;
  });
}

window.onIndoPatchDone = function(res) {
  indoPatchBusy = false;
  if (res && res.status) {
    updateIndoPatchUI(res.status);
  }
  if (res && res.message) {
    appendLog(`[PATCH-ID] ${res.message}`);
    showToast(res.message, res.success ? 'ok' : 'error');
  }
};

// ==========================================================================
// LANGUAGE SWITCHER (5 LANGUAGES: ID / EN / ES / PT-BR / PT-PT)
// ==========================================================================
function applyLanguage(lang, persist) {
  const supported = window.SUPPORTED_LANGS || ['id', 'en', 'es', 'pt-BR', 'pt-PT'];
  currentLang = supported.includes(lang) ? lang : 'en';
  const dict = I18N[currentLang] || I18N.en || {};

  // Update elements with data-i18n
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (dict[key]) {
      el.textContent = dict[key];
    }
  });

  const label = document.getElementById('langLabel');
  if (label) {
    label.textContent = (window.LANG_SHORT && window.LANG_SHORT[currentLang]) || currentLang.toUpperCase();
  }

  const select = document.getElementById('selectLang');
  if (select) select.value = currentLang;

  // Re-render dynamic tables/lists so button labels & notices update immediately
  if (cachedKeybinds && Object.keys(cachedKeybinds).length > 0) {
    renderKeybindTables(cachedKeybinds);
  }
  renderTrophies(cachedTrophies, activeTrophyFilter);
  renderPkgList(cachedPkgs);

  if (persist) {
    onSettingChanged();
  }
}

function setLanguage(lang) {
  applyLanguage(lang, true);
}

function toggleLanguage() {
  const supported = window.SUPPORTED_LANGS || ['id', 'en', 'es', 'pt-BR', 'pt-PT'];
  const idx = supported.indexOf(currentLang);
  const next = supported[(idx + 1) % supported.length];
  setLanguage(next);
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
  const badgeText = document.getElementById('badgeGamepadText');
  if (badgeText) badgeText.textContent = name;

  const cbox = document.getElementById('controllerStatusBox');
  if (cbox) {
    cbox.textContent = name.toLowerCase().includes('keyboard') 
      ? `ACTIVE: ${name} (Connect Xbox or PlayStation controller anytime)`
      : `CONNECTED: ${name}`;
    cbox.style.color = name.toLowerCase().includes('keyboard') ? 'var(--text-muted)' : 'var(--ready)';
  }
};

window.onGameExited = function(newStats, cacheMb) {
  const btn = document.getElementById('btnLaunch');
  if (btn) {
    btn.disabled = false;
    const lbl = btn.querySelector('#txtLaunchBtn');
    if (lbl) lbl.textContent = I18N[currentLang].btn_play;
  }
  const badge = document.getElementById('gameReadyText');
  if (badge) badge.textContent = 'Shaders ready';
  const dot = document.getElementById('statusDot');
  if (dot) dot.style.background = 'var(--green-dot)';
  if (newStats) renderSessionStats(newStats);
  if (typeof cacheMb === 'number') renderShaderCache(cacheMb);
  refreshSavesList();
};

let appToastTimer = null;
function showToast(msg, type = 'ok') {
  const el = document.getElementById('appToast');
  if (!el) return;
  el.textContent = msg;
  el.className = `app-toast show ${type}`;
  if (appToastTimer) clearTimeout(appToastTimer);
  appToastTimer = setTimeout(() => {
    el.classList.remove('show');
  }, 3600);
}

function renderSessionStats(stats) {
  if (!stats) return;
  const heroMeta = document.getElementById('heroPlaytimeMeta');
  if (heroMeta) {
    heroMeta.textContent = stats.sessions > 0
      ? `${stats.playtime_text} · last played ${stats.last_played_text}`
      : stats.playtime_text;
  }
  const lastRun = document.getElementById('kvLastRunResult');
  if (lastRun) lastRun.textContent = stats.last_result || 'Ready to launch';
}

function renderHardwareSummary(hw) {
  if (!hw) return;
  cachedHardware = hw;

  const el = document.getElementById('lblDetectedGpu');
  if (el) {
    const ram = hw.ram_gb ? ` · ${hw.ram_gb} GB RAM` : '';
    el.textContent = `${hw.gpu || 'Vulkan 1.3 GPU'}${ram}`;
  }

  const vramStr = hw.vram_gb ? ` (${hw.vram_gb} GB VRAM)` : '';
  const setTxt = (id, val) => {
    const node = document.getElementById(id);
    if (node) node.textContent = val || '—';
  };
  setTxt('specCpu', hw.cpu || 'Unknown CPU');
  setTxt('specGpu', `${hw.gpu || 'Vulkan 1.3 GPU'}${vramStr}`);
  setTxt('specRam', hw.ram_gb ? `${hw.ram_gb} GB` : 'Unknown');
  setTxt('specOs', hw.os || 'Windows');
  setTxt('specDisk', hw.disk_free || 'Unknown');
  setTxt('specRecommended', hw.recommended || 'Balanced (1080p FSR 3.1)');
}

function copySystemSpecs() {
  const hw = cachedHardware || {};
  const vramStr = hw.vram_gb ? ` (${hw.vram_gb} GB VRAM)` : '';
  const text = [
    '=== Kamen Rider: Memory of Heroes PC Native v1.3.2 — System Specs ===',
    `CPU: ${hw.cpu || 'Unknown'}`,
    `GPU: ${hw.gpu || 'Unknown'}${vramStr}`,
    `RAM: ${hw.ram_gb ? hw.ram_gb + ' GB' : 'Unknown'}`,
    `OS:  ${hw.os || 'Windows'}`,
    `Disk: ${hw.disk_free || 'Unknown'}`,
    `Recommended Preset: ${hw.recommended || 'Balanced'}`
  ].join('\n');

  const okMsg = (I18N[currentLang] && I18N[currentLang].msg_specs_copied) || 'System specs copied to clipboard!';
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => showToast(okMsg, 'ok')).catch(() => showToast(okMsg, 'ok'));
  } else {
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); } catch (e) {}
    document.body.removeChild(ta);
    showToast(okMsg, 'ok');
  }
}

function applyRecommendedPreset() {
  const preset = (cachedHardware && cachedHardware.recommended_preset) || 'balanced';
  applyPreset(preset);
  const okMsg = (I18N[currentLang] && I18N[currentLang].msg_preset_applied) || 'Recommended preset applied!';
  showToast(okMsg, 'ok');
}

function exportDiagnosticBundle() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.export_diagnostic_bundle().then(res => {
      if (res && res.message && res.message !== 'Cancelled.') {
        showToast(res.message, res.success ? 'ok' : 'error');
        appendLog(`[DIAGNOSTIC] ${res.message}`);
      }
    }).catch(err => {
      showToast('Diagnostic Export Error: ' + err, 'error');
    });
  }
}

function renderShaderCache(mb) {
  const el = document.getElementById('kvShaderSize');
  if (!el) return;
  const val = (typeof mb === 'number' && !isNaN(mb)) ? mb.toFixed(1) : '0.0';
  el.textContent = `Ready · ${val} MB cached`;
}

// ==========================================================================
// INITIALIZATION
// ==========================================================================
function initLauncher(forceReload = false) {
  if (initStarted && !forceReload) return;
  if (window.pywebview && window.pywebview.api) {
    initStarted = true;
    initDone = false;
    window.pywebview.api.get_initial_data().then(data => {
      // 1. Language, Theme & Patch Status
      if (data.language) {
        applyLanguage(data.language, false);
      }
      applyTheme(data.theme || 'dark', false);
      if (data.indo_patch_status) {
        updateIndoPatchUI(data.indo_patch_status);
      }
      if (data.session_stats) renderSessionStats(data.session_stats);
      if (data.hardware) renderHardwareSummary(data.hardware);
      if (typeof data.shader_cache_mb === 'number') renderShaderCache(data.shader_cache_mb);

      // 2. Paths & Player Name
      document.getElementById('inputGameDir').value = data.game_dir || '';
      const dirDisp = document.getElementById('lblGameDirDisplay');
      if (dirDisp && data.game_dir) {
        dirDisp.textContent = data.game_dir;
        dirDisp.title = data.game_dir;
      }
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
      
      const dm = data.display_mode || ((data.fullscreen === 'true' || data.fullscreen === true) ? 'fullscreen' : ((data.borderless === 'true' || data.borderless === true || data.borderless === undefined) ? 'borderless' : 'windowed'));
      document.getElementById('chkFullscreen').checked = (dm === 'fullscreen');
      document.getElementById('chkBorderless').checked = (dm === 'borderless');
      const om = data.fps_overlay_mode || ((data.show_perf_hud === 'true' || data.show_perf_hud === true) ? 'detailed' : ((data.show_fps === 'true' || data.show_fps === true) ? 'fps' : 'off'));
      document.getElementById('chkShowFps').checked = (om !== 'off');
      document.getElementById('chkShowPerfHud').checked = (om === 'detailed');
      document.getElementById('chkCompileShaders').checked = (data.compile_shaders_bg === 'true' || data.compile_shaders_bg === true || data.compile_shaders_bg === undefined);
      document.getElementById('chkHideLauncher').checked = (data.hide_launcher_on_play === 'true' || data.hide_launcher_on_play === true);
      const chkAB = document.getElementById('chkAutoBackup');
      if (chkAB) chkAB.checked = (data.auto_backup_saves === 'true' || data.auto_backup_saves === true || data.auto_backup_saves === undefined);
      document.getElementById('chkUpdateStartup').checked = (data.check_updates_startup === 'true' || data.check_updates_startup === true || data.check_updates_startup === undefined);
      const chkRpc = document.getElementById('chkDiscordRpc');
      if (chkRpc) chkRpc.checked = (data.discord_rpc === 'true' || data.discord_rpc === true || data.discord_rpc === undefined);
      
      const vol = data.audio_volume || '100';
      document.getElementById('rngVolume').value = vol;
      document.getElementById('lblVolumeVal').textContent = `${vol}%`;

      // 4. Badges & Gamepad
      if (data.app_ver) {
        const bv = document.getElementById('badgeVer');
        if (bv) bv.textContent = `v${data.app_ver}`;
        const kv = document.getElementById('kvVersion');
        if (kv) kv.textContent = `${data.app_ver} (CUSA17374)`;
      }
      syncOverviewSummary();
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

      // Only after real values are loaded do we allow saves to write through
      initDone = true;

      // Honor the "check updates on startup" toggle automatically
      const shouldCheckStartup = document.getElementById('chkUpdateStartup');
      if (shouldCheckStartup && shouldCheckStartup.checked) {
        checkForUpdates(true);
      }
    }).catch(err => {
      console.error("Failed to load initial data:", err);
      initDone = true;
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
  if (!initDone) return; // do not persist default/pre-init control values
  const isFs = document.getElementById('chkFullscreen').checked;
  const isBl = document.getElementById('chkBorderless').checked;
  const dispMode = isFs ? 'fullscreen' : (isBl ? 'borderless' : 'windowed');
  const showFps = document.getElementById('chkShowFps').checked;
  const showHud = document.getElementById('chkShowPerfHud').checked;
  const ovMode = showHud ? 'detailed' : (showFps ? 'fps' : 'off');
  const settings = {
    game_dir: document.getElementById('inputGameDir').value,
    resolution: document.getElementById('selectRes').value,
    fps: document.getElementById('selectFps').value,
    upscaler: document.getElementById('selectUpscaler').value,
    upscaler_quality: document.getElementById('selectUpscalerQuality').value,
    aspect_ratio: document.getElementById('selectAspect').value,
    vsync_mode: document.getElementById('selectVsync').value,
    fullscreen: isFs,
    borderless: isBl,
    display_mode: dispMode,
    show_fps: showFps,
    show_perf_hud: showHud,
    fps_overlay_mode: ovMode,
    compile_shaders_bg: document.getElementById('chkCompileShaders').checked,
    hide_launcher_on_play: document.getElementById('chkHideLauncher').checked,
    auto_backup_saves: document.getElementById('chkAutoBackup') ? document.getElementById('chkAutoBackup').checked : true,
    check_updates_startup: document.getElementById('chkUpdateStartup').checked,
    discord_rpc: document.getElementById('chkDiscordRpc') ? document.getElementById('chkDiscordRpc').checked : true,
    audio_volume: document.getElementById('rngVolume').value,
    language: currentLang,
    theme: currentTheme,
    indo_patch: indoPatchEnabled
  };
  window.pywebview.api.save_settings(settings);
  syncOverviewSummary();
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
        const dirDisp = document.getElementById('lblGameDirDisplay');
        if (dirDisp) {
          dirDisp.textContent = res.path;
          dirDisp.title = res.path;
        }
        if (res.app_ver) {
          const bv = document.getElementById('badgeVer');
          if (bv) bv.textContent = `v${res.app_ver}`;
          const kv = document.getElementById('kvVersion');
          if (kv) kv.textContent = `${res.app_ver} (CUSA17374)`;
        }
        if (res.indo_patch_status) {
          updateIndoPatchUI(res.indo_patch_status);
        }
        appendLog(`[DIRECTORY] Game folder set to: ${res.path}`);
        showToast('Game folder updated!', 'ok');
      }
    });
  }
}

function launchGame() {
  const btn = document.getElementById('btnLaunch');
  btn.disabled = true;
  const lbl = btn.querySelector('#txtLaunchBtn');
  if (lbl) lbl.textContent = 'Running...';

  const badge = document.getElementById('gameReadyText');
  if (badge) badge.textContent = 'Game running';
  const dot = document.getElementById('statusDot');
  if (dot) dot.style.background = 'var(--amber-text)';

  onSettingChanged();

  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.launch_game().then(res => {
      if (res === "NO_GAME") {
        window.onGameExited();
      }
    }).catch(err => {
      showToast("Launch Error: " + err, 'error');
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
      <div class="save-icon">
        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
      </div>
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
    opt.textContent = `[BACKUP] ${b.name} (${b.size_kb} KB - ${b.date})`;
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
      showToast(res.message, res.success ? 'ok' : 'error');
      appendLog(`[BACKUP] ${res.message}`);
      refreshSavesList();
    });
  }
}

function importSaveZip() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.import_save_zip().then(res => {
      if (res && res.message && res.message !== 'Cancelled.') {
        showToast(res.message, res.success ? 'ok' : 'error');
        appendLog(`[SAVE IMPORT] ${res.message}`);
        if (res.success) refreshSavesList();
      }
    });
  }
}

function openScreenshotsFolder() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.open_screenshots_folder().then(msg => showToast(msg, 'ok'));
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
        <button class="btn-trophy-test" onclick="previewTrophyPopup(${t.id})" title="Test Achievement Notification Popup">${(I18N[currentLang] && I18N[currentLang].btn_test_sm) || 'Test'}</button>
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
  const badgeEl = toast.querySelector('.ps4-toast-badge span');
  if (badgeEl) badgeEl.textContent = 'ACHIEVEMENT UNLOCKED';

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

function filterTrophies(type, btn) {
  activeTrophyFilter = type;
  document.querySelectorAll('.btn-filter').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  renderTrophies(cachedTrophies, type);
}

// ==========================================================================
// AUTO UPDATER & LOGS (True 1-Click Download & Self-Replace)
// ==========================================================================
let latestUpdateMeta = null;
let autoUpdateRunning = false;

function checkForUpdates(silent) {
  const status = document.getElementById('updateStatusText');
  if (status) status.textContent = "Checking GitHub Releases...";
  
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.check_updates().then(res => {
      latestUpdateMeta = res;
      if (res.up_to_date) {
        if (status) status.textContent = `● Up to date (${res.current})`;
        if (!silent) showToast(`You are up to date (${res.current})`, 'ok');
      } else {
        const sz = res.asset_size_mb ? ` (${res.asset_size_mb} MB)` : '';
        if (status) status.textContent = `● Update available: ${res.latest}${sz}`;
        const banner = document.getElementById('updateBanner');
        const bTitle = document.getElementById('updateBannerTitle');
        const bSub = document.getElementById('updateBannerSub');
        const bBtn = document.getElementById('btnStartAutoUpdate');
        if (bTitle) bTitle.textContent = `Update available: ${res.latest}${sz}`;
        if (bSub) bSub.textContent = `Installed: ${res.current} → Latest: ${res.latest}. Your CUSA17374 dump, saves, and settings stay untouched.`;
        if (bBtn) bBtn.style.display = res.download_url ? 'inline-flex' : 'none';
        if (banner) banner.classList.add('show');
        if (!silent) showToast(`Update available: ${res.latest}! Check Overview banner to install.`, 'ok');
      }
    }).catch(() => {
      if (status) status.textContent = '● Could not reach update server.';
    });
  }
}

function openUpdateReleasePage() {
  const url = (latestUpdateMeta && latestUpdateMeta.url) || 'https://github.com/ao-zero/Kamen-Rider-Memory-of-Heroes-PC/releases';
  openExternal(url);
}

function startAutoUpdate() {
  if (autoUpdateRunning || !latestUpdateMeta || !latestUpdateMeta.download_url) return;
  if (!confirm(`Download and install ${latestUpdateMeta.latest} now?\n\nThe launcher will restart automatically. Your CUSA17374 game dump, saves, and launcher.ini will NOT be modified.`)) {
    return;
  }
  autoUpdateRunning = true;
  const btn = document.getElementById('btnStartAutoUpdate');
  const pWrap = document.getElementById('updateProgressWrap');
  if (btn) { btn.disabled = true; btn.textContent = 'Updating...'; }
  if (pWrap) pWrap.classList.add('show');
  window.pywebview.api.start_auto_update(latestUpdateMeta.download_url);
}

window.onUpdateProgress = function(pct, text) {
  const bar = document.getElementById('updateProgressBar');
  const lbl = document.getElementById('updateProgressText');
  if (bar) bar.style.width = `${Math.max(0, Math.min(100, pct))}%`;
  if (lbl) lbl.textContent = `${pct}% · ${text}`;
};

window.onUpdateDone = function(res) {
  autoUpdateRunning = false;
  if (res && res.success) {
    showToast(res.message || 'Update ready! Restarting...', 'ok');
  } else {
    showToast((res && res.message) || 'Auto-update failed.', 'error');
    const btn = document.getElementById('btnStartAutoUpdate');
    if (btn) { btn.disabled = false; btn.textContent = 'Retry Update'; }
  }
};

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
      showToast(res.message, res.success ? 'ok' : 'error');
      if (res.success) {
        initLauncher(true);
      }
    });
  }
}

function resetAllSettings() {
  if (confirm("Reset ALL launcher graphics profiles, settings, and keybinds to factory default?")) {
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.reset_all_settings().then(msg => {
        showToast(msg, 'ok');
        appendLog(`[RESET] ${msg}`);
        initLauncher(true);
      });
    }
  }
}

function clearShaderCache() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.clear_shader_cache().then(msg => {
      showToast(msg, 'ok');
      renderShaderCache(0);
      appendLog(`[CACHE] ${msg}`);
    });
  }
}

function createDesktopShortcut() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.create_desktop_shortcut().then(msg => showToast(msg, 'ok'));
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
function getActionLabel(act) {
  const labels = window.ACTION_LABELS || {};
  const dict = labels[currentLang] || labels.en || {};
  return dict[act] || (labels.en && labels.en[act]) || act;
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

  const remapBtnText = (I18N[currentLang] && I18N[currentLang].btn_remap) || 'Change';

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
        <button class="btn-remap-sm" onclick="startKbmListen('${act}', this)">${remapBtnText}</button>
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

// Close the pad picker with Escape or by clicking the backdrop (R-32 / R-26)
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closePadPicker();
});
document.getElementById('modalPadPicker').addEventListener('click', (e) => {
  if (e.target === e.currentTarget) closePadPicker();
});

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
function startKbmListen(actionKey, btn) {
  btn = btn || (typeof event !== 'undefined' && event ? event.target : null) || document.activeElement;
  if (btn) {
    btn.textContent = (I18N[currentLang] && I18N[currentLang].lbl_press_key) || "Press Key / Click...";
    btn.style.background = "var(--accent)";
    btn.style.color = "#0D1510";
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
  cachedPkgs = pkgs || [];
  const container = document.getElementById('pkgListContainer');
  if (!container) return;
  container.innerHTML = '';

  if (cachedPkgs.length === 0) {
    const emptyMsg = (I18N[currentLang] && I18N[currentLang].msg_no_pkg_found) || "No .pkg files found in root folder. Click 'Browse .PKG...' on the right to install manually.";
    container.innerHTML = `<div style="font-size: 11px; color: var(--text-muted); padding: 8px 0;">${emptyMsg}</div>`;
    return;
  }

  cachedPkgs.forEach(pkg => {
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
