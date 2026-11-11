#!/usr/bin/env python3
"""Bangun library design system INTEK untuk FigCraft.

Sumber kebenaran: ~/penpot/brand-package/company-brand-assets (versi 2026-09-16-red-v1).
- Warna aksen #D3001A / #7E0F12 dari PDF ReBrand (padanan RGB digital, bukan Pantone).
- Font judul Oxanium, isi Roboto: font yang tertanam di PDF ReBrand (contoh penerapan,
  bukan tabel spesifikasi resmi).
- Logo: PNG resmi 1835x374, tidak digambar ulang.

Keluaran: scripts/build_intek_ds.json, dijalankan dengan
  figcraft-cli run scripts/build_intek_ds.json --out library/intek-design-system.figcraft
"""
import json
from pathlib import Path

WORK = Path("/home/aisanbox/figcraft-work")
LOGO = WORK / "assets/brand/intek-logo-red.png"
ICONS = WORK / "assets/icons/lucide"
LOGO_W, LOGO_H = 1835, 374

# Warna tema: Light / Dark. Semua pasangan teks lolos WCAG AA (>= 4.5:1), dihitung 3 Nov 2026.
THEME = {
    "Surface":        ("#FFFFFF", "#141414"),
    "Surface raised": ("#F5F5F5", "#1F1F1F"),
    "Text":           ("#1C1C1E", "#F2F2F2"),
    "Text muted":     ("#5F6368", "#A3A3A3"),
    "Primary":        ("#D3001A", "#FF5A66"),
    "Primary hover":  ("#A50014", "#FF7A84"),
    "On primary":     ("#FFFFFF", "#141414"),
    "Border":         ("#DADCE0", "#3A3A3A"),
    "Danger":         ("#B42318", "#FF8A7A"),
}
SIZES = {"Radius/S": 4, "Radius/M": 8, "Radius/L": 12}

PAINT_STYLES = {
    "Brand/Primary": "#D3001A",
    "Brand/Soft": "#FDECEE",
    "Brand/Accent": "#7E0F12",
    "Text/Primary": "#1C1C1E",
    "Text/Secondary": "#5F6368",
    "Text/On brand": "#FFFFFF",
    "Surface/Page": "#F5F5F5",
    "Surface/Card": "#FFFFFF",
    "Surface/Sunken": "#EDEDED",
    "Border/Default": "#DADCE0",
}

H, B = "Oxanium", "Roboto"
TEXT_STYLES = {  # nama: (family, style, size, line height)
    "Display":   (H, "Bold", 48, 56),
    "Heading/L": (H, "Bold", 30, 38),
    "Heading/M": (H, "SemiBold", 22, 30),
    "Heading/S": (H, "SemiBold", 17, 24),
    "Body/L":    (B, "Regular", 18, 28),
    "Body/M":    (B, "Regular", 15, 22),
    "Body/S":    (B, "Regular", 13, 18),
    "Label/M":   (B, "Medium", 14, 20),
    "Label/S":   (B, "Medium", 12, 16),
}

# Teks contoh template (fiksi "Ridgeline") diganti agar tidak terbawa ke desain INTEK.
REPLACE = {
    "Ridgeline at first light": "Solusi Intek Indonesia",
    "Welcome back": "Masuk ke akun",
    "Sign in to plan your next walk.": "Gunakan email kantor untuk melanjutkan.",
    "mara@ridgeline.example": "nama@contoh.co.id",
    "Sign in": "Masuk",
    "Create an account": "Lupa kata sandi?",
    "Card title": "Judul kartu",
    "A short line that says what this card is about.": "Satu kalimat singkat tentang isi kartu ini.",
    "Open": "Buka",
    "This field is required": "Wajib diisi",
    "Helper text": "Teks bantuan",
    "The Theme collection's colour variables in this mode": "Variabel warna koleksi Theme pada mode ini",
    "The text styles, largest first": "Gaya teks, dari yang terbesar",
    "Number variables for corner radius and spacing": "Variabel angka untuk radius sudut dan jarak",
    "Password": "Kata sandi",
    "Value": "Isi",
    "Button": "Tombol",
}

# Ikon yang sering dipakai di aplikasi internal; sisanya (2.000+) diimpor sesuai kebutuhan.
CORE_ICONS = [
    "house", "layout-dashboard", "menu", "search", "bell", "settings", "user", "users",
    "log-out", "plus", "pencil", "trash", "check", "x", "chevron-down", "chevron-right",
    "chevron-left", "arrow-right", "arrow-left", "download", "upload", "file-text", "folder",
    "calendar", "clock", "mail", "phone", "map-pin", "funnel", "eye", "lock",
    "circle-alert", "circle-check", "info", "triangle-alert", "external-link", "ellipsis",
    "chart-column", "clipboard-list", "truck", "package", "building", "hard-hat", "shield-check",
    # tambahan 3 Nov 2026 untuk aplikasi pemesanan/komersial
    "utensils", "pizza", "soup", "coffee", "salad", "cake-slice", "drumstick", "sandwich",
    "cup-soda", "ice-cream-cone", "star", "heart", "minus", "shopping-bag", "bike",
    "ticket-percent", "wallet", "credit-card", "receipt", "store", "flame", "banknote",
    "navigation", "sliders-horizontal", "circle", "circle-dot",
]


def hexpaint(h):
    return [{"type": "solid", "color": h}]


def text_style(fam, sty, size, lh):
    return {"case": "original", "decoration": "none", "fills": None, "font_family": fam,
            "font_size": float(size), "font_style": sty,
            "letter_spacing": {"unit": "percent", "value": 0.0},
            "line_height": {"unit": "pixels", "value": float(lh)}, "link": None}


# id node di template design-system v0.15.0 (diperiksa lewat `figcraft-cli info`).
COMP_IDS = {"Button": 143, "Input": 159, "Card": 160}


def main():
    s = []
    add = lambda cmd, params, as_=None: s.append({"command": cmd, "params": params, **({"as": as_} if as_ else {})})

    add("file.newFromTemplate", {"template": "design-system"})
    add("file.rename", {"name": "INTEK Design System"})

    for name, (light, dark) in THEME.items():
        add("variable.set", {"variable": name, "mode": "Light", "value": light})
        add("variable.set", {"variable": name, "mode": "Dark", "value": dark})
    for name, v in SIZES.items():
        add("variable.set", {"variable": name, "value": v})

    for name, h in PAINT_STYLES.items():
        add("style.update", {"style": name, "value": hexpaint(h)})
    for name, spec in TEXT_STYLES.items():
        add("style.update", {"style": name, "value": text_style(*spec)})

    # edit.findReplace hanya bekerja di halaman aktif: ulangi per halaman template.
    for page_index in (0, 1):
        add("page.select", {"index": page_index})
        for old, new in REPLACE.items():
            add("edit.findReplace", {"find": old, "replace": new, "select": False})

    # Nilai default properti komponen (findReplace tidak menyentuhnya).
    add("page.select", {"index": 1})
    for comp, prop, val in (("Button", "Label", "Tombol"), ("Input", "Label", "Label"), ("Input", "Value", "Isi"),
                            ("Card", "Title", "Judul kartu"), ("Card", "Body", "Satu kalimat singkat tentang isi kartu ini.")):
        add("component.editProperty", {"id": COMP_IDS[comp], "name": prop, "default": val})

    # Halaman Brand: logo resmi sebagai komponen, proporsi asli.
    add("page.add", {"name": "Brand"}, "brand")
    add("page.select", {"id": {"$ref": "brand"}})
    y = 0
    for label, w in (("Logo/INTEK merah · L", 360), ("Logo/INTEK merah · M", 220), ("Logo/INTEK merah · S", 140)):
        h = round(w * LOGO_H / LOGO_W, 2)
        add("image.place", {"path": str(LOGO), "x": 0, "y": y, "width": w, "height": h,
                            "name": label, "mode": "fit"}, label)
        add("component.create", {"ids": [{"$ref": label}]}, label + "#c")
        y += h + 48

    # Halaman Icons: ikon inti Lucide sebagai komponen 24x24.
    add("page.add", {"name": "Icons"}, "icons")
    add("page.select", {"id": {"$ref": "icons"}})
    for i, name in enumerate(CORE_ICONS):
        p = ICONS / f"{name}.svg"
        if not p.exists():
            raise SystemExit(f"ikon tidak ada: {p}")
        ref = f"ic-{name}"
        add("file.import", {"path": str(p), "x": (i % 11) * 48, "y": (i // 11) * 48}, ref)
        add("node.set", {"ids": [{"$ref": ref}], "props": {"name": f"Icon/{name}"}})
        add("component.create", {"ids": [{"$ref": ref}]}, ref + "#c")

    # Komponen v2 (3 Nov 2026): badge, KPI, tabel, timeline, sidebar, banner, dll.
    import sys
    sys.path.insert(0, str(WORK / "scripts"))
    from komponen_v2 import tambahkan_komponen
    tambahkan_komponen(add, ICONS, TEXT_STYLES)

    out = WORK / "scripts/build_intek_ds.json"
    out.write_text(json.dumps(s, indent=1, ensure_ascii=False))
    print(f"{len(s)} langkah -> {out}")


if __name__ == "__main__":
    main()
