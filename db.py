#!/usr/bin/env python3
"""Database PostgreSQL untuk laporan & artikel sentimen berita.

Skema (anti-duplikat):
  - reports:      satu baris per analisis; UNIQUE (keyword, scraped_at)
  - articles:     artikel kanonik per URL; UNIQUE (url) -> artikel yang sama
                  tidak pernah tersimpan dua kali, lintas laporan sekalipun
  - report_articles: join laporan <-> artikel + hasil analisis per laporan;
                  UNIQUE (report_id, article_id)
"""
from __future__ import annotations

import os
from typing import Any

import psycopg2
import psycopg2.extras

DB_DSN = os.environ.get(
    "NEWS_SENTIMENT_DSN",
    "host=127.0.0.1 port=5432 dbname=news_sentiment user=minofa password=minofa123",
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    id          SERIAL PRIMARY KEY,
    keyword     TEXT NOT NULL,
    scraped_at  TIMESTAMPTZ NOT NULL,
    total       INTEGER NOT NULL,
    negatif     INTEGER NOT NULL DEFAULT 0,
    netral      INTEGER NOT NULL DEFAULT 0,
    positif     INTEGER NOT NULL DEFAULT 0,
    durasi      REAL,
    json_file   TEXT,
    map_file    TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_reports_keyword_scraped UNIQUE (keyword, scraped_at)
);

CREATE TABLE IF NOT EXISTS articles (
    id          SERIAL PRIMARY KEY,
    url         TEXT NOT NULL,
    judul       TEXT,
    sumber      TEXT,
    tanggal     TEXT,
    snippet     TEXT,
    CONSTRAINT uq_articles_url UNIQUE (url)
);

CREATE TABLE IF NOT EXISTS report_articles (
    report_id   INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    article_id  INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    sentimen    TEXT,
    confidence  REAL,
    lokasi      TEXT,
    lat         DOUBLE PRECISION,
    lon         DOUBLE PRECISION,
    PRIMARY KEY (report_id, article_id)
);

CREATE INDEX IF NOT EXISTS idx_report_articles_report ON report_articles(report_id);
CREATE INDEX IF NOT EXISTS idx_report_articles_article ON report_articles(article_id);
"""

# Migrasi skema lama (articles berisi report_id + url tanpa unique)
# -> pisah ke articles (url unique) + report_articles.
MIGRATE_LEGACY = """
DO $$
BEGIN
    DROP TABLE IF EXISTS report_articles;
    DROP TABLE IF EXISTS articles_new;
    CREATE TABLE articles_new (
        id      SERIAL PRIMARY KEY,
        url     TEXT NOT NULL,
        judul   TEXT,
        sumber  TEXT,
        tanggal TEXT,
        snippet TEXT,
        CONSTRAINT uq_articles_url UNIQUE (url)
    );
    INSERT INTO articles_new (url, judul, sumber, tanggal, snippet)
    SELECT DISTINCT ON (url) url, judul, sumber, tanggal, snippet
    FROM articles WHERE url IS NOT NULL ORDER BY url, id;

    CREATE TABLE report_articles (
        report_id   INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
        article_id  INTEGER NOT NULL REFERENCES articles_new(id) ON DELETE CASCADE,
        sentimen    TEXT,
        confidence  REAL,
        lokasi      TEXT,
        lat         DOUBLE PRECISION,
        lon         DOUBLE PRECISION,
        PRIMARY KEY (report_id, article_id)
    );
    INSERT INTO report_articles (report_id, article_id, sentimen, confidence, lokasi, lat, lon)
    SELECT a.report_id, n.id, a.sentimen, a.confidence, a.lokasi, a.lat, a.lon
    FROM articles a JOIN articles_new n ON n.url = a.url;

    DROP TABLE articles;
    ALTER TABLE articles_new RENAME TO articles;
    CREATE INDEX idx_report_articles_report ON report_articles(report_id);
    CREATE INDEX idx_report_articles_article ON report_articles(article_id);
END $$;
"""


def connect():
    return psycopg2.connect(DB_DSN)


def init_db() -> None:
    with connect() as conn:
        with conn.cursor() as cur:
            # Deteksi skema lama: articles masih punya kolom report_id (belum unique)
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'articles' AND column_name = 'report_id'",
            )
            legacy = cur.fetchone() is not None
            if legacy:
                cur.execute(MIGRATE_LEGACY)
            cur.execute(SCHEMA)
            # CREATE TABLE IF NOT EXISTS tidak menambah constraint di tabel lama;
            # pastikan constraint unique reports ada (idempotent).
            cur.execute(
                """DO $$
                   BEGIN
                       IF NOT EXISTS (SELECT 1 FROM pg_constraint
                                      WHERE conname = 'uq_reports_keyword_scraped') THEN
                           ALTER TABLE reports
                               ADD CONSTRAINT uq_reports_keyword_scraped UNIQUE (keyword, scraped_at);
                       END IF;
                   END $$;"""
            )
        conn.commit()


def save_report(report: dict, articles: list[dict]) -> int:
    """Simpan report + artikel (upsert by url, link via report_articles).
    Artikel dengan url yang sudah ada TIDAK diduplikasi. Kembalikan report_id."""
    r = report["ringkasan"]
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO reports (keyword, scraped_at, total, negatif, netral, positif, durasi, json_file, map_file)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (keyword, scraped_at) DO UPDATE SET map_file = EXCLUDED.map_file
                   RETURNING id""",
                (
                    report["keyword"],
                    report["scraped_at"],
                    report["total_artikel"],
                    r["negatif"]["jumlah"],
                    r["netral"]["jumlah"],
                    r["positif"]["jumlah"],
                    report.get("durasi_detik"),
                    report.get("saved"),
                    report.get("map_file"),
                ),
            )
            report_id = cur.fetchone()[0]
            for a in articles:
                url = (a.get("url") or "").strip()
                if not url:
                    continue
                cur.execute(
                    """INSERT INTO articles (url, judul, sumber, tanggal, snippet)
                       VALUES (%s, %s, %s, %s, %s)
                       ON CONFLICT (url) DO UPDATE SET
                           judul = EXCLUDED.judul,
                           sumber = EXCLUDED.sumber
                       RETURNING id""",
                    (url, a.get("judul"), a.get("sumber"), a.get("tanggal"), a.get("snippet")),
                )
                article_id = cur.fetchone()[0]
                cur.execute(
                    """INSERT INTO report_articles (report_id, article_id, sentimen, confidence, lokasi, lat, lon)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (report_id, article_id) DO NOTHING""",
                    (
                        report_id, article_id, a.get("sentimen"), a.get("confidence"),
                        a.get("lokasi"), a.get("lat"), a.get("lon"),
                    ),
                )
        conn.commit()
    return report_id


def list_reports(limit: int = 20) -> list[dict]:
    with connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """SELECT id, keyword, scraped_at, total, negatif, netral, positif, map_file
                   FROM reports ORDER BY scraped_at DESC LIMIT %s""",
                (limit,),
            )
            rows = cur.fetchall()
    out = []
    for r in rows:
        out.append({
            "id": r["id"],
            "keyword": r["keyword"],
            "scraped_at": r["scraped_at"].isoformat() if r["scraped_at"] else None,
            "total": r["total"],
            "map_file": r["map_file"],
            "ringkasan": {
                "negatif": {"jumlah": r["negatif"]},
                "netral": {"jumlah": r["netral"]},
                "positif": {"jumlah": r["positif"]},
            },
        })
    return out


def get_report(report_id: int) -> dict | None:
    with connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM reports WHERE id = %s", (report_id,))
            rep = cur.fetchone()
            if not rep:
                return None
            cur.execute(
                """SELECT a.judul, a.sumber, a.tanggal, a.url, ra.sentimen, ra.confidence,
                          ra.lokasi, ra.lat, ra.lon
                   FROM report_articles ra
                   JOIN articles a ON a.id = ra.article_id
                   WHERE ra.report_id = %s ORDER BY ra.article_id""",
                (report_id,),
            )
            arts = cur.fetchall()
    total = rep["total"] or 1
    return {
        "id": rep["id"],
        "keyword": rep["keyword"],
        "scraped_at": rep["scraped_at"].isoformat() if rep["scraped_at"] else None,
        "total_artikel": rep["total"],
        "map_file": rep["map_file"],
        "ringkasan": {
            s: {"jumlah": rep[s], "persen": round(100 * rep[s] / total, 1)}
            for s in ("negatif", "netral", "positif")
        },
        "artikel": [
            {
                "judul": a["judul"], "sumber": a["sumber"], "tanggal": a["tanggal"],
                "url": a["url"], "sentimen": a["sentimen"], "confidence": a["confidence"],
                "lokasi": a["lokasi"], "lat": a["lat"], "lon": a["lon"],
            }
            for a in arts
        ],
    }
