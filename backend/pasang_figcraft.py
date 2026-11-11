#!/usr/bin/env python3
"""Model "FigCraft" di Open WebUI: otak gpt-5.6-sol + Tool FigCraft + skill INTEK.

Dijalankan di dalam container open-webui (lihat pasang.sh). Lewat API
admin resmi saja:
  1. Tool `figcraft` (berkas figcraft_tool.py; valve api_key diisi dari env FIGCRAFT_KEY) -> /api/v1/tools/create|update.
     Hanya admin yang bisa mengubahnya; dibaca semua user (grant user "*").
  2. Model `figcraft` -> base `gpt-5.6-sol`, system prompt = skill_figcraft.md,
     toolIds = ["figcraft"], function calling native, akses baca semua user.
Model Penpot/FreeCAD tidak disentuh. Aman diulang.
Env: OWUI_ADMIN_ID, FIGCRAFT_KEY.
"""
import json
import os
import sys
import urllib.error
import urllib.request

from open_webui.utils.auth import create_token

BASE = "http://127.0.0.1:8080"
DIR = os.path.dirname(os.path.abspath(__file__))
token = create_token({"id": os.environ["OWUI_ADMIN_ID"]})
PUBLIK = [{"principal_type": "user", "principal_id": "*", "permission": "read"}]


def api(path, body=None):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode() if body is not None else None,
                                 method="POST" if body is not None else "GET",
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"galat": e.code, "isi": e.read().decode()[:300]}


def ada(path):
    r = api(path)
    return bool(r) and "galat" not in r


laporan = {}

# 1) Tool FigCraft
tool = {"id": "figcraft", "name": "FigCraft", "content": open(os.path.join(DIR, "figcraft_tool.py")).read(),
        "meta": {"description": "Desain UI INTEK di FigCraft lewat jembatan figcraft-api :8794"}, "access_grants": PUBLIK}
r = api("/api/v1/tools/id/figcraft/update", tool) if ada("/api/v1/tools/id/figcraft") else api("/api/v1/tools/create", tool)
laporan["tool"] = r.get("id") or r
# Kunci jembatan disimpan sebagai valve tool (hanya admin yang bisa melihat valves).
r = api("/api/v1/tools/id/figcraft/valves/update", {"api_url": "http://host.docker.internal:8794",
                                                     "api_key": os.environ["FIGCRAFT_KEY"], "timeout_detik": 360})
laporan["valves"] = "ok" if "galat" not in r else r

# 2) Model dasar 9router harus bisa dibaca user biasa juga: Open WebUI menolak
#    ("Model not found") model preset yang base model-nya tidak terlihat oleh
#    user. Polanya sama dengan model publik lain (gpt-5.6-sol, worker, ...).
BASE_MODEL = "9router.cc/claude-sonnet-5"
r = api("/api/v1/models/model/access/update", {"id": BASE_MODEL, "name": BASE_MODEL, "access_grants": PUBLIK})
laporan["akses_model_dasar"] = r.get("id") or r

# 3) Model FigCraft -> claude-sonnet-5 lewat 9router
model = {
    "id": "figcraft",
    "name": "FigCraft",
    "base_model_id": BASE_MODEL,   # lewat 9router: otak claude-sonnet-5
    "is_active": True,
    "params": {"system": open(os.path.join(DIR, "skill_figcraft.md")).read(), "function_calling": "native"},
    "meta": {
        "description": "Desainer UI INTEK di FigCraft (http://172.15.50.14:18767/?webgl), otak claude-sonnet-5 lewat 9router. "
                       "Hasil dibuka di editor FigCraft; desain beberapa layar bisa butuh beberapa menit.",
        "profile_image_url": "/static/favicon.png",
        "capabilities": {"vision": True, "citations": False},
        "toolIds": ["figcraft"],
        "tags": [{"name": "figcraft"}],
    },
    "access_grants": PUBLIK,
}
r = api("/api/v1/models/model/update?id=figcraft", model) if ada("/api/v1/models/model?id=figcraft") \
    else api("/api/v1/models/create", model)
laporan["model"] = {"id": r.get("id"), "base": r.get("base_model_id"),
                    "tools": (r.get("meta") or {}).get("toolIds")} if "galat" not in r else r

print(json.dumps(laporan, indent=1, ensure_ascii=False))
sys.exit(1 if any(isinstance(v, dict) and "galat" in v for v in laporan.values()) else 0)
