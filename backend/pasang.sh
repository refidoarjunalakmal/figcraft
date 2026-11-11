#!/bin/bash
# Pasang/selaraskan model "FigCraft" di Open WebUI lewat API admin resmi.
#   ./pasang.sh   -> salin berkas ke container, jalankan, hapus lagi
# Kunci jembatan dibaca dari ./.kunci (0600), tidak pernah dicetak.
set -euo pipefail
cd "$(dirname "$0")"
ADMIN_ID="4fafff31-7242-43a0-8bd0-9c2b5166117c"   # admin@ai.stack (sama dengan owui-penpot)
D="/tmp/owui_figcraft_$$"
docker exec open-webui mkdir -p "$D"
trap 'docker exec open-webui rm -rf "$D"' EXIT
for f in pasang_figcraft.py figcraft_tool.py skill_figcraft.md; do docker cp "$f" "open-webui:$D/$f"; done
docker exec -w /app/backend -e PYTHONPATH=/app/backend -e OWUI_ADMIN_ID="$ADMIN_ID" -e FIGCRAFT_KEY="$(cat .kunci)" \
  open-webui python3 "$D/pasang_figcraft.py"
