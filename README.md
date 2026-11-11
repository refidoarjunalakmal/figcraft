# FigCraft Web & AI Integration Suite

Suite web editor dan jembatan AI untuk **FigCraft** (vektor UI design & prototyping engine berbasis pure Rust/WebAssembly). Dilengkapi fitur kustom INTEK: kanvas web otomatis, auto-load font OFL, drawer riwayat proyek, live sync, serta jembatan Open WebUI / AI Tooling.

---

## 📁 Struktur Repositori

```text
figcraft/
├── docker-compose.yml          # Konfigurasi container Nginx port 18767
├── nginx/
│   └── default.conf            # Konfigurasi Nginx (WASM caching, CORS, API reverse proxy)
├── static/                     # Web static bundle (FigCraft WASM + Custom Web UI)
│   ├── index.html              # Editor FigCraft utama (?control & ?webgl auto-param)
│   ├── buka.html               # File viewer & loader desain langsung via URL
│   ├── galeri.html             # Visual gallery dark-mode untuk seluruh proyek desain
│   ├── riwayat.js              # Floating action bar (Simpan Ctrl+S, Drawer Riwayat, Live Sync)
│   ├── riwayat.css             # Desain styling antarmuka riwayat & drawer
│   ├── fonts/                  # Custom font loader (Oxanium, Roboto, OFL fonts)
│   ├── snippets/               # Inlined JS dependencies
│   ├── *.wasm & *.js           # Engine inti FigCraft WASM v0.15.0
│   └── pratinjau/              # Folder mount lokal untuk berkas .figcraft dan .png
├── backend/                    # Layanan Jembatan API & AI Tooling
│   ├── figcraft_api.py         # HTTP service pengontrol figcraft-cli & render katalog
│   ├── figcraft_tool.py        # Tool function calling native untuk Open WebUI
│   ├── skill_figcraft.md       # System prompt & aturan desain UI Kit
│   ├── pasang_figcraft.py      # Script otomatisasi instalasi model & tool ke Open WebUI
│   ├── pasang.sh               # Runner setup tool
│   └── library/
│       └── intek-design-system.figcraft # Library komponen UI INTEK (KPI cards, tabel, dll)
├── .env.example                # Contoh konfigurasi environment
├── .gitignore                  # Filter berkas internal/besar (.kunci, pratinjau/*, dsb)
└── README.md
```

---

## 🚀 Cara Menjalankan

### 1. Menjalankan Web Editor (Port 18767)

Pastikan Docker & Docker Compose sudah terpasang.

```bash
# Jalankan container web editor
docker compose up -d
```

Akses layanan melalui browser:
* **Editor Langsung**: `http://<IP_HOST>:18767/?webgl`
* **Galeri Proyek**: `http://<IP_HOST>:18767/galeri.html`
* **Buka Desain Tertentu**: `http://<IP_HOST>:18767/buka.html?webgl&file=pratinjau/owui/<proyek>/<nama>.figcraft`

---

### 2. Menjalankan Backend Jembatan (API)

Backend bertugas menerima perintah kompilasi dari AI atau Web Editor, memanggil `figcraft-cli`, dan menghasilkan snapshot PNG thumbnail.

1. Siapkan file kunci atau environment variable:
   ```bash
   cp .env.example .env
   # Edit .env dan sesuaikan FIGCRAFT_API_KEY
   ```
2. Jalankan server API (port default `8794`):
   ```bash
   cd backend
   python3 figcraft_api.py
   ```

---

## 🎨 Fitur Kustom yang Ditanamkan

1. **Auto WebGL2 & Control Injection**:
   Secara otomatis memaksakan parameter `?control&webgl` pada URL agar kanvas siap menerima perintah API `window.figcraft`.
2. **Font Loader Interaktif (`buka.html`)**:
   Memuat font spesifik (`oxanium.ttf`, `roboto.ttf`) ke WebAssembly runtime sebelum file desain dibuka, mencegah teks rusak atau fallback font yang tidak sesuai.
3. **Riwayat Proyek & Auto-Reload (`riwayat.js`)**:
   * **Tombol Simpan (Ctrl+S)**: Mengirimkan snapshot desain terkini dari kanvas kembali ke server (`/api/simpan`).
   * **Drawer Proyek**: Pencarian instan dan navigasi cepat ke file desain lain.
   * **Live Sync**: Otomatis me-reload kanvas saat AI selesai menyunting berkas desain di background.
4. **Galeri Visual (`galeri.html`)**:
   Halaman portal modern bertema gelap untuk menampilkan kartu katalog thumbnail dari file `pratinjau/proyek.json`.

---

## 📄 Lisensi
- FigCraft engine inti dilisensikan di bawah **MIT / Apache-2.0** oleh Storyteller / ArtCraft.
- Skrip integrasi, Nginx bundle, dan web wrapper dikembangkan untuk INTEK Design System.

