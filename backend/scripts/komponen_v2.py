"""Komponen INTEK v2 (3 Nov 2026): bahan dashboard, tabel, laporan, dan pesan.

Dipanggil dari build_intek_ds.py -> tambahkan_komponen(add). Semua komponen memakai
auto layout dan properti teks, supaya model AI cukup `library.place` lalu
`instance.setProperties` -- tidak perlu menggambar tabel/badge dari teks berspasi
(penyebab desain "kasar" pada uji 3 Nov: 102 node, 2 instance library).

Komponen (nama dipakai apa adanya di library.place):
  Badge/<Berhasil|Gagal|Sebagian|Dilewati|Info|Netral>   prop: Label
  Chip/Data contoh
  KPI Card                         prop: Label, Nilai, Keterangan
  Table/Header · 3|4|5|6           prop: Kolom 1..n
  Table/Row · 3|4|5|6              prop: Sel 1..n
  Timeline/Item                    prop: Jam, Judul, Detail  (+ slot Badge)
  Sidebar/Item · Aktif|Default     prop: Label
  Banner/<Info|Peringatan|Galat|Sukses>   prop: Judul, Pesan
  Section Header                   prop: Judul, Subjudul
  Tabs · Item Aktif|Default        prop: Label
  Avatar · Inisial                 prop: Inisial
  Progress Bar                     (lebar isi diatur dengan node.set di instance)
  Chat Bubble · Bot                prop: Pesan, Jam
  Empty State                      prop: Judul, Pesan
"""

RED, RED_SOFT, RED_DEEP = "#D3001A", "#FDECEE", "#7E0F12"
TXT, MUTED, PAGE, CARD, BORDER, SUNKEN = "#1C1C1E", "#5F6368", "#F5F5F5", "#FFFFFF", "#DADCE0", "#EDEDED"
SHADOW_S = [{"type": "dropShadow", "color": "#1C1C1E14", "offset": [0, 1], "radius": 3, "spread": 0, "visible": True}]
BAWAH = {"strokeTopWeight": 0, "strokeRightWeight": 0, "strokeLeftWeight": 0}  # garis bawah saja
SHADOW_M = [{"type": "dropShadow", "color": "#1C1C1E1A", "offset": [0, 4], "radius": 16, "spread": 0, "visible": True}]

# Status: (latar, teks, ikon). Kontras teks >= 4.5:1 pada latarnya.
STATUS = {
    "Berhasil": ("#E6F4EA", "#137333", "circle-check"),
    "Gagal":    ("#FCE8E6", "#B42318", "circle-alert"),
    "Sebagian": ("#FEF3C7", "#92400E", "triangle-alert"),
    "Dilewati": ("#EDEDED", "#5F6368", "clock"),
    "Info":     ("#E8F0FE", "#1A56DB", "info"),
    "Netral":   ("#F1F3F4", "#3C4043", "circle"),
}
BANNER = {
    "Info":       ("#E8F0FE", "#1A56DB", "info"),
    "Peringatan": ("#FEF3C7", "#92400E", "triangle-alert"),
    "Galat":      ("#FCE8E6", "#B42318", "circle-alert"),
    "Sukses":     ("#E6F4EA", "#137333", "circle-check"),
}
LEBAR_TABEL = 960   # lebar bawaan baris tabel; di layar diubah ke fill


def tambahkan_komponen(add, icons_dir, text_styles):
    """Tambah halaman "Components v2". `add(cmd, params, as_)` dari build_intek_ds."""
    n = [0]

    def uid(p):
        n[0] += 1
        return f"v2-{p}-{n[0]}"

    def ref(x):
        return {"$ref": x}

    def frame(name, parent=None, x=None, y=None, **props):
        r = uid("f")
        p = {"type": "frame", "name": name, "props": props}
        if parent:
            p["parent"] = ref(parent)
        if x is not None:
            p["x"], p["y"] = x, y
        add("node.create", p, r)
        return r

    def text(parent, chars, style, color=TXT, name=None, **props):
        r = uid("t")
        add("node.create", {"type": "text", "parent": ref(parent), "text": chars, "name": name or chars[:24]}, r)
        fam, sty, size, lh = text_styles[style]
        add("node.set", {"ids": [ref(r)], "props": {"fontFamily": fam, "fontStyle": sty, "fontSize": size,
                                                     "lineHeight": lh, "fill": color, **props}})
        return r

    def icon(parent, name, color, size=16):
        r = uid("ic")
        add("file.import", {"path": str(icons_dir / f"{name}.svg")}, r)
        add("node.reparent", {"ids": [ref(r)], "parent": ref(parent)})
        add("transform.scale", {"ids": [ref(r)], "factor": size / 24})
        add("selection.colors", {"ids": [ref(r)]}, r + "c")
        add("selection.setPaint", {"targets": {"$ref": r + "c", "field": "colors/0/targets"},
                                   "paint": {"type": "solid", "color": color}})
        return r

    def komponen(r, nama, props=()):
        """Jadikan komponen + pasang properti teks. props: [(nama_prop, layer_ref)]."""
        add("node.set", {"ids": [ref(r)], "props": {"name": nama}})
        add("component.create", {"ids": [ref(r)]}, r + "#c")
        for prop, layer in props:
            add("component.addProperty", {"id": ref(r + "#c"), "name": prop, "type": "text", "layer": ref(layer)})
        return r + "#c"

    add("page.add", {"name": "Components v2"}, "v2page")
    add("page.select", {"id": ref("v2page")})
    y = 0
    badge_c = {}

    # ---------- Badge status ----------
    x = 0
    for st, (bg, fg, ic) in STATUS.items():
        b = frame(f"Badge/{st}", None, x, y, layout="horizontal", gap=4, padding=[4, 10, 4, 8], cornerRadius=999,
                  fill=bg, crossAlign="center", sizingH="hug", sizingV="hug")
        icon(b, ic, fg, 14)
        t = text(b, st, "Label/S", fg, "Label")
        badge_c[st] = komponen(b, f"Badge/{st}", [("Label", t)])
        x += 140
    c = frame("Chip/Data contoh", None, x, y, layout="horizontal", padding=[3, 8, 3, 8], cornerRadius=6,
              fill=RED_SOFT, sizingH="hug", sizingV="hug")
    text(c, "Data contoh", "Label/S", RED_DEEP, "Label")
    komponen(c, "Chip/Data contoh")
    y += 60

    # ---------- KPI Card ----------
    k = frame("KPI Card", None, 0, y, layout="vertical", gap=6, padding=20, cornerRadius=12, fill=CARD,
              stroke=BORDER, strokeWeight=1, width=280, sizingH="fixed", sizingV="hug", effects=SHADOW_S)
    t1 = text(k, "Terkirim hari ini", "Label/M", MUTED, "Label")
    t2 = text(k, "59", "Heading/L", TXT, "Nilai")
    t3 = text(k, "atasan menerima brief", "Body/S", MUTED, "Keterangan")
    komponen(k, "KPI Card", [("Label", t1), ("Nilai", t2), ("Keterangan", t3)])

    # ---------- Section Header ----------
    s = frame("Section Header", None, 320, y, layout="vertical", gap=4, width=520, sizingH="fixed", sizingV="hug", fill="none")
    s1 = text(s, "Judul bagian", "Heading/M", TXT, "Judul")
    s2 = text(s, "Keterangan singkat bagian ini", "Body/M", MUTED, "Subjudul")
    komponen(s, "Section Header", [("Judul", s1), ("Subjudul", s2)])

    # ---------- Empty State ----------
    e = frame("Empty State", None, 880, y, layout="vertical", gap=8, padding=32, crossAlign="center", cornerRadius=12,
              fill=PAGE, width=360, sizingH="fixed", sizingV="hug")
    icon(e, "folder", MUTED, 32)
    e1 = text(e, "Belum ada data", "Heading/S", TXT, "Judul")
    e2 = text(e, "Data akan muncul setelah jadwal pertama berjalan.", "Body/S", MUTED, "Pesan", textAlign="center")
    komponen(e, "Empty State", [("Judul", e1), ("Pesan", e2)])
    y += 200

    # ---------- Tabel: header + baris, 3-6 kolom ----------
    for kolom in (3, 4, 5, 6):
        h = frame(f"Table/Header · {kolom}", None, 0, y, layout="horizontal", padding=[10, 16, 10, 16], gap=16,
                  fill=SUNKEN, cornerRadius=[8, 8, 0, 0], width=LEBAR_TABEL, sizingH="fixed", sizingV="hug",
                  crossAlign="center")
        hp = []
        for i in range(kolom):
            cell = frame(f"Kolom {i + 1}", h, layout="horizontal", sizingH="fill", sizingV="hug", fill="none")
            hp.append((f"Kolom {i + 1}", text(cell, f"Kolom {i + 1}".upper(), "Label/S", MUTED, f"Kolom {i + 1}",
                                              textAutoResize="height", sizingH="fill")))
        komponen(h, f"Table/Header · {kolom}", hp)
        r = frame(f"Table/Row · {kolom}", None, 0, y + 40, layout="horizontal", padding=[12, 16, 12, 16], gap=16,
                  fill=CARD, strokeBottomWeight=1, stroke=BORDER, **BAWAH, width=LEBAR_TABEL, sizingH="fixed",
                  sizingV="hug", crossAlign="center")
        rp = []
        for i in range(kolom):
            cell = frame(f"Sel {i + 1}", r, layout="horizontal", sizingH="fill", sizingV="hug", fill="none")
            rp.append((f"Sel {i + 1}", text(cell, f"Isi {i + 1}", "Body/M", TXT, f"Sel {i + 1}",
                                            textAutoResize="height", sizingH="fill")))
        komponen(r, f"Table/Row · {kolom}", rp)
        y += 110

    # ---------- Timeline item ----------
    tl = frame("Timeline/Item", None, 0, y, layout="horizontal", gap=16, padding=[12, 16, 12, 16], crossAlign="center",
               fill=CARD, strokeBottomWeight=1, stroke=BORDER, **BAWAH, width=LEBAR_TABEL, sizingH="fixed", sizingV="hug")
    jam = text(tl, "07:10", "Label/M", MUTED, "Jam")
    titik = frame("Titik", tl, width=10, height=10, cornerRadius=999, fill=RED)
    isi = frame("Isi", tl, layout="vertical", gap=2, sizingH="fill", sizingV="hug", fill="none")
    j1 = text(isi, "Brief pagi disiapkan", "Label/M", TXT, "Judul")
    j2 = text(isi, "59 penerima · 31 detik", "Body/S", MUTED, "Detail")
    bi = uid("badge")
    add("instance.create", {"component": ref(badge_c["Berhasil"]), "parent": ref(tl)}, bi)
    add("node.set", {"ids": [ref(bi)], "props": {"name": "Status"}})
    tc = komponen(tl, "Timeline/Item", [("Jam", jam), ("Judul", j1), ("Detail", j2)])
    # Badge bisa ditukar per baris (Berhasil/Gagal/Sebagian/Dilewati/Info/Netral) + labelnya ikut terbuka.
    add("component.addProperty", {"id": ref(tc), "name": "Status", "type": "instanceSwap", "layer": ref(bi),
                                  "preferred": [ref(c) for c in badge_c.values()]})
    add("component.exposeInstance", {"id": ref(bi)})
    y += 90

    # ---------- Sidebar item ----------
    for i, (keadaan, bg, fg) in enumerate((("Aktif", RED_SOFT, RED), ("Default", "none", TXT))):
        si = frame(f"Sidebar/Item · {keadaan}", None, i * 260, y, layout="horizontal", gap=12, padding=[10, 12, 10, 12],
                   cornerRadius=8, crossAlign="center", fill=bg, width=232, sizingH="fixed", sizingV="hug")
        ii = uid("ikon")
        add("instance.create", {"component": ref("ic-layout-dashboard#c"), "parent": ref(si)}, ii)
        add("transform.scale", {"ids": [ref(ii)], "factor": 18 / 24})
        add("selection.colors", {"ids": [ref(ii)]}, ii + "c")
        add("selection.setPaint", {"targets": {"$ref": ii + "c", "field": "colors/0/targets"},
                                   "paint": {"type": "solid", "color": fg}})
        add("node.set", {"ids": [ref(ii)], "props": {"name": "Ikon"}})
        sl = text(si, "Dashboard", "Label/M", fg, "Label")
        sc = komponen(si, f"Sidebar/Item · {keadaan}", [("Label", sl)])
        add("component.addProperty", {"id": ref(sc), "name": "Ikon", "type": "instanceSwap", "layer": ref(ii)})

    # ---------- Tabs ----------
    for i, (keadaan, garis, fg) in enumerate((("Aktif", RED, TXT), ("Default", None, MUTED))):
        tb = frame(f"Tabs · Item {keadaan}", None, 560 + i * 160, y, layout="horizontal", padding=[10, 4, 10, 4],
                   sizingH="hug", sizingV="hug", fill="none",
                   **({"strokeBottomWeight": 2, "stroke": garis, **BAWAH} if garis else {}))
        tt = text(tb, "Ringkasan", "Label/M", fg, "Label")
        komponen(tb, f"Tabs · Item {keadaan}", [("Label", tt)])

    # ---------- Avatar ----------
    av = frame("Avatar · Inisial", None, 900, y, layout="horizontal", mainAlign="center", crossAlign="center",
               width=36, height=36, cornerRadius=999, fill=RED_SOFT)
    at = text(av, "AB", "Label/M", RED_DEEP, "Inisial")
    komponen(av, "Avatar · Inisial", [("Inisial", at)])
    y += 80

    # ---------- Banner ----------
    for i, (jenis, (bg, fg, ic)) in enumerate(BANNER.items()):
        bn = frame(f"Banner/{jenis}", None, (i % 2) * 500, y + (i // 2) * 90,
                   layout="horizontal", gap=12, padding=16, cornerRadius=10, fill=bg, crossAlign="min",
                   width=460, sizingH="fixed", sizingV="hug")
        icon(bn, ic, fg, 20)
        bi = frame("Isi", bn, layout="vertical", gap=2, sizingH="fill", sizingV="hug", fill="none")
        b1 = text(bi, "Judul pemberitahuan", "Label/M", fg, "Judul")
        b2 = text(bi, "Penjelasan singkat apa yang terjadi dan apa yang perlu dilakukan.", "Body/S", TXT, "Pesan",
                  textAutoResize="height", sizingH="fill")
        komponen(bn, f"Banner/{jenis}", [("Judul", b1), ("Pesan", b2)])
    y += 200

    # ---------- Progress bar ----------
    pb = frame("Progress Bar", None, 0, y, layout="horizontal", width=320, height=8, cornerRadius=999, fill=SUNKEN,
               sizingH="fixed")
    frame("Isi", pb, width=220, height=8, cornerRadius=999, fill=RED)
    komponen(pb, "Progress Bar")

    # ---------- Chat bubble (Telegram) ----------
    cb = frame("Chat Bubble · Bot", None, 400, y, layout="vertical", gap=4, padding=[10, 12, 8, 12],
               cornerRadius=[4, 14, 14, 14], fill=CARD, width=320, sizingH="fixed", sizingV="hug", effects=SHADOW_S)
    c1 = text(cb, "REKAP LAPORAN HARIAN TIM\nKehadiran laporan: 17/19 (89%)", "Body/M", TXT, "Pesan",
              textAutoResize="height", sizingH="fill")
    c2 = text(cb, "19:00", "Label/S", MUTED, "Jam", textAlign="right", sizingH="fill")
    komponen(cb, "Chat Bubble · Bot", [("Pesan", c1), ("Jam", c2)])
    y += 120

    # =========================================================================
    # ---------- Komponen Mobile (iOS / Android Consumer Apps) ---------------
    # =========================================================================

    # 1) Mobile / Status Bar (402 px width)
    msb = frame("Mobile/StatusBar", None, 0, y, layout="horizontal", padding=[12, 20, 10, 20],
                mainAlign="spaceBetween", crossAlign="center", fill="none", width=402, sizingH="fixed", sizingV="hug")
    msb_t = text(msb, "09:41", "Label/M", TXT, "Jam")
    msb_r = frame("Icons", msb, layout="horizontal", gap=6, crossAlign="center", sizingH="hug", sizingV="hug", fill="none")
    icon(msb_r, "chart-column", TXT, 14)
    icon(msb_r, "wallet", TXT, 14)
    komponen(msb, "Mobile/StatusBar", [("Jam", msb_t)])

    # 2) Mobile / Header (Sapaan + Avatar / Action)
    mh = frame("Mobile/Header", None, 440, y, layout="horizontal", padding=[8, 20, 12, 20],
               mainAlign="spaceBetween", crossAlign="center", fill="none", width=402, sizingH="fixed", sizingV="hug")
    mh_left = frame("TitleGroup", mh, layout="vertical", gap=2, sizingH="fill", sizingV="hug", fill="none")
    mh_sapa = text(mh_left, "Halo, Pengelana", "Label/S", MUTED, "Sapaan")
    mh_judul = text(mh_left, "Jelajah Alam", "Heading/M", TXT, "Judul")
    mh_av = frame("AvatarAction", mh, layout="horizontal", mainAlign="center", crossAlign="center",
                  width=38, height=38, cornerRadius=999, fill=RED_SOFT)
    text(mh_av, "AK", "Label/M", RED_DEEP, "Inisial")
    komponen(mh, "Mobile/Header", [("Judul", mh_judul), ("Sapaan", mh_sapa)])
    y += 80

    # 3) Mobile / RatingBadge (★ 4.9)
    rb = frame("Mobile/RatingBadge", None, 0, y, layout="horizontal", gap=4, padding=[3, 8, 3, 8],
               cornerRadius=6, fill="#FEF3C7", crossAlign="center", sizingH="hug", sizingV="hug")
    icon(rb, "star", "#D97706", 12)
    rb_t = text(rb, "4,9", "Label/S", "#92400E", "Nilai")
    komponen(rb, "Mobile/RatingBadge", [("Nilai", rb_t)])

    # 4) Mobile / Pill (Aktif / Default)
    pa = frame("Mobile/Pill · Aktif", None, 140, y, layout="horizontal", padding=[6, 16, 6, 16],
               cornerRadius=999, fill=RED, crossAlign="center", sizingH="hug", sizingV="hug")
    pa_t = text(pa, "Semua Jalur", "Label/M", "#FFFFFF", "Label")
    komponen(pa, "Mobile/Pill · Aktif", [("Label", pa_t)])

    pd = frame("Mobile/Pill · Default", None, 300, y, layout="horizontal", padding=[6, 16, 6, 16],
               cornerRadius=999, fill=CARD, stroke=BORDER, strokeWeight=1, crossAlign="center", sizingH="hug", sizingV="hug")
    pd_t = text(pd, "Hiking", "Label/M", TXT, "Label")
    komponen(pd, "Mobile/Pill · Default", [("Label", pd_t)])
    y += 60

    # 5) Mobile / SearchBar
    ms = frame("Mobile/SearchBar", None, 0, y, layout="horizontal", gap=10, padding=[10, 14, 10, 14],
               cornerRadius=12, fill=SUNKEN, stroke=BORDER, strokeWeight=1, crossAlign="center",
               width=362, sizingH="fixed", sizingV="hug")
    icon(ms, "search", MUTED, 18)
    ms_ph = text(ms, "Cari jalur, gunung, atau lokasi...", "Body/M", MUTED, "Placeholder", sizingH="fill")
    ms_flt = frame("FilterBtn", ms, layout="horizontal", mainAlign="center", crossAlign="center",
                   width=30, height=30, cornerRadius=8, fill=CARD, stroke=BORDER, strokeWeight=1)
    icon(ms_flt, "sliders-horizontal", TXT, 16)
    komponen(ms, "Mobile/SearchBar", [("Placeholder", ms_ph)])
    y += 80

    # 6) Mobile / Card / Featured (Kartu Media 16:9 Unggulan)
    mcf = frame("Mobile/Card/Featured", None, 0, y, layout="vertical", cornerRadius=16, fill=CARD,
                stroke=BORDER, strokeWeight=1, width=362, sizingH="fixed", sizingV="hug", effects=SHADOW_M, clip=True)
    mcf_media = frame("MediaArea", mcf, layout="vertical", mainAlign="spaceBetween", padding=12,
                      width=362, height=160, fill="#1E293B", sizingH="fill")
    mcf_top_row = frame("TopRow", mcf_media, layout="horizontal", mainAlign="spaceBetween", crossAlign="center", sizingH="fill", sizingV="hug", fill="none")
    mcf_tag = frame("Tag", mcf_top_row, layout="horizontal", padding=[4, 10, 4, 10], cornerRadius=999, fill="#0F172A99", sizingH="hug", sizingV="hug")
    text(mcf_tag, "Paling Populer", "Label/S", "#FFFFFF")
    mcf_bm = frame("Bookmark", mcf_top_row, layout="horizontal", mainAlign="center", crossAlign="center",
                   width=32, height=32, cornerRadius=999, fill="#0000004D")
    icon(mcf_bm, "heart", "#FFFFFF", 16)
    mcf_body = frame("Content", mcf, layout="vertical", gap=8, padding=16, sizingH="fill", sizingV="hug", fill="none")
    mcf_r1 = frame("RowTitle", mcf_body, layout="horizontal", mainAlign="spaceBetween", crossAlign="center", sizingH="fill", sizingV="hug", fill="none")
    mcf_title = text(mcf_r1, "Jalur Puncak Pinus", "Heading/S", TXT, "Judul", sizingH="fill")
    mcf_badge = frame("RatingBox", mcf_r1, layout="horizontal", gap=4, padding=[3, 8, 3, 8], cornerRadius=6, fill="#FEF3C7", crossAlign="center", sizingH="hug", sizingV="hug")
    icon(mcf_badge, "star", "#D97706", 12)
    mcf_rate = text(mcf_badge, "4,9", "Label/S", "#92400E", "Rating")
    mcf_r2 = frame("RowMeta", mcf_body, layout="horizontal", gap=12, crossAlign="center", sizingH="fill", sizingV="hug", fill="none")
    icon(mcf_r2, "map-pin", MUTED, 14)
    mcf_loc = text(mcf_r2, "Taman Nasional", "Body/S", MUTED, "Lokasi")
    icon(mcf_r2, "navigation", MUTED, 14)
    mcf_dist = text(mcf_r2, "8,4 km", "Body/S", MUTED, "Jarak")
    icon(mcf_r2, "clock", MUTED, 14)
    mcf_dur = text(mcf_r2, "3j 15m", "Body/S", MUTED, "Durasi")
    komponen(mcf, "Mobile/Card/Featured", [("Judul", mcf_title), ("Lokasi", mcf_loc), ("Jarak", mcf_dist), ("Durasi", mcf_dur), ("Rating", mcf_rate)])

    # 7) Mobile / Card / ListItem (Nearby / List Cell)
    mcl = frame("Mobile/Card/ListItem", None, 400, y, layout="horizontal", padding=12, gap=12, cornerRadius=12,
                fill=CARD, stroke=BORDER, strokeWeight=1, width=362, sizingH="fixed", sizingV="hug", crossAlign="center", effects=SHADOW_S)
    mcl_thumb = frame("Thumbnail", mcl, layout="horizontal", mainAlign="center", crossAlign="center",
                      width=64, height=64, cornerRadius=10, fill=SUNKEN)
    icon(mcl_thumb, "map-pin", MUTED, 24)
    mcl_info = frame("Info", mcl, layout="vertical", gap=3, sizingH="fill", sizingV="hug", fill="none")
    mcl_t = text(mcl_info, "Telaga Sunyi Asri", "Label/M", TXT, "Judul")
    mcl_sub = text(mcl_info, "6,2 km · Tingkat Sedang", "Body/S", MUTED, "Detail")
    mcl_rt = text(mcl_info, "★ 4,8 · Rekomendasi", "Label/S", "#B45309", "Rating")
    icon(mcl, "chevron-right", MUTED, 18)
    komponen(mcl, "Mobile/Card/ListItem", [("Judul", mcl_t), ("Detail", mcl_sub), ("Rating", mcl_rt)])
    y += 280

    # 8) Mobile / BottomNav (4 Menu Utama)
    mbn = frame("Mobile/BottomNav", None, 0, y, layout="horizontal", padding=[10, 16, 14, 16],
                mainAlign="spaceAround", crossAlign="center", fill=CARD, stroke=BORDER,
                strokeTopWeight=1, strokeRightWeight=0, strokeBottomWeight=0, strokeLeftWeight=0,
                width=390, sizingH="fixed", sizingV="hug", effects=SHADOW_M)
    m1 = frame("Nav1", mbn, layout="vertical", gap=3, crossAlign="center", sizingH="hug", sizingV="hug", fill="none")
    icon(m1, "navigation", RED, 20)
    m1_t = text(m1, "Jelajah", "Label/S", RED, "Menu 1")
    m2 = frame("Nav2", mbn, layout="vertical", gap=3, crossAlign="center", sizingH="hug", sizingV="hug", fill="none")
    icon(m2, "heart", MUTED, 20)
    m2_t = text(m2, "Disimpan", "Label/S", MUTED, "Menu 2")
    m3 = frame("Nav3", mbn, layout="vertical", gap=3, crossAlign="center", sizingH="hug", sizingV="hug", fill="none")
    icon(m3, "chart-column", MUTED, 20)
    m3_t = text(m3, "Aktivitas", "Label/S", MUTED, "Menu 3")
    m4 = frame("Nav4", mbn, layout="vertical", gap=3, crossAlign="center", sizingH="hug", sizingV="hug", fill="none")
    icon(m4, "user", MUTED, 20)
    m4_t = text(m4, "Profil", "Label/S", MUTED, "Menu 4")
    komponen(mbn, "Mobile/BottomNav", [("Menu 1", m1_t), ("Menu 2", m2_t), ("Menu 3", m3_t), ("Menu 4", m4_t)])
