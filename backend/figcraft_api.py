#!/usr/bin/env python3
"""Jembatan HTTP kecil: Open WebUI (container) -> figcraft-cli di host .14.

Open WebUI berjalan di container tanpa figcraft-cli, jadi tool-nya memanggil
layanan ini (pola sama dengan FreeCAD RPC :9875). Semua berkas dikurung di
/home/aisanbox/figcraft-work/owui/<proyek>/ dan figcraft-cli selalu dijalankan
dengan --automation-read-root/--automation-write-root ke figcraft-work.

Endpoint (POST JSON, header X-Api-Key wajib):
  /bangun   {proyek, nama, langkah:[{command, params, as?}]}
            -> jalankan skrip, simpan .figcraft, render PNG, salin ke editor web
  /render   {proyek, nama}           -> PNG base64 (untuk dilihat model)
  /info     {proyek, nama}           -> ringkasan halaman/frame
  /ekspor   {proyek, nama, format}   -> svg|pdf|penpot, kembalikan tautan unduh
  /perintah {cari}                   -> dokumentasi perintah figcraft-cli
GET /health

Hanya mendengar di 172.17.0.1 (jembatan docker) dan 127.0.0.1, bukan jaringan kantor.
"""
import base64
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WORK = Path(os.environ.get("FIGCRAFT_WORK", Path.home() / "figcraft-work"))
OWUI = WORK / "owui"
LIB = Path(os.environ.get("FIGCRAFT_LIB", Path(__file__).parent / "library/intek-design-system.figcraft"))
WEB = Path(os.environ.get("FIGCRAFT_WEB", Path(__file__).parent.parent / "static"))
PRATINJAU = WEB / "pratinjau" / "owui"
WEB_BASE = os.environ.get("FIGCRAFT_WEB_BASE", "http://localhost:18767")
CLI = os.environ.get("FIGCRAFT_CLI", shutil.which("figcraft-cli") or str(Path.home() / ".local/bin/figcraft-cli"))
ROOT = ["--automation-read-root", str(WORK), "--automation-write-root", str(WORK)]

kunci_file = Path(__file__).with_name(".kunci")
if kunci_file.exists():
    KUNCI = kunci_file.read_text().strip()
else:
    KUNCI = os.environ.get("FIGCRAFT_API_KEY", "YOUR_API_KEY_HERE")

HOST = os.environ.get("FIGCRAFT_API_HOST", "172.17.0.1")
PORT = int(os.environ.get("FIGCRAFT_API_PORT", "8794"))
MAKS_LANGKAH = 4000
KUNCI_PROYEK = threading.Lock()   # satu build per waktu: figcraft-cli berat di CPU


def aman(s, cadangan="desain"):
    s = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(s or "")).strip("-").lower()[:60]
    return s or cadangan


def jalur(proyek, nama, ext):
    d = OWUI / aman(proyek, "umum")
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{aman(nama)}.{ext}"


def cli(args, timeout=300):
    p = subprocess.run([CLI, *args], capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout or "")[-6000:], (p.stderr or "")[-3000:]


def tautan_editor(fig):
    tujuan = PRATINJAU / fig.parent.name
    tujuan.mkdir(parents=True, exist_ok=True)
    shutil.copy2(fig, tujuan / fig.name)
    return f"{WEB_BASE}/buka.html?webgl&file=pratinjau/owui/{fig.parent.name}/{fig.name}"


def tautan_unduh(berkas):
    tujuan = PRATINJAU / berkas.parent.name
    tujuan.mkdir(parents=True, exist_ok=True)
    shutil.copy2(berkas, tujuan / berkas.name)
    return f"{WEB_BASE}/pratinjau/owui/{berkas.parent.name}/{berkas.name}"


def render(fig, png, skala=1):
    return cli(["render", str(fig), "-o", str(png), "--scale", str(skala), *ROOT], timeout=180)


def perbarui_katalog():
    """Perbarui pratinjau/proyek.json setiap kali ada desain baru atau direvisi."""
    try:
        projects = []
        if PRATINJAU.exists():
            for f in PRATINJAU.glob("**/*.figcraft"):
                png = f.with_suffix(".png")
                rel_fig = str(f.relative_to(WEB))
                rel_png = str(png.relative_to(WEB)) if png.exists() else None
                stat = f.stat()
                projects.append({
                    "id": f"{f.parent.name}_{f.stem}",
                    "proyek": f.parent.name,
                    "nama": f.name,
                    "judul": f.parent.name.replace("-", " ").title(),
                    "mtime": stat.st_mtime,
                    "tanggal": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d %b %Y, %H:%M"),
                    "size": stat.st_size,
                    "file": rel_fig,
                    "png": rel_png,
                    "buka_url": f"/buka.html?webgl&file={rel_fig}"
                })
        projects.sort(key=lambda x: x["mtime"], reverse=True)
        out_file = WEB / "pratinjau" / "proyek.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps({"total": len(projects), "projects": projects}, indent=2, ensure_ascii=False))
    except Exception as e:
        sys.stderr.write(f"[perbarui_katalog] galat: {e}\n")


def bangun(b):
    langkah = b.get("langkah")
    if not isinstance(langkah, list) or not langkah or len(langkah) > MAKS_LANGKAH:
        return 400, {"ok": False, "galat": f"langkah wajib list 1..{MAKS_LANGKAH}"}
    for l in langkah:
        if not isinstance(l, dict) or "command" not in l:
            return 400, {"ok": False, "galat": "tiap langkah wajib {command, params}"}
        if l["command"] == "library.add":     # library selalu dipasang oleh jembatan
            l.setdefault("params", {})["path"] = str(LIB)
    if langkah[0].get("command") != "library.add":
        langkah.insert(0, {"command": "library.add", "params": {"path": str(LIB)}})
    fig = jalur(b.get("proyek"), b.get("nama"), "figcraft")
    with tempfile.NamedTemporaryFile("w", suffix=".json", dir=fig.parent, delete=False) as f:
        json.dump(langkah, f, ensure_ascii=False)
        skrip = f.name
    try:
        args = ["run", skrip, "--out", str(fig), *ROOT]
        if b.get("lanjutkan") and fig.exists():
            args[2:2] = ["--in", str(fig)]
        with KUNCI_PROYEK:
            rc, out, err = cli(args)
    finally:
        os.unlink(skrip)
    gagal = [l for l in out.splitlines() if '"ok":false' in l.replace(" ", "")]
    if rc != 0 or gagal:
        return 200, {"ok": False, "galat": (gagal[0] if gagal else err or out)[-1500:],
                     "catatan": "Skrip dijalankan sebagai satu kesatuan: satu langkah gagal = tidak ada yang disimpan."}
    png = fig.with_suffix(".png")
    render(fig, png)
    ed = tautan_editor(fig)
    pu = tautan_unduh(png) if png.exists() else None
    perbarui_katalog()
    return 200, {"ok": True, "file": str(fig.relative_to(WORK)), "editor": ed,
                 "pratinjau_png": pu,
                 "langkah": len(langkah)}


LIHAT_SISI_MAKS = 1280      # px sisi terpanjang gambar yang dikirim ke model
LIHAT_KB_MAKS = 350         # batas ukuran JPEG; base64-nya ~470 rb karakter


def _kecilkan(png, sisi=LIHAT_SISI_MAKS, kb=LIHAT_KB_MAKS):
    """PNG -> JPEG kecil. Dulu PNG utuh dikirim: desain 6 board = 9040x1024,
    base64 ~1,5 juta karakter, melebihi konteks model (3 Nov 2026)."""
    import io
    from PIL import Image
    im = Image.open(png).convert("RGB")
    im.thumbnail((sisi, sisi), Image.LANCZOS)
    for q in (80, 65, 50, 40):
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=q, optimize=True)
        if buf.tell() <= kb * 1024:
            break
    return buf.getvalue(), im.size


def lihat(b):
    """Gambar SATU board (frame tingkat atas) per panggilan, dikecilkan.
    `board` = nomor urut (1..n) atau nama board; kosong = board pertama.
    Selalu mengembalikan daftar board supaya model bisa memeriksa satu per satu."""
    fig = jalur(b.get("proyek"), b.get("nama"), "figcraft")
    if not fig.exists():
        return 404, {"ok": False, "galat": "desain belum ada"}
    folder = fig.parent / (fig.stem + "-boards")
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir()
    try:
        rc, out, err = cli(["export", str(fig), "-o", str(folder), "--format", "png", *ROOT], timeout=180)
        boards = sorted(folder.glob("*.png"))
        if rc != 0 or not boards:
            return 200, {"ok": False, "galat": (err or out)[-800:] or "tidak ada board"}
        nama = [p.stem for p in boards]
        pilih = str(b.get("board") or "1").strip()
        if pilih.isdigit() and 1 <= int(pilih) <= len(boards):
            p = boards[int(pilih) - 1]
        else:
            cocok = [x for x in boards if x.stem.lower() == pilih.lower()] or \
                    [x for x in boards if pilih.lower() in x.stem.lower()]
            if not cocok:
                return 200, {"ok": False, "galat": f"board '{pilih}' tidak ada", "boards": nama}
            p = cocok[0]
        data, ukuran = _kecilkan(p)
        return 200, {"ok": True, "board": p.stem, "urutan": boards.index(p) + 1, "boards": nama,
                     "ukuran": f"{ukuran[0]}x{ukuran[1]}", "jpg_base64": base64.b64encode(data).decode()}
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def info(b):
    fig = jalur(b.get("proyek"), b.get("nama"), "figcraft")
    if not fig.exists():
        return 404, {"ok": False, "galat": "desain belum ada"}
    rc, out, err = cli(["info", str(fig), *ROOT], timeout=60)
    return 200, {"ok": rc == 0, "info": out or err}


def ekspor(b):
    fmt = str(b.get("format") or "").lower()
    if fmt not in ("svg", "pdf", "penpot", "png"):
        return 400, {"ok": False, "galat": "format: svg|pdf|penpot|png"}
    fig = jalur(b.get("proyek"), b.get("nama"), "figcraft")
    if not fig.exists():
        return 404, {"ok": False, "galat": "desain belum ada"}
    out_f = fig.with_suffix("." + fmt)
    args = ["export", str(fig), "-o", str(out_f), "--format", fmt, *ROOT] if fmt != "png" \
        else ["render", str(fig), "-o", str(out_f), "--scale", "2", *ROOT]
    rc, out, err = cli(args, timeout=240)
    if rc != 0 or not out_f.exists():
        return 200, {"ok": False, "galat": (err or out)[-800:]}
    return 200, {"ok": True, "unduh": tautan_unduh(out_f)}


def perintah(b):
    cari = str(b.get("cari") or "")[:60]
    rc, out, err = cli(["commands", "--filter", cari] if cari else ["commands"], timeout=30)
    return 200, {"ok": rc == 0, "perintah": out[:6000]}


def simpan(b):
    proyek = aman(b.get("proyek"), "desain-manual")
    nama = aman(b.get("nama"), "desain")
    data_b64 = b.get("data_base64")
    if not data_b64:
        return 400, {"ok": False, "galat": "data_base64 wajib diisi"}
    try:
        raw_bytes = base64.b64decode(data_b64)
    except Exception as e:
        return 400, {"ok": False, "galat": f"base64 tidak valid: {e}"}

    fig = jalur(proyek, nama, "figcraft")
    fig.write_bytes(raw_bytes)

    # render PNG pratinjau
    png = fig.with_suffix(".png")
    with KUNCI_PROYEK:
        render(fig, png)

    # salin ke folder web pratinjau
    editor_url = tautan_editor(fig)
    if png.exists():
        tautan_unduh(png)

    perbarui_katalog()
    rel_fig = f"pratinjau/owui/{fig.parent.name}/{fig.name}"
    return 200, {
        "ok": True,
        "proyek": proyek,
        "nama": nama,
        "file": rel_fig,
        "editor": editor_url,
    }


RUTE = {"/bangun": bangun, "/render": lihat, "/info": info, "/ekspor": ekspor, "/perintah": perintah, "/simpan": simpan}


class H(BaseHTTPRequestHandler):
    def _kirim(self, kode, isi):
        b = json.dumps(isi, ensure_ascii=False).encode()
        self.send_response(kode)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path == "/health":
            return self._kirim(200, {"ok": True, "cli": os.path.exists(CLI), "library": LIB.exists()})
        self._kirim(404, {"ok": False})

    def do_POST(self):
        if self.headers.get("X-Api-Key", "") != KUNCI:
            return self._kirim(401, {"ok": False, "galat": "kunci tidak sah"})
        fn = RUTE.get(self.path)
        if not fn:
            return self._kirim(404, {"ok": False, "galat": "rute tidak ada"})
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if n > 50 * 1024 * 1024:
                return self._kirim(413, {"ok": False, "galat": "muatan terlalu besar"})
            kode, isi = fn(json.loads(self.rfile.read(n) or b"{}"))
        except subprocess.TimeoutExpired:
            kode, isi = 504, {"ok": False, "galat": "figcraft-cli melewati batas waktu"}
        except Exception as e:  # noqa: BLE001
            kode, isi = 500, {"ok": False, "galat": f"{type(e).__name__}: {str(e)[:300]}"}
        self._kirim(kode, isi)

    def log_message(self, fmt, *a):
        print("%s %s" % (self.address_string(), fmt % a), flush=True)


if __name__ == "__main__":
    OWUI.mkdir(parents=True, exist_ok=True)
    perbarui_katalog()
    srv = ThreadingHTTPServer((HOST, PORT), H)
    srv.daemon_threads = True
    print(f"figcraft-api di {HOST}:{PORT}", flush=True)
    srv.serve_forever()
