#!/usr/bin/env python3
"""
Sentimen Berita Indonesia — scraping berita per keyword + analisis sentimen NLP.

Alur:
  1. Scrape berita dari Google News RSS (hl=id, gl=ID) berdasarkan keyword.
  2. Analisis sentimen tiap judul/artikel dengan model transformer Bahasa
     Indonesia (w11wo/indonesian-roberta-base-sentiment-classifier).
  3. Output: ringkasan konsol, JSON lengkap, dan laporan HTML.

Pemakaian:
  python main.py "inflasi"
  python main.py "ekonomi indonesia" --limit 80 --out reports
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests

GNEWS_RSS = "https://news.google.com/rss/search"

MODEL_NAME = "cardiffnlp/twitter-xlm-roberta-base-sentiment"

SENTIMEN_ID = {"positif": "Positif", "netral": "Netral", "negatif": "Negatif"}
ORDER = ["negatif", "netral", "positif"]

# Normalisasi label dari model (Inggris: positive/neutral/negative) ke kunci Indonesia.
LABEL_MAP = {
    "positif": "positif", "positive": "positif", "pos": "positif",
    "netral": "netral", "neutral": "netral",
    "negatif": "negatif", "negative": "negatif", "neg": "negatif",
}

ANSI = {
    "positif": "\033[32m",   # hijau
    "netral": "\033[33m",    # kuning
    "negatif": "\033[31m",   # merah
    "reset": "\033[0m",
    "dim": "\033[2m",
    "bold": "\033[1m",
}


@dataclass
class Article:
    title: str
    source: str
    published: str
    link: str
    snippet: str = ""
    sentiment: str = ""          # positif / netral / negatif
    confidence: float = 0.0
    key: str = field(default="")


def scrape_gnews(keyword: str, limit: int = 60) -> list[Article]:
    """Ambil berita Indonesia dari Google News RSS untuk keyword tertentu."""
    params = {
        "q": keyword,
        "hl": "id",
        "gl": "ID",
        "ceid": "ID:id",
    }
    r = requests.get(GNEWS_RSS, params=params, timeout=30,
                     headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})
    r.raise_for_status()
    feed = feedparser.parse(r.content)

    articles: list[Article] = []
    seen: set[str] = set()
    for entry in feed.entries:
        title = html.unescape(entry.get("title", "")).strip()
        if not title:
            continue
        key = re.sub(r"\s+", " ", title.lower())
        if key in seen:
            continue
        seen.add(key)
        # buang judul berita bayangan (Google News "..." entries) minimal 2 kata
        snippet = html.unescape(entry.get("summary", "") or "")
        snippet = re.sub(r"<[^>]+>", " ", snippet).strip()
        articles.append(Article(
            title=title,
            source=entry.get("source", {}).get("title", "—"),
            published=entry.get("published", ""),
            link=entry.get("link", ""),
            snippet=snippet,
            key=hashlib.md5(key.encode()).hexdigest()[:10],
        ))
        if len(articles) >= limit:
            break
    return articles


class SentimentAnalyzer:
    """Wrapper pipeline transformers untuk sentimen Bahasa Indonesia."""

    def __init__(self) -> None:
        from transformers import pipeline  # import lambat: model besar

        print("Memuat model sentimen Indonesia...", file=sys.stderr, flush=True)
        t0 = time.time()
        self.pipe = pipeline(
            "sentiment-analysis",
            model=MODEL_NAME,
            tokenizer=MODEL_NAME,
            truncation=True,
            max_length=128,
            device=-1,  # CPU
        )
        print(f"Model siap ({time.time() - t0:.1f}s).", file=sys.stderr, flush=True)

    def predict(self, article: Article) -> tuple[str, float]:
        text = article.title
        if article.snippet:
            text = f"{article.title}. {article.snippet}"
        out = self.pipe(text)[0]
        label = str(out["label"]).strip().lower()
        label = label.split("_")[-1]  # "LABEL_1_positif" -> "positif"
        label = LABEL_MAP.get(label, label)
        return label, float(out["score"])


def build_report(articles: list[Article], keyword: str, elapsed: float) -> dict:
    counts = {s: sum(1 for a in articles if a.sentiment == s) for s in ORDER}
    total = len(articles)
    return {
        "keyword": keyword,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "total_artikel": total,
        "durasi_detik": round(elapsed, 2),
        "ringkasan": {
            s: {"jumlah": counts[s], "persen": round(100 * counts[s] / total, 1) if total else 0}
            for s in ORDER
        },
        "artikel": [
            {
                "judul": a.title,
                "sumber": a.source,
                "tanggal": a.published,
                "url": a.link,
                "sentimen": a.sentiment,
                "confidence": round(a.confidence, 4),
            }
            for a in articles
        ],
    }


def print_console(report: dict) -> None:
    kw = report["keyword"]
    total = report["total_artikel"]
    print(f"\n{ANSI['bold']}SENTIMEN BERITA: \"{kw}\"{ANSI['reset']}  ({total} artikel, {report['durasi_detik']}s)")
    print("─" * 72)
    for s in ORDER:
        d = report["ringkasan"][s]
        bar = "█" * round(d["persen"] / 2)
        print(f"  {ANSI[s]}{SENTIMEN_ID[s]:<8}{ANSI['reset']} {d['persen']:>5.1f}%  ({d['jumlah']:>3} artikel)  {ANSI['dim']}{bar}{ANSI['reset']}")
    print("─" * 72)
    for i, a in enumerate(report["artikel"], 1):
        c = a["confidence"]
        print(f"{ANSI[a['sentimen']]}{SENTIMEN_ID[a['sentimen']][:1]}{ANSI['reset']} "
              f"{i:>2}. [{a['sumber']}] {a['judul'][:80]} {ANSI['dim']}({c:.2f}){ANSI['reset']}")
    print()


def render_html(report: dict, out_path: Path) -> None:
    """Laporan HTML mandiri, desain bersih (tanpa emoji/gradien)."""
    counts = report["ringkasan"]
    rows = ""
    for i, a in enumerate(report["artikel"], 1):
        s = a["sentimen"]
        dot = {"positif": "#1a7f37", "netral": "#9a6700", "negatif": "#cf222e"}[s]
        rows += f"""
        <tr>
          <td class="num">{i}</td>
          <td><a href="{a['url']}" target="_blank" rel="noreferrer">{a['judul']}</a>
              <div class="src">{a['sumber']} · {a['tanggal']}</div></td>
          <td class="cell-sent"><span class="chip" style="--c:{dot}">{SENTIMEN_ID[s]}</span></td>
          <td class="conf">{a['confidence']:.0%}</td>
        </tr>"""
    bars = ""
    for s in ORDER:
        d = counts[s]
        bars += f"""
        <div class="bar-row">
          <span class="lbl" style="color:{'#1a7f37' if s=='positif' else '#9a6700' if s=='netral' else '#cf222e'}">{SENTIMEN_ID[s]}</span>
          <div class="track"><div class="fill" style="width:{d['persen']}%;background:{'#1a7f37' if s=='positif' else '#9a6700' if s=='netral' else '#cf222e'}"></div></div>
          <span class="pct">{d['persen']}% <em>({d['jumlah']})</em></span>
        </div>"""

    html_doc = f"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Sentimen Berita: {report['keyword']}</title>
<style>
  :root {{ --ink:#24313d; --dim:#55636f; --faint:#8a97a3; --bg:#fbfaf7; --surface:#fff;
           --hairline:#e4e0d6; --accent:#175e7d; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
         font-family:-apple-system,'Segoe UI',Roboto,'Helvetica Neue',sans-serif; line-height:1.6; }}
  .wrap {{ max-width:860px; margin:0 auto; padding:48px 24px 72px; }}
  .kicker {{ font-size:11px; letter-spacing:.2em; text-transform:uppercase; color:var(--accent); margin:0 0 10px; }}
  h1 {{ font-family:Georgia,'Times New Roman',serif; font-size:32px; font-weight:600; margin:0 0 6px; }}
  .sub {{ color:var(--dim); margin:0 0 28px; font-size:15px; }}
  .stats {{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-bottom:24px; }}
  .stat {{ border:1px solid var(--hairline); background:var(--surface); padding:16px; }}
  .stat b {{ font-size:30px; font-weight:700; display:block; line-height:1.1; }}
  .stat span {{ font-size:12px; color:var(--dim); text-transform:uppercase; letter-spacing:.1em; }}
  .panel {{ border:1px solid var(--hairline); background:var(--surface); padding:22px; margin-bottom:24px; }}
  .panel h2 {{ font-family:Georgia,serif; font-size:18px; margin:0 0 14px; }}
  .bar-row {{ display:grid; grid-template-columns:90px 1fr 110px; align-items:center; gap:12px; margin-bottom:10px; }}
  .lbl {{ font-weight:600; font-size:13px; }}
  .track {{ height:10px; background:#f0ede6; }}
  .fill {{ height:100%; }}
  .pct {{ font-size:12px; color:var(--dim); text-align:right; }} .pct em {{ color:var(--faint); }}
  table {{ width:100%; border-collapse:collapse; font-size:13.5px; }}
  th {{ text-align:left; font-size:11px; text-transform:uppercase; letter-spacing:.12em;
        color:var(--faint); border-bottom:1px solid var(--hairline); padding:8px 10px; }}
  td {{ border-bottom:1px solid var(--hairline); padding:10px; vertical-align:top; }}
  td.num {{ color:var(--faint); width:32px; }}
  td a {{ color:var(--ink); text-decoration:none; font-weight:500; }}
  td a:hover {{ color:var(--accent); text-decoration:underline; }}
  .src {{ color:var(--faint); font-size:12px; margin-top:2px; }}
  .cell-sent {{ width:88px; }}
  .chip {{ display:inline-block; font-size:11px; font-weight:600; letter-spacing:.06em;
           color:var(--c); border:1px solid color-mix(in srgb, var(--c) 45%, transparent);
           background:color-mix(in srgb, var(--c) 9%, white); padding:2px 10px; border-radius:4px; }}
  .conf {{ width:60px; color:var(--dim); font-variant-numeric:tabular-nums; }}
  .foot {{ margin-top:28px; color:var(--faint); font-size:12px; }}
</style>
</head>
<body>
<div class="wrap">
  <p class="kicker">Sentimen Analisis · Berita Indonesia</p>
  <h1>Sentimen: "{report['keyword']}"</h1>
  <p class="sub">{report['total_artikel']} artikel · scrapped {report['scraped_at'][:16].replace('T', ' ')} UTC · model RoBERTa Bahasa Indonesia</p>

  <div class="stats">
    <div class="stat"><b style="color:#cf222e">{counts['negatif']['jumlah']}</b><span>Negatif ({counts['negatif']['persen']}%)</span></div>
    <div class="stat"><b style="color:#9a6700">{counts['netral']['jumlah']}</b><span>Netral ({counts['netral']['persen']}%)</span></div>
    <div class="stat"><b style="color:#1a7f37">{counts['positif']['jumlah']}</b><span>Positif ({counts['positif']['persen']}%)</span></div>
  </div>

  <div class="panel"><h2>Distribusi sentimen</h2>{bars}</div>

  <div class="panel"><h2>Artikel</h2>
    <table><thead><tr><th></th><th>Judul</th><th>Sentimen</th><th>Keyakinan</th></tr></thead>
    <tbody>{rows}</tbody></table>
  </div>

  <p class="foot">Dihasilkan otomatis oleh sentimen-berita · hasil bersifat indikatif, bukan penilaian editorial.</p>
</div>
</body>
</html>"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_doc, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Sentimen analisis berita Indonesia per keyword")
    ap.add_argument("keyword", nargs="?", default="ekonomi indonesia", help="keyword pencarian berita")
    ap.add_argument("--limit", type=int, default=60, help="jumlah artikel maksimal (default 60)")
    ap.add_argument("--out", default="reports", help="direktori output (default reports)")
    args = ap.parse_args()

    t0 = time.time()
    print(f"Scraping berita untuk keyword: \"{args.keyword}\" ...")
    articles = scrape_gnews(args.keyword, limit=args.limit)
    if not articles:
        print("Tidak ada artikel ditemukan.", file=sys.stderr)
        return 1
    print(f"  {len(articles)} artikel berhasil diambil.")

    analyzer = SentimentAnalyzer()
    for a in articles:
        a.sentiment, a.confidence = analyzer.predict(a)

    report = build_report(articles, args.keyword, time.time() - t0)
    print_console(report)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = re.sub(r"[^a-z0-9]+", "-", args.keyword.lower()).strip("-")[:40] or "berita"
    json_path = out_dir / f"{slug}-{stamp}.json"
    html_path = out_dir / f"{slug}-{stamp}.html"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    render_html(report, html_path)
    print(f"Laporan tersimpan: {json_path}")
    print(f"                  {html_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
