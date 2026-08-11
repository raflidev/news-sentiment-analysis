#!/usr/bin/env python3
"""Peta sentimen per lokasi (folium/Leaflet). Agregasi artikel per wilayah,
warna marker = sentimen dominan, ukuran = jumlah artikel."""
from __future__ import annotations

from pathlib import Path

import folium

WARNA = {"negatif": "#cf222e", "netral": "#9a6700", "positif": "#1a7f37"}
LABEL = {"negatif": "Negatif", "netral": "Netral", "positif": "Positif"}


def generate(report: dict, out_path: Path) -> Path:
    """Buat peta HTML dari report (artikel punya lokasi/lat/lon). Kembalikan path."""
    # Agregasi per lokasi
    agg: dict[str, dict] = {}
    for a in report.get("artikel", []):
        nama = (a.get("lokasi") or "").strip()
        if not nama or a.get("lat") is None:
            continue
        key = f"{nama}|{a['lat']}|{a['lon']}"
        g = agg.setdefault(key, {"nama": nama, "lat": a["lat"], "lon": a["lon"],
                                 "negatif": 0, "netral": 0, "positif": 0, "judul": []})
        sent = a.get("sentimen", "netral")
        if sent in g:
            g[sent] += 1
        if len(g["judul"]) < 3 and a.get("judul"):
            g["judul"].append(a["judul"][:90])

    m = folium.Map(location=[-2.5, 118.0], zoom_start=5, tiles="OpenStreetMap",
                   control_scale=True)
    for g in agg.values():
        total = g["negatif"] + g["netral"] + g["positif"]
        dominan = max(("negatif", "netral", "positif"), key=lambda s: g[s])
        warna = WARNA[dominan]
        radius = 7 + min(total * 2.5, 22)
        popup = folium.Popup(
            f"<b>{g['nama']}</b> ({total} artikel)<br/>"
            f"<span style='color:{WARNA['negatif']}'>Negatif {g['negatif']}</span> · "
            f"<span style='color:{WARNA['netral']}'>Netral {g['netral']}</span> · "
            f"<span style='color:{WARNA['positif']}'>Positif {g['positif']}</span>"
            + ("<br/><i>" + "<br/>".join(g["judul"]) + "</i>" if g["judul"] else ""),
            max_width=320,
        )
        folium.CircleMarker(
            location=[g["lat"], g["lon"]],
            radius=radius,
            color=warna,
            weight=1.5,
            fill=True,
            fill_color=warna,
            fill_opacity=0.55,
            popup=popup,
            tooltip=f"{g['nama']} · {total} artikel",
        ).add_to(m)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(out_path))
    return out_path
