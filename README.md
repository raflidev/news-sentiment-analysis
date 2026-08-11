# News Sentiment Analysis (Indonesia)

Scraping berita Indonesia per keyword (Google News RSS) + analisis sentimen
(positif / netral / negatif) dengan model transformer Bahasa Indonesia
[`w11wo/indonesian-roberta-base-sentiment-classifier`](https://huggingface.co/w11wo/indonesian-roberta-base-sentiment-classifier).

## Setup

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt        # torch CPU: pip install torch --index-url https://download.pytorch.org/whl/cpu
```

Model (~500 MB) otomatis diunduh dari HuggingFace saat pertama kali dijalankan.

## Pemakaian

```bash
python main.py "inflasi"                 # keyword bebas
python main.py "ekonomi indonesia" --limit 80
```

Output:

- ringkasan + daftar artikel berwarna di konsol
- `reports/<keyword>-<timestamp>.json` — data lengkap
- `reports/<keyword>-<timestamp>.html` — laporan mandiri (statistik + tabel artikel)
- `reports/<keyword>-<timestamp>-peta.html` — peta sentimen per lokasi (folium/Leaflet)
- semua laporan & artikel tersimpan di **PostgreSQL** (`news_sentiment`, lihat `db.py`)

## Web UI

```bash
./venv/bin/python app.py   # http://localhost:8003
```

Halaman web: analisis per keyword, statistik + bar distribusi, peta sentimen
interaktif, tabel artikel dengan lokasi, dan riwayat laporan (dari database).

## Monitoring otomatis (cron/Telegram)

`run_sentimen.py` membaca keyword dari `keywords.txt`, menjalankan analisis,
dan mencetak ringkasan siap-Telegram (dipakai oleh cron job Hermes harian).

## Anti-duplikat

- `articles.url` UNIQUE global: artikel yang sama tidak pernah tersimpan dua kali
- `reports` UNIQUE(keyword, scraped_at): tidak ada report ganda
- `report_articles` PK(report_id, article_id): link laporan-artikel unik
- migrasi otomatis dari skema lama saat `init_db()`

## Cara kerja

1. `scrape_gnews()` — ambil RSS Google News dengan `hl=id&gl=ID`, dedupe judul.
2. `SentimentAnalyzer` — pipeline `transformers`, klasifikasi 3 kelas per judul+snippet.
3. Laporan JSON/HTML + statistik distribusi.
