#!/usr/bin/env python3
"""
Web UI untuk News Sentiment Analysis (Flask).

Endpoints:
  GET  /                halaman utama (static/index.html)
  POST /api/analyze     {keyword, limit} -> jalankan scrape + analisis, simpan laporan
  GET  /api/reports     daftar laporan tersimpan (metadata)
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

import db as db_mod
import peta as peta_mod
from gazetteer import extract_locations
from main import SentimentAnalyzer, build_report, render_html, scrape_gnews

BASE = Path(__file__).resolve().parent
REPORTS_DIR = BASE / "reports"
app = Flask(__name__, static_folder="static", static_url_path="/static")

db_mod.init_db()

_analyzer: SentimentAnalyzer | None = None


def get_analyzer() -> SentimentAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentAnalyzer()
    return _analyzer


def slugify(kw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", kw.lower()).strip("-")[:40] or "berita"


@app.get("/")
def index():
    return send_from_directory(BASE / "static", "index.html")


@app.get("/api/status")
def status():
    try:
        get_analyzer()
        return jsonify({"status": "ready", "model": "cardiffnlp/twitter-xlm-roberta-base-sentiment"})
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500


@app.post("/api/analyze")
def analyze():
    data = request.get_json(force=True, silent=True) or {}
    keyword = (data.get("keyword") or "").strip()
    if not keyword:
        return jsonify({"error": "Keyword wajib diisi."}), 400
    try:
        limit = max(1, min(int(data.get("limit") or 40), 100))
    except (TypeError, ValueError):
        limit = 40

    t0 = time.time()
    try:
        articles = scrape_gnews(keyword, limit=limit)
    except Exception as e:  # jaringan / RSS bermasalah
        return jsonify({"error": f"Gagal mengambil berita: {e}"}), 502
    if not articles:
        return jsonify({"error": "Tidak ada artikel ditemukan untuk keyword tersebut."}), 404

    analyzer = get_analyzer()
    for a in articles:
        a.sentiment, a.confidence = analyzer.predict(a)
        locs = extract_locations(f"{a.title} {a.snippet}")
        if locs:
            a.lokasi = locs[0]["nama"]
            a.lat = locs[0]["lat"]
            a.lon = locs[0]["lon"]

    report = build_report(articles, keyword, time.time() - t0)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    name = f"{slugify(keyword)}-{stamp}"
    (REPORTS_DIR / f"{name}.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    render_html(report, REPORTS_DIR / f"{name}.html")
    peta_mod.generate(report, REPORTS_DIR / f"{name}-peta.html")
    report["saved"] = f"{name}.json"
    report["map_file"] = f"{name}-peta.html"

    artikel_db = [{
        "judul": a.title, "sumber": a.source, "tanggal": a.published,
        "url": a.link, "snippet": a.snippet, "sentimen": a.sentiment,
        "confidence": a.confidence, "lokasi": a.lokasi, "lat": a.lat, "lon": a.lon,
    } for a in articles]
    report_id = db_mod.save_report(report, artikel_db)
    report["id"] = report_id

    return jsonify(report)


@app.get("/api/reports")
def list_reports():
    return jsonify(db_mod.list_reports())


@app.get("/api/reports/<int:rid>")
def get_report(rid: int):
    rep = db_mod.get_report(rid)
    if rep is None:
        return jsonify({"error": "Laporan tidak ditemukan."}), 404
    return jsonify(rep)


@app.get("/peta/<path:name>")
def serve_map(name: str):
    safe = Path(name).name
    p = REPORTS_DIR / safe
    if not p.exists() or not safe.endswith(".html"):
        return jsonify({"error": "Peta tidak ditemukan."}), 404
    return send_from_directory(REPORTS_DIR, safe)


if __name__ == "__main__":
    print("News Sentiment Analysis web: http://localhost:8003")
    app.run(host="0.0.0.0", port=8003, threaded=True)
