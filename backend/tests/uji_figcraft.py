"""Uji sebagai user biasa: model FigCraft terlihat dan benar-benar membangun desain lewat tool (streaming)."""
import json, sqlite3, time, urllib.request
from open_webui.utils.auth import create_token
c = sqlite3.connect("file:/app/backend/data/webui.db?mode=ro", uri=True)
uid = c.execute("select id from user where role='user' order by created_at limit 1").fetchone()[0]
tok = create_token({"id": uid})
def req(path, body=None, t=60):
    return urllib.request.Request("http://127.0.0.1:8080" + path, data=json.dumps(body).encode() if body else None,
                                  method="POST" if body else "GET",
                                  headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
m = [x for x in json.loads(urllib.request.urlopen(req("/api/models"), timeout=60).read())["data"] if x["id"] == "figcraft"]
print("model terlihat user biasa:", bool(m), "| base:", m and (m[0].get("info") or {}).get("base_model_id"))
t = time.time(); teks = []; tool = []
r = req("/api/chat/completions", {"model": "figcraft", "stream": True, "tool_ids": ["figcraft"],
        "messages": [{"role": "user", "content": "Langsung panggil figcraft_bangun (tanpa figcraft_perintah). Uji singkat: buat 1 layar desktop 1280x800 proyek 'uji-owui' nama 'kartu-ringkasan' berisi judul 'Ringkasan Gudang' (Heading/L), teks 'Data contoh' (Body/M), dan 3 komponen Card berdampingan (Stok masuk / Stok keluar / Barang kritis) dengan angka contoh. Lalu lihat hasilnya dan beri tautan editor."}]})
for raw in urllib.request.urlopen(r, timeout=900):
    l = raw.decode(errors="ignore").strip()
    if not l.startswith("data:") or l.endswith("[DONE]"): continue
    try: d = json.loads(l[5:])
    except ValueError: continue
    for ch in d.get("choices") or []:
        dl = ch.get("delta") or {}
        teks.append(dl.get("content") or "")
        for tc in dl.get("tool_calls") or []:
            n = (tc.get("function") or {}).get("name")
            if n: tool.append(n)
print("durasi %.0f detik | tool dipanggil: %s" % (time.time() - t, tool))
print("jawaban:", "".join(teks)[-900:].replace("\n", " "))
