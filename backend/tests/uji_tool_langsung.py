"""Uji kode Tool FigCraft persis seperti dijalankan Open WebUI: muat dari database + valves tersimpan."""
import asyncio, inspect, json
from open_webui.models.tools import Tools as TT
from open_webui.utils.plugin import load_tool_module_by_id
tunggu = lambda x: asyncio.run(x) if inspect.isawaitable(x) else x
t = tunggu(TT.get_tool_by_id("figcraft"))
mod = tunggu(load_tool_module_by_id("figcraft", content=t.content))
mod = mod[0] if isinstance(mod, tuple) else mod
v = tunggu(TT.get_tool_valves_by_id("figcraft")) or {}
mod.valves = mod.Valves(**v)
print("valves tersimpan:", sorted(v), "| kunci terisi:", bool(v.get("api_key")))
langkah = json.dumps([
 {"command": "file.rename", "params": {"name": "Uji Tool OWUI"}},
 {"command": "node.create", "params": {"type": "frame", "name": "Layar", "props": {"x": 0, "y": 0, "width": 1280, "height": 800, "fill": "#F5F5F5", "layout": "vertical", "padding": 32, "gap": 16}}, "as": "Layar"},
 {"command": "node.create", "params": {"type": "text", "parent": {"$ref": "Layar"}, "text": "Ringkasan Gudang", "name": "Judul"}, "as": "Judul"},
 {"command": "library.applyStyle", "params": {"library": "INTEK Design System", "style": "Heading/L", "ids": [{"$ref": "Judul"}]}},
 {"command": "node.create", "params": {"type": "frame", "name": "Baris", "parent": {"$ref": "Layar"}, "props": {"layout": "horizontal", "gap": 16, "sizingH": "fill", "sizingV": "hug", "fill": "none"}}, "as": "Baris"},
] + [x for i, (j, b) in enumerate([("Stok masuk", "128 unit · data contoh"), ("Stok keluar", "96 unit · data contoh"), ("Barang kritis", "7 item · data contoh")]) for x in (
 {"command": "library.place", "params": {"library": "INTEK Design System", "component": "Card"}, "as": f"K{i}"},
 {"command": "node.reparent", "params": {"ids": [{"$ref": f"K{i}"}], "parent": {"$ref": "Baris"}}},
 {"command": "instance.setProperties", "params": {"ids": [{"$ref": f"K{i}"}], "properties": {"Title": j, "Body": b}}})])
print("bangun:", mod.figcraft_bangun("uji-owui", "uji-tool", langkah))
print("lihat:", mod.figcraft_lihat("uji-owui", "uji-tool")[:60], "...")
print("ekspor:", mod.figcraft_ekspor("uji-owui", "uji-tool", "penpot"))
