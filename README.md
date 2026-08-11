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

## Cara kerja

1. `scrape_gnews()` — ambil RSS Google News dengan `hl=id&gl=ID`, dedupe judul.
2. `SentimentAnalyzer` — pipeline `transformers`, klasifikasi 3 kelas per judul+snippet.
3. Laporan JSON/HTML + statistik distribusi.
