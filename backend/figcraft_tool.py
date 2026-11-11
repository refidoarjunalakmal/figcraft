"""
title: FigCraft
author: INTEK
description: Desain layar UI dengan design system INTEK di FigCraft (http://172.15.50.14:18767/?webgl) -- bangun desain dari langkah perintah, lihat hasilnya sebagai gambar, cek struktur, dan ekspor SVG/PDF/Penpot.
version: 1.0.0
"""

import json
import urllib.error
import urllib.request

from pydantic import BaseModel, Field

# Jembatan figcraft-cli di host .14 (systemd user `figcraft-api`), hanya terjangkau
# dari container lewat host.docker.internal.
DEFAULT_URL = "http://host.docker.internal:8794"


class Tools:
    class Valves(BaseModel):
        api_url: str = Field(default=DEFAULT_URL, description="Alamat jembatan figcraft-api")
        api_key: str = Field(default="", description="X-Api-Key jembatan (~/owui-figcraft/.kunci)")
        timeout_detik: int = Field(default=360, description="Batas waktu satu panggilan")

    def __init__(self):
        self.valves = self.Valves()

    def _post(self, path: str, body: dict) -> dict:
        req = urllib.request.Request(self.valves.api_url.rstrip("/") + path, data=json.dumps(body).encode(),
                                     method="POST", headers={"Content-Type": "application/json",
                                                             "X-Api-Key": self.valves.api_key})
        try:
            with urllib.request.urlopen(req, timeout=self.valves.timeout_detik) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            try:
                return json.loads(e.read())
            except Exception:
                return {"ok": False, "galat": f"HTTP {e.code}"}
        except Exception as e:
            return {"ok": False, "galat": f"{type(e).__name__}: {str(e)[:300]}"}

    def figcraft_bangun(self, proyek: str, nama: str, langkah_json: str, lanjutkan: bool = False) -> str:
        """
        Bangun (atau lanjutkan) desain FigCraft dari daftar langkah perintah, simpan, dan buat pratinjau.
        Library INTEK otomatis dipasang di langkah pertama. Semua langkah dijalankan sebagai SATU
        kesatuan: kalau satu langkah salah, tidak ada yang disimpan -- perbaiki lalu kirim ulang.
        :param proyek: Nama proyek/folder, misalnya "inventori-gudang".
        :param nama: Nama desain, misalnya "dashboard".
        :param langkah_json: JSON array langkah, tiap langkah {"command": "...", "params": {...}, "as": "nama_ref"?}. Rujuk node yang dibuat sebelumnya dengan {"$ref": "nama_ref"}.
        :param lanjutkan: true = tambahkan ke desain yang sudah ada dengan nama sama; false = desain baru.
        """
        try:
            langkah = json.loads(langkah_json)
        except Exception as e:
            return f"GAGAL: langkah_json bukan JSON yang sah ({e})."
        r = self._post("/bangun", {"proyek": proyek, "nama": nama, "langkah": langkah, "lanjutkan": lanjutkan})
        if not r.get("ok"):
            return "GAGAL: " + str(r.get("galat")) + (" " + r["catatan"] if r.get("catatan") else "")
        return (f"Desain tersimpan ({r.get('langkah')} langkah).\n"
                f"Buka di editor FigCraft: {r.get('editor')}\n"
                f"Pratinjau PNG: {r.get('pratinjau_png')}\n"
                "Panggil figcraft_lihat untuk memeriksa tampilannya sebelum menyatakan selesai.")

    def figcraft_lihat(self, proyek: str, nama: str, board: str = "1") -> str:
        """
        Lihat SATU board desain sebagai gambar kecil untuk diperiksa (teks terpotong, tumpang tindih,
        perataan, kontras). Desain dengan banyak board: panggil sekali per board (board="1", "2", ...).
        Jawaban selalu menyebut daftar semua board.
        :param proyek: Nama proyek yang sama dengan saat dibangun.
        :param nama: Nama desain yang sama dengan saat dibangun.
        :param board: Nomor urut board (1, 2, ...) atau nama board. Bawaan: 1.
        """
        r = self._post("/render", {"proyek": proyek, "nama": nama, "board": board})
        daftar = ", ".join(f"{i}. {n}" for i, n in enumerate(r.get("boards") or [], 1))
        if not r.get("ok"):
            return "GAGAL: " + str(r.get("galat")) + (f"\nBoard yang ada: {daftar}" if daftar else "")
        return (f"Board {r['urutan']}/{len(r['boards'])}: {r['board']} ({r['ukuran']}, diperkecil untuk diperiksa)\n"
                f"Semua board: {daftar}\n"
                f"![{r['board']}](data:image/jpeg;base64,{r['jpg_base64']})")

    def figcraft_info(self, proyek: str, nama: str) -> str:
        """
        Ringkasan struktur desain: halaman, jumlah node, dan frame tingkat atas beserta ukurannya.
        :param proyek: Nama proyek.
        :param nama: Nama desain.
        """
        r = self._post("/info", {"proyek": proyek, "nama": nama})
        return r.get("info") if r.get("ok") else "GAGAL: " + str(r.get("galat"))

    def figcraft_ekspor(self, proyek: str, nama: str, format: str = "pdf") -> str:
        """
        Ekspor desain ke svg, pdf, penpot (arsip Penpot 2.x), atau png resolusi 2x, lalu kembalikan tautan unduh.
        :param proyek: Nama proyek.
        :param nama: Nama desain.
        :param format: svg, pdf, penpot, atau png.
        """
        r = self._post("/ekspor", {"proyek": proyek, "nama": nama, "format": format})
        return f"Unduh: {r['unduh']}" if r.get("ok") else "GAGAL: " + str(r.get("galat"))

    def figcraft_perintah(self, cari: str = "") -> str:
        """
        Cari dokumentasi perintah FigCraft beserta parameternya (misalnya "node.create", "library", "text.").
        :param cari: Kata kunci nama perintah.
        """
        r = self._post("/perintah", {"cari": cari})
        return r.get("perintah") if r.get("ok") else "GAGAL: " + str(r.get("galat"))
