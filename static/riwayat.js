/**
 * Riwayat Proyek & Live Auto-Reload untuk FigCraft Web
 * Terhubung langsung ke katalog pratinjau/proyek.json di server.
 */

(function () {
  'use strict';

  // 1. Inject DOM Topbar, Drawer, dan Toast
  function injectUI() {
    if (document.getElementById('fc_topbar')) return;

    // Topbar
    const topbar = document.createElement('div');
    topbar.id = 'fc_topbar';
    topbar.innerHTML = `
      <button id="fc_btn_simpan" class="fc-btn fc-btn-primary" title="Simpan desain aktif ini langsung ke server & katalog Riwayat Proyek (Ctrl+S)">
        <span>💾</span> <span>Simpan ke Server</span>
      </button>
      <button id="fc_btn_riwayat" class="fc-btn" title="Buka riwayat seluruh proyek desain yang pernah dibuat">
        <span>📂</span> <span>Riwayat Proyek</span> <span id="fc_badge_total" class="fc-badge">-</span>
      </button>
      <div id="fc_live_pill" class="fc-live-pill" style="display: none;" title="Auto-Sync aktif: kanvas otomatis diperbarui jika AI melakukan revisi">
        <span class="fc-live-dot" id="fc_live_dot"></span>
        <span id="fc_live_text">Live Sync</span>
      </div>
    `;
    document.body.appendChild(topbar);

    // Drawer & Backdrop
    const backdrop = document.createElement('div');
    backdrop.id = 'fc_drawer_backdrop';
    document.body.appendChild(backdrop);

    const drawer = document.createElement('div');
    drawer.id = 'fc_drawer';
    drawer.innerHTML = `
      <div class="fc-drawer-header">
        <div class="fc-drawer-title">
          <span>📂</span>
          <div>
            <div>Riwayat Proyek Desain</div>
            <div style="font-size: 11px; font-weight: normal; color: var(--fc-text-muted);" id="fc_drawer_sub">Memuat proyek...</div>
          </div>
        </div>
        <button id="fc_drawer_close" class="fc-drawer-close" title="Tutup (Esc)">✕</button>
      </div>
      <div class="fc-drawer-search-box">
        <div class="fc-search-wrapper">
          <span class="fc-search-icon">🔍</span>
          <input type="text" id="fc_search_input" class="fc-search-input" placeholder="Cari nama proyek, mobile, dashboard..." autocomplete="off">
        </div>
      </div>
      <div class="fc-drawer-body" id="fc_project_list">
        <div style="text-align: center; padding: 40px; color: var(--fc-text-muted);">Memuat riwayat...</div>
      </div>
    `;
    document.body.appendChild(drawer);

    // Toast
    const toast = document.createElement('div');
    toast.id = 'fc_toast';
    toast.innerHTML = `<span id="fc_toast_icon">⚡</span> <span id="fc_toast_msg"></span>`;
    document.body.appendChild(toast);

    // Event Listeners
    const btnSimpan = document.getElementById('fc_btn_simpan');
    if (btnSimpan) btnSimpan.addEventListener('click', simpanKeServer);
    document.getElementById('fc_btn_riwayat').addEventListener('click', toggleDrawer);
    document.getElementById('fc_drawer_close').addEventListener('click', closeDrawer);
    backdrop.addEventListener('click', closeDrawer);
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && drawer.classList.contains('open')) closeDrawer();
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        simpanKeServer();
      }
    });

    document.getElementById('fc_search_input').addEventListener('input', (e) => {
      renderProjectList(e.target.value.trim().toLowerCase());
    });
  }

  let projectsData = [];

  function showToast(msg, icon = '⚡', duration = 3000) {
    const toast = document.getElementById('fc_toast');
    if (!toast) return;
    document.getElementById('fc_toast_icon').textContent = icon;
    document.getElementById('fc_toast_msg').textContent = msg;
    toast.classList.add('show');
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => toast.classList.remove('show'), duration);
  }

  async function simpanKeServer() {
    if (!window.figcraft) {
      showToast('FigCraft belum siap!', '⚠️', 3000);
      return;
    }
    const btn = document.getElementById('fc_btn_simpan');
    const oldHtml = btn ? btn.innerHTML : '';
    if (btn) {
      btn.innerHTML = '<span>⏳</span> <span>Menyimpan...</span>';
      btn.disabled = true;
    }

    try {
      showToast('Mengambil data kanvas…', '🔄', 3000);
      const res = await window.figcraft.execute('file.saveAs', { data: true });
      if (!res || !res.data) throw new Error('Kanvas kosong atau gagal mengekspor');

      let nama = (res.name || '').replace(/\.figcraft$/i, '').trim();
      const curParams = new URLSearchParams(location.search.replace(/&amp;/g, '&'));
      const curFile = curParams.get('file') || curParams.get('amp;file') || '';

      if (!nama || nama.toLowerCase() === 'untitled' || nama.toLowerCase() === 'draf') {
        if (curFile) {
          nama = decodeURIComponent(curFile.split('/').pop().replace(/\.figcraft$/i, ''));
        } else {
          nama = prompt('Beri nama proyek desain ini:', 'Ray-Sniff') || '';
        }
      }

      nama = nama.trim();
      if (!nama) {
        showToast('Penyimpanan dibatalkan (nama kosong).', 'ℹ️', 3000);
        return;
      }

      const slug = nama.toLowerCase().replace(/[^a-z0-9_-]+/g, '-').replace(/^-+|-+$/g, '') || 'desain-manual';

      showToast('Menyimpan ' + nama + ' ke server & merender preview…', '💾', 6000);

      const r = await fetch('/api/simpan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          proyek: slug,
          nama: slug,
          data_base64: res.data
        })
      });

      const json = await r.json();
      if (!json.ok) throw new Error(json.galat || 'Gagal menyimpan ke server');

      showToast('Desain "' + nama + '" berhasil disimpan ke server!', '✅', 4000);
      await loadProjects();

      const newUrl = '/buka.html?webgl&file=' + json.file;
      history.replaceState(null, '', newUrl);

    } catch (err) {
      console.error('[SimpanKeServer] Galat:', err);
      showToast('Gagal: ' + (err.message || err), '❌', 5000);
    } finally {
      if (btn) {
        btn.innerHTML = oldHtml;
        btn.disabled = false;
      }
    }
  }

  function toggleDrawer() {
    const drawer = document.getElementById('fc_drawer');
    const backdrop = document.getElementById('fc_drawer_backdrop');
    if (drawer.classList.contains('open')) {
      closeDrawer();
    } else {
      drawer.classList.add('open');
      backdrop.classList.add('open');
      document.getElementById('fc_search_input').focus();
    }
  }

  function closeDrawer() {
    const drawer = document.getElementById('fc_drawer');
    const backdrop = document.getElementById('fc_drawer_backdrop');
    if (drawer) drawer.classList.remove('open');
    if (backdrop) backdrop.classList.remove('open');
  }

  // 2. Muat Katalog Proyek dari server
  async function loadProjects() {
    try {
      const res = await fetch('./pratinjau/proyek.json?t=' + Date.now(), { cache: 'no-cache' });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      projectsData = data.projects || [];
      const badge = document.getElementById('fc_badge_total');
      if (badge) badge.textContent = projectsData.length;
      const sub = document.getElementById('fc_drawer_sub');
      if (sub) sub.textContent = `${projectsData.length} proyek tersimpan di server`;
      renderProjectList();
    } catch (e) {
      console.warn('[FigCraft Riwayat] Gagal memuat proyek.json:', e);
      const list = document.getElementById('fc_project_list');
      if (list) list.innerHTML = `<div style="text-align: center; padding: 30px; color: var(--fc-text-muted);">Gagal memuat katalog: ${e.message}</div>`;
    }
  }

  function renderProjectList(keyword = '') {
    const list = document.getElementById('fc_project_list');
    if (!list) return;

    const filtered = projectsData.filter(p => {
      if (!keyword) return true;
      return p.proyek.toLowerCase().includes(keyword) ||
             p.nama.toLowerCase().includes(keyword) ||
             p.tanggal.toLowerCase().includes(keyword);
    });

    if (filtered.length === 0) {
      list.innerHTML = `<div style="text-align: center; padding: 30px; color: var(--fc-text-muted);">Tidak ada proyek yang cocok dengan "${keyword}"</div>`;
      return;
    }

    // Identifikasi file yang saat ini sedang dibuka
    const curParams = new URLSearchParams(location.search.replace(/&amp;/g, '&'));
    const curFile = curParams.get('file') || curParams.get('amp;file') || '';

    list.innerHTML = filtered.map(p => {
      const isActive = curFile && p.file.endsWith(curFile);
      const thumb = p.png
        ? `<img src="${p.png}" alt="${p.nama}" loading="lazy" onerror="this.parentElement.innerHTML='🎨';">`
        : `🎨`;

      return `
        <div class="fc-card" style="${isActive ? 'border-color: var(--fc-primary); background: rgba(211,0,26,0.03);' : ''}">
          <div class="fc-card-thumb">${thumb}</div>
          <div class="fc-card-info">
            <div>
              <div class="fc-card-title" title="${p.judul}">${p.judul}</div>
              <div class="fc-card-sub" title="${p.nama}">${p.nama}</div>
            </div>
            <div class="fc-card-meta">
              <span>🕒 ${p.tanggal}</span>
              <div class="fc-card-actions">
                ${isActive
                  ? `<span style="font-size: 11px; font-weight: 600; color: var(--fc-primary);">Aktif</span>`
                  : `<a href="${p.buka_url}" class="fc-btn fc-btn-primary fc-btn-sm">Buka</a>`
                }
              </div>
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  // 3. Live Auto-Reload System (Khusus di buka.html saat ada file)
  function initLiveSync() {
    const qParams = new URLSearchParams(location.search.replace(/&amp;/g, '&'));
    const file = qParams.get('file') || qParams.get('amp;file');
    if (!file) {
      // Jika di index.html (tanpa file), buka drawer secara otomatis setelah 600ms
      // agar user langsung melihat daftar proyeknya
      if (!sessionStorage.getItem('fc_drawer_shown')) {
        sessionStorage.setItem('fc_drawer_shown', '1');
        setTimeout(() => {
          toggleDrawer();
          showToast('Menampilkan 36 proyek yang tersimpan di server', '📂', 4000);
        }, 600);
      }
      return;
    }

    // Tampilkan pill "Live Sync"
    const pill = document.getElementById('fc_live_pill');
    const dot = document.getElementById('fc_live_dot');
    const liveText = document.getElementById('fc_live_text');
    if (pill) pill.style.display = 'inline-flex';

    let lastMtime = null;
    let lastLen = null;
    let isUpdating = false;
    const fileUrl = new URL(file, location.href).href;
    const fileName = decodeURIComponent(file.split('/').pop());

    // Ambil timestamp awal
    fetch(fileUrl, { method: 'HEAD', cache: 'no-cache' })
      .then(r => {
        if (r.ok) {
          lastMtime = r.headers.get('Last-Modified');
          lastLen = r.headers.get('Content-Length');
        }
      })
      .catch(() => {});

    // Polling setiap 2.5 detik
    setInterval(async () => {
      if (isUpdating || document.hidden) return;

      try {
        const head = await fetch(fileUrl, { method: 'HEAD', cache: 'no-cache' });
        if (!head.ok) return;

        const newMtime = head.headers.get('Last-Modified');
        const newLen = head.headers.get('Content-Length');

        if (lastMtime && newMtime && (newMtime !== lastMtime || (newLen && newLen !== lastLen))) {
          isUpdating = true;
          if (dot) dot.classList.add('updating');
          if (liveText) liveText.textContent = 'Memperbarui...';
          showToast('AI melakukan perubahan! Memuat versi terbaru…', '🔄', 4000);

          lastMtime = newMtime;
          lastLen = newLen;

          const res = await fetch(fileUrl, { cache: 'no-cache' });
          if (res.ok && window.figcraft) {
            const bytes = new Uint8Array(await res.arrayBuffer());
            const oldIdx = window.__bukaHasil ? window.__bukaHasil.index : 0;
            const rNew = await window.figcraft.openFile(fileName, bytes);

            if (rNew && typeof rNew.index === 'number' && rNew.index !== oldIdx) {
              try {
                await window.figcraft.execute('file.close', { index: oldIdx, force: true });
              } catch (e) {}
            }
            window.__bukaHasil = rNew;
            try { await window.figcraft.execute('view.zoomFit', {}); } catch (e) {}

            showToast('Desain berhasil diperbarui secara live!', '✅', 3500);
            loadProjects(); // sinkronkan katalog
          }
        }
      } catch (err) {
        console.debug('[LiveSync] Polling error:', err);
      } finally {
        isUpdating = false;
        if (dot) dot.classList.remove('updating');
        if (liveText) liveText.textContent = 'Live Sync';
      }
    }, 2500);
  }

  // Jalankan saat DOM siap
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      injectUI();
      loadProjects();
      initLiveSync();
    });
  } else {
    injectUI();
    loadProjects();
    initLiveSync();
  }
})();

