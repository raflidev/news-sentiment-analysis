#!/usr/bin/env python3
"""
Wrapper cron: jalankan analisis sentimen untuk semua keyword di keywords.txt,
lalu cetak ringkasan siap-Telegram (stdout = pesan yang dikirim).

Keyword tambahan: tulis satu per baris di keywords.txt.
Keyword khusus sekali jalan: ./run_sentimen.py "keyword bebas"
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
VENV_PY = BASE / "venv" / "bin" / "python"
KEYWORDS_FILE = BASE / "keywords.txt"
LIMIT = 40

EMOJI = {"negatif": "\U0001f534", "netral": "\U0001f7e1", "positif": "\U0001f7e2"}


def slug(kw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", kw.lower()).strip("-")[:40] or "berita"


def run_keyword(kw: str, limit: int) -> dict | None:
    subprocess.run(
        [str(VENV_PY), str(BASE / "main.py"), kw, "--limit", str(limit), "--out", str(BASE / "reports")],
        capture_output=True, text=True, timeout=600,
    )
    jsons = sorted((BASE / "reports").glob(f"{slug(kw)}-*.json"))
    if not jsons:
        return None
    return json.loads(jsons[-1].read_text(encoding="utf-8"))


def fmt_article(a: dict) -> str:
    return f"- [{a['sumber']}] {a['judul']} ({a['confidence']:.0%})"


def main() -> int:
    if len(sys.argv) > 1:
        keywords = [sys.argv[1]]
    else:
        keywords = [k.strip() for k in KEYWORDS_FILE.read_text(encoding="utf-8").splitlines() if k.strip()]
        if not keywords:
            keywords = ["ekonomi indonesia"]

    blocks = []
    for kw in keywords:
        report = run_keyword(kw, LIMIT)
        if not report:
            blocks.append(f"*{kw}*: gagal mengambil berita.")
            continue
        r = report["ringkasan"]
        n = r["negatif"]["jumlah"]
        net = r["netral"]["jumlah"]
        p = r["positif"]["jumlah"]
        artikel = sorted(report["artikel"], key=lambda a: a["confidence"], reverse=True)
        neg = [a for a in artikel if a["sentimen"] == "negatif"][:3]
        pos = [a for a in artikel if a["sentimen"] == "positif"][:3]
        lines = [
            f'📰 *SENTIMEN BERITA: "{report["keyword"]}"*',
            f'{report["total_artikel"]} artikel · {report["scraped_at"][:16].replace("T", " ")} UTC',
            "",
            f'{EMOJI["negatif"]} Negatif {r["negatif"]["persen"]:.0f}% ({n})',
            f'{EMOJI["netral"]} Netral {r["netral"]["persen"]:.0f}% ({net})',
            f'{EMOJI["positif"]} Positif {r["positif"]["persen"]:.0f}% ({p})',
        ]
        if neg:
            lines += ["", "*Paling negatif:*"] + [fmt_article(a) for a in neg]
        if pos:
            lines += ["", "*Paling positif:*"] + [fmt_article(a) for a in pos]
        blocks.append("\n".join(lines))

    print("\n\n".join(blocks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
