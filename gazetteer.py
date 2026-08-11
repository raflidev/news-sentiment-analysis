#!/usr/bin/env python3
"""Gazetteer lokasi Indonesia (provinsi, kota besar, sebutan umum) untuk
ekstraksi lokasi dari teks berita. Format: (nama, lat, lon)."""

# 38 provinsi + ibu kota (nama provinsi, ibu kota, sebutan umum)
LOCATIONS = [
    # Aceh
    ("Aceh", 5.5483, 95.3238), ("Banda Aceh", 5.5483, 95.3238), ("Sabang", 5.8933, 95.3197),
    ("Lhokseumawe", 5.1801, 97.1507), ("Langsa", 4.4683, 97.9683),
    # Sumatera Utara
    ("Sumatera Utara", 3.5952, 98.6722), ("Sumut", 3.5952, 98.6722), ("Medan", 3.5952, 98.6722),
    ("Binjai", 3.6000, 98.4850), ("Pematangsiantar", 2.9600, 99.0600), ("Tebing Tinggi", 3.3285, 99.1625),
    ("Sibolga", 1.7400, 98.7811), ("Padang Sidempuan", 1.3794, 99.2714), ("Gunungsitoli", 1.2833, 97.6167),
    ("Tanjung Balai", 2.9667, 99.8000), ("Danau Toba", 2.6840, 98.8750), ("Toba", 2.6840, 98.8750),
    # Sumatera Barat
    ("Sumatera Barat", -0.9471, 100.4172), ("Sumbar", -0.9471, 100.4172), ("Padang", -0.9471, 100.4172),
    ("Bukittinggi", -0.3056, 100.3696), ("Payakumbuh", -0.2260, 100.6320), ("Solok", -0.8000, 100.6530),
    ("Pariaman", -0.6229, 100.1205), ("Sawahlunto", -0.6814, 100.7768),
    # Riau
    ("Riau", 0.5071, 101.4478), ("Pekanbaru", 0.5071, 101.4478), ("Dumai", 1.6667, 101.4500),
    ("Siak", 0.8000, 102.0000), ("Pelalawan", 0.2083, 102.1778), ("Rokan Hulu", 0.8780, 100.4700),
    # Kepulauan Riau
    ("Kepulauan Riau", 0.9184, 104.4577), ("Kepri", 0.9184, 104.4577), ("Tanjungpinang", 0.9184, 104.4577),
    ("Batam", 1.0456, 104.0305), ("Tanjung Balai Karimun", 0.9786, 103.4297),
    # Jambi
    ("Jambi", -1.5900, 103.6132), ("Kota Jambi", -1.5900, 103.6132), ("Sungaipenuh", -2.0630, 101.3930),
    # Sumatera Selatan
    ("Sumatera Selatan", -2.9761, 104.7754), ("Sumsel", -2.9761, 104.7754), ("Palembang", -2.9761, 104.7754),
    ("Prabumulih", -3.4320, 104.2350), ("Lubuklinggau", -3.2967, 102.8617), ("Pagar Alam", -4.0250, 103.2500),
    ("Kayuagung", -3.3860, 104.8350), ("Baturaja", -4.1300, 104.1670),
    # Bangka Belitung
    ("Bangka Belitung", -2.1290, 106.1136), ("Babel", -2.1290, 106.1136), ("Pangkalpinang", -2.1290, 106.1136),
    ("Belitung", -2.8686, 107.9850), ("Tanjung Pandan", -2.7500, 107.6500),
    # Bengkulu
    ("Bengkulu", -3.8004, 102.2656), ("Kota Bengkulu", -3.8004, 102.2656),
    # Lampung
    ("Lampung", -5.4500, 105.2670), ("Bandar Lampung", -5.4500, 105.2670), ("Metro", -5.1167, 105.3000),
    ("Lampung Selatan", -5.5300, 105.5200),
    # DKI Jakarta
    ("DKI Jakarta", -6.2088, 106.8456), ("Jakarta", -6.2088, 106.8456), ("DKI", -6.2088, 106.8456),
    ("Kepulauan Seribu", -5.6333, 106.5833),
    # Jawa Barat
    ("Jawa Barat", -6.9175, 107.6191), ("Jabar", -6.9175, 107.6191), ("Bandung", -6.9175, 107.6191),
    ("Bogor", -6.5971, 106.8060), ("Bekasi", -6.2383, 106.9756), ("Depok", -6.4025, 106.7942),
    ("Tangerang", -6.1783, 106.6319), ("Cilegon", -6.0036, 106.0111), ("Sukabumi", -6.9181, 106.9267),
    ("Cianjur", -6.8205, 107.1394), ("Garut", -7.2279, 107.9087), ("Tasikmalaya", -7.3274, 108.2207),
    ("Cimahi", -6.8723, 107.5425), ("Cirebon", -6.7320, 108.5523), ("Indramayu", -6.3264, 108.3244),
    ("Karawang", -6.3227, 107.2952), ("Purwakarta", -6.5570, 107.4430), ("Subang", -6.5695, 107.7597),
    ("Sumedang", -6.8582, 107.9200), ("Majalengka", -6.8360, 108.2270), ("Kuningan", -6.9780, 108.4830),
    ("Banjar", -7.3690, 108.5320), ("Pangandaran", -7.6667, 108.6450), ("Cikarang", -6.2608, 107.1569),
    # Banten
    ("Banten", -6.1204, 106.1503), ("Serang", -6.1204, 106.1503), ("Tangerang Selatan", -6.2886, 106.7177),
    ("Tangsel", -6.2886, 106.7177), ("Pandeglang", -6.3084, 106.1066), ("Lebak", -6.5640, 106.2520),
    # Jawa Tengah
    ("Jawa Tengah", -6.9667, 110.4167), ("Jateng", -6.9667, 110.4167), ("Semarang", -6.9667, 110.4167),
    ("Magelang", -7.4706, 110.2202), ("Salatiga", -7.3305, 110.5082), ("Surakarta", -7.5755, 110.8243),
    ("Solo", -7.5755, 110.8243), ("Pekalongan", -6.8886, 109.6753), ("Tegal", -6.8694, 109.1402),
    ("Kudus", -6.8048, 110.8405), ("Pati", -6.7549, 111.0350), ("Purwokerto", -7.4214, 109.2344),
    ("Cilacap", -7.7178, 109.0154), ("Kebumen", -7.6774, 109.6690), ("Purworejo", -7.7134, 110.0080),
    ("Wonosobo", -7.3618, 109.9030), ("Temanggung", -7.3160, 110.1740), ("Klaten", -7.7059, 110.6065),
    ("Boyolali", -7.5320, 110.5950), ("Sragen", -7.4310, 111.0220), ("Blora", -6.9700, 111.4190),
    ("Rembang", -6.7040, 111.3440), ("Demak", -6.8900, 110.6400), ("Jepara", -6.5730, 110.6690),
    ("Batang", -6.4840, 110.7080), ("Kendal", -6.9170, 110.2110), ("Sukoharjo", -7.6340, 110.8130),
    ("Karanganyar", -7.5940, 110.9420), ("Wonogiri", -7.8150, 110.9250), ("Purbalingga", -7.3840, 109.3640),
    ("Banjarnegara", -7.3960, 109.6930), ("Cilacap", -7.7178, 109.0154), ("Grobogan", -7.0150, 110.9200),
    # DI Yogyakarta
    ("DI Yogyakarta", -7.7956, 110.3695), ("Yogyakarta", -7.7956, 110.3695), ("Jogja", -7.7956, 110.3695),
    ("Sleman", -7.7150, 110.3550), ("Bantul", -7.8910, 110.3350), ("Kulon Progo", -7.8380, 110.1660),
    ("Gunungkidul", -7.9870, 110.5020),
    # Jawa Timur
    ("Jawa Timur", -7.2575, 112.7521), ("Jatim", -7.2575, 112.7521), ("Surabaya", -7.2575, 112.7521),
    ("Malang", -7.9666, 112.6326), ("Batu", -7.8675, 112.5240), ("Kediri", -7.8167, 112.0117),
    ("Blitar", -8.0950, 112.1600), ("Madiun", -7.6298, 111.5239), ("Mojokerto", -7.4722, 112.4336),
    ("Pasuruan", -7.6400, 112.9070), ("Probolinggo", -7.7540, 113.2160), ("Jember", -8.1720, 113.6990),
    ("Banyuwangi", -8.2186, 114.3691), ("Situbondo", -7.7060, 114.0100), ("Bondowoso", -7.9130, 113.8230),
    ("Lumajang", -8.1330, 113.2200), ("Ngawi", -7.4040, 111.4430), ("Bojonegoro", -7.1500, 111.8850),
    ("Tuban", -6.8970, 112.0450), ("Lamongan", -7.1170, 112.4170), ("Gresik", -7.1560, 112.6550),
    ("Sidoarjo", -7.4470, 112.7180), ("Sampang", -7.1960, 113.2400), ("Pamekasan", -7.1560, 113.4730),
    ("Sumenep", -7.0110, 113.8660), ("Madura", -7.0580, 113.3790), ("Pacitan", -8.1930, 111.1020),
    ("Ponorogo", -7.8680, 111.4620), ("Trenggalek", -8.0540, 111.7060), ("Tulungagung", -8.0660, 111.9020),
    ("Nganjuk", -7.6040, 111.8990), ("Magetan", -7.6440, 111.3430), ("Bangkalan", -7.0460, 112.7350),
    # Bali
    ("Bali", -8.6500, 115.2167), ("Denpasar", -8.6500, 115.2167), ("Badung", -8.5840, 115.1770),
    ("Gianyar", -8.5410, 115.3230), ("Buleleng", -8.1060, 115.0910), ("Karangasem", -8.4510, 115.5970),
    ("Bangli", -8.4540, 115.3540), ("Klungkung", -8.5390, 115.4020), ("Tabanan", -8.5390, 115.1290),
    ("Singaraja", -8.1120, 115.0880), ("Nusa Dua", -8.7990, 115.2220), ("Kuta", -8.7230, 115.1720),
    # NTB
    ("Nusa Tenggara Barat", -8.5833, 116.1167), ("NTB", -8.5833, 116.1167), ("Mataram", -8.5833, 116.1167),
    ("Lombok", -8.5860, 116.3210), ("Sumbawa", -8.4930, 117.4210), ("Bima", -8.4580, 118.7270),
    # NTT
    ("Nusa Tenggara Timur", -10.1772, 123.6070), ("NTT", -10.1772, 123.6070), ("Kupang", -10.1772, 123.6070),
    ("Flores", -8.6470, 121.1310), ("Labuan Bajo", -8.4966, 119.8878), ("Ende", -8.8420, 121.6640),
    ("Maumere", -8.6190, 122.2120), ("Timor", -9.2800, 124.9400), ("Alor", -8.2740, 124.7440),
    # Kalimantan Barat
    ("Kalimantan Barat", -0.0263, 109.3425), ("Kalbar", -0.0263, 109.3425), ("Pontianak", -0.0263, 109.3425),
    ("Singkawang", 0.9080, 108.9850), ("Sambas", 1.3620, 109.2810), ("Ketapang", -1.8520, 109.9760),
    # Kalimantan Tengah
    ("Kalimantan Tengah", -2.2090, 113.9140), ("Kalteng", -2.2090, 113.9140), ("Palangka Raya", -2.2090, 113.9140),
    ("Pangkalan Bun", -2.6740, 111.6250), ("Sampit", -2.5330, 112.9490),
    # Kalimantan Selatan
    ("Kalimantan Selatan", -3.3186, 114.5944), ("Kalsel", -3.3186, 114.5944), ("Banjarmasin", -3.3186, 114.5944),
    ("Banjarbaru", -3.4560, 114.8450), ("Martapura", -3.4110, 114.8570),
    # Kalimantan Timur
    ("Kalimantan Timur", -0.5022, 117.1536), ("Kaltim", -0.5022, 117.1536), ("Samarinda", -0.5022, 117.1536),
    ("Balikpapan", -1.2379, 116.8529), ("Bontang", 0.1290, 117.4700), ("Tenggarong", -0.4360, 116.9900),
    ("Sangatta", 0.3390, 117.5400), ("Kutai", -0.4400, 116.9800),
    # Kalimantan Utara
    ("Kalimantan Utara", 2.8375, 117.3653), ("Kaltara", 2.8375, 117.3653), ("Tanjung Selor", 2.8375, 117.3653),
    ("Tarakan", 3.3271, 117.5786), ("Nunukan", 4.0590, 116.6800), ("Malinau", 3.5830, 116.6670),
    # Sulawesi Utara
    ("Sulawesi Utara", 1.4748, 124.8421), ("Sulut", 1.4748, 124.8421), ("Manado", 1.4748, 124.8421),
    ("Bitung", 1.4360, 125.1870), ("Tomohon", 1.3180, 124.8410), ("Kotamobagu", 0.7330, 124.3170),
    # Gorontalo
    ("Gorontalo", 0.5400, 123.0600), ("Kota Gorontalo", 0.5400, 123.0600),
    # Sulawesi Tengah
    ("Sulawesi Tengah", -0.9083, 119.8333), ("Sulteng", -0.9083, 119.8333), ("Palu", -0.9083, 119.8333),
    ("Poso", -1.3960, 120.7530), ("Luwuk", -0.9500, 122.7900), ("Toli-Toli", 1.0370, 120.8190),
    # Sulawesi Barat
    ("Sulawesi Barat", -2.6778, 118.8864), ("Sulbar", -2.6778, 118.8864), ("Mamuju", -2.6778, 118.8864),
    # Sulawesi Selatan
    ("Sulawesi Selatan", -5.1477, 119.4327), ("Sulsel", -5.1477, 119.4327), ("Makassar", -5.1477, 119.4327),
    ("Parepare", -4.0140, 119.6230), ("Palopo", -2.9940, 120.1970), ("Toraja", -3.0000, 119.9300),
    ("Tana Toraja", -2.9790, 119.9050), ("Wajo", -4.1370, 120.0290), ("Bone", -4.5390, 120.2030),
    ("Bulukumba", -5.5510, 120.1900),
    # Sulawesi Tenggara
    ("Sulawesi Tenggara", -3.9985, 122.5131), ("Sultra", -3.9985, 122.5131), ("Kendari", -3.9985, 122.5131),
    ("Baubau", -5.4620, 122.6060), ("Kolaka", -4.0490, 121.6060),
    # Maluku
    ("Maluku", -3.6954, 128.1814), ("Ambon", -3.6954, 128.1814), ("Tual", -5.6280, 132.7520),
    # Maluku Utara
    ("Maluku Utara", 0.7243, 127.5782), ("Malut", 0.7243, 127.5782), ("Sofifi", 0.7243, 127.5782),
    ("Ternate", 0.7906, 127.3844), ("Tidore", 0.6831, 127.4010),
    # Papua Barat
    ("Papua Barat", -0.8615, 134.0620), ("Papbar", -0.8615, 134.0620), ("Manokwari", -0.8615, 134.0620),
    ("Sorong", -0.8651, 131.2541), ("Raja Ampat", -0.5000, 130.8000), ("Fakfak", -2.9260, 132.2960),
    # Papua Barat Daya
    ("Papua Barat Daya", -0.8651, 131.2541),
    # Papua
    ("Papua", -2.5410, 140.7180), ("Jayapura", -2.5410, 140.7180), ("Timika", -4.5460, 136.8880),
    ("Nabire", -3.3665, 135.4910), ("Biak", -1.1750, 136.0500), ("Merauke", -8.4932, 140.4018),
    # Papua Pegunungan
    ("Papua Pegunungan", -4.0969, 138.9440), ("Wamena", -4.0969, 138.9440),
    # Papua Tengah
    ("Papua Tengah", -3.3665, 135.4910),
    # Papua Selatan
    ("Papua Selatan", -8.4932, 140.4018),
    # Nasional
    ("Indonesia", -2.5489, 118.0149),
]

# Indeks nama -> koordinat (nama terpanjang menang saat match)
_INDEX = {}
for name, lat, lon in LOCATIONS:
    key = name.lower()
    if key not in _INDEX or len(name) > len(_INDEX[key][0]):
        _INDEX[key] = (name, lat, lon)

NAMES = sorted(_INDEX.keys(), key=len, reverse=True)


def extract_locations(text: str, max_hits: int = 3) -> list[dict]:
    """Cari nama lokasi dalam teks. Kembalikan daftar {nama, lat, lon} unik."""
    if not text:
        return []
    low = text.lower()
    found: list[dict] = []
    seen: set[str] = set()
    for key in NAMES:
        # word boundary: hindari match di dalam kata ("kendali" != Kendal)
        if _match_word(low, key):
            if key not in seen:
                seen.add(key)
                name, lat, lon = _INDEX[key]
                found.append({"nama": name, "lat": lat, "lon": lon})
            if len(found) >= max_hits:
                break
    return found


def _match_word(text: str, key: str) -> bool:
    start = 0
    while True:
        idx = text.find(key, start)
        if idx == -1:
            return False
        before = idx == 0 or not text[idx - 1].isalnum()
        after = idx + len(key) >= len(text) or not text[idx + len(key)].isalnum()
        if before and after:
            return True
        start = idx + 1
