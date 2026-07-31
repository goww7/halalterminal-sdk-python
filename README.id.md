# halalterminal - SDK Python

![AAPL halal status](https://api.halalterminal.com/api/badge/AAPL.svg) _badge langsung dari API, sematkan untuk simbol apa pun_

Klien Python resmi untuk [Halal Terminal API](https://halalterminal.com) - penyaringan saham Syariah di seluruh 5 metodologi yang diaudit (AAOIFI, DJIM, FTSE, MSCI, S&P), data pasar waktu nyata, analisis look-through ETF, kalkulator zakat & pemurnian.

[![PyPI](https://img.shields.io/pypi/v/halalterminal)](https://pypi.org/project/halalterminal/)
[![Python](https://img.shields.io/pypi/pyversions/halalterminal)](https://pypi.org/project/halalterminal/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Daftar Isi

- [Instalasi](#install)
- [Otentikasi](#authentication)
- [Mulai Cepat](#quickstart)
- [Contoh Penggunaan](#usage-examples)
  - [Penyaringan Saham](#screen-a-stock)
  - [Pemindaian Portofolio](#portfolio-scan)
  - [Kutipan Pasar](#market-quote)
  - [Perhitungan Zakat](#zakat-calculation)
  - [Penanganan Kesalahan](#error-handling)
  - [Penampilan Disclaimer](#disclaimer-rendering)
  - [Jalan Keluar Umum](#generic-escape-hatch)
- [Referensi API](#api-reference)
  - [Konstruktor Klien](#client-constructor)
  - [Metode](#methods)
  - [Tipe Respons](#response-types)
  - [Kelas Kesalahan](#error-classes)
- [Penggunaan Async](#async-usage)
- [Pengujian](#testing)

---

## Instalasi

```bash
pip install halalterminal
```

Python ≥ 3.9. Dependensi runtime tunggal: [`requests`](https://docs.python-requests.org/).

---

## Otentikasi

Buat kunci API gratis - tanpa kartu kredit:

```bash
curl -s -X POST https://api.halalterminal.com/api/keys/generate \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com"}'
# {"api_key": "ht_…", "tier": "free", "tokens_per_month": 500}
```

Berikan kunci ke klien **atau** atur variabel lingkungan `HALAL_TERMINAL_API_KEY`:

```python
from halalterminal import Client

# Explicit key
ht = Client(api_key="ht_…")

# Env var fallback — no argument needed
# export HALAL_TERMINAL_API_KEY=ht_…
ht = Client()
```

Beberapa endpoint (`get_disclaimers`, `health`) bersifat publik dan berfungsi tanpa kunci apa pun.

---

## Mulai Cepat

```python
from halalterminal import Client

ht = Client(api_key="ht_…")

aapl = ht.screen("AAPL")
print(aapl.is_compliant)              # True
print(aapl.compliance_explanation)   # "Compliant under all 5 methodologies."
print(aapl.purification_rate)        # 0.009  (0.9 % of dividends to purify)

# Every response carries inline compliance copy — render it in your UI
for d in aapl.disclaimers:
    print(f"[{d.severity}] {d.text}")
```

---

## Contoh Penggunaan

### Penyaringan Saham

```python
from halalterminal import Client

ht = Client(api_key="ht_…")
result = ht.screen("AAPL")

# Top-level result
print(result.symbol)                       # "AAPL"
print(result.is_compliant)                 # True / False / None
print(result.shariah_compliance_status)    # "compliant" | "non_compliant" | "questionable"
print(result.business_screen_pass)         # True
print(result.financial_screen_pass)        # True
print(result.purification_rate)            # 0.009 — share of dividends to purify

# Per-methodology breakdown (AAOIFI, DJIM, FTSE, MSCI, SP500S)
for methodology, details in result.by_methodology.items():
    print(methodology, details["is_compliant"], details.get("reason"))

# Force a fresh API-side recalculation (bypasses the server cache)
fresh = ht.screen("NVDA", force_refresh=True)

# Anything not yet a typed attribute is in .raw
print(result.raw["some_new_field"])
```

### Pemindaian Portofolio

```python
from halalterminal import Client

ht = Client(api_key="ht_…")
portfolio = ht.scan_portfolio(["AAPL", "MSFT", "JNJ", "BAC"])

print(portfolio.total)              # 4
print(portfolio.compliant_count)    # 3
print(portfolio.non_compliant_count)# 1

# Per-symbol detail lives in .raw["results"]
for item in portfolio.raw["results"]:
    print(item["symbol"], item["is_compliant"])
```

Simbol diubah menjadi huruf kapital secara otomatis - "aapl" dan "AAPL" setara.

### Kutipan Pasar

```python
from halalterminal import Client

ht = Client(api_key="ht_…")
q = ht.get_quote("MSFT")

print(q.symbol)           # "MSFT"
print(q.name)             # "Microsoft Corporation"
print(q.price)            # 421.76
print(q.change)           # 2.34
print(q.change_percent)   # 0.56
print(q.volume)           # 19384721
print(q.market_cap)       # 3134000000000
```

### Perhitungan Zakat

```python
from halalterminal import Client

ht = Client(api_key="ht_…")

zakat = ht.calculate_zakat(
    holdings=[
        {"symbol": "AAPL", "market_value": 25_000},
        {"symbol": "MSFT", "market_value": 10_000},
    ],
    gold_price_per_gram=65.0,   # optional; API uses its own price if omitted
)

print(zakat.total_market_value)  # 35000.0
print(zakat.nisab_threshold)     # 5525.0
print(zakat.is_above_nisab)      # True
print(zakat.total_zakat)         # 875.0

# Per-holding zakat breakdown is in .raw["holdings"]
for h in zakat.raw["holdings"]:
    print(h["symbol"], h.get("zakat_amount"))
```

### Penanganan Kesalahan

```python
from halalterminal import (
    Client,
    ApiKeyError,
    QuotaExceededError,
    RateLimitError,
    NotFoundError,
    ServerError,
    HalalTerminalError,
)

ht = Client(api_key="ht_…")

try:
    result = ht.screen("AAPL")
except ApiKeyError:
    # 401/403 — key missing, invalid, or deactivated
    print("Check your API key at api.halalterminal.com/dashboard")
except QuotaExceededError as e:
    # 429 with code=QUOTA_EXCEEDED — monthly token allowance exhausted
    # e.detail carries the upgrade hint from the API
    print(f"Quota exhausted. Hint: {e.detail}")
except RateLimitError:
    # 429 from the upstream rate limiter (distinct from quota)
    import time; time.sleep(2)
except NotFoundError:
    # 404 — symbol not found in our database
    print("Unknown ticker")
except ServerError:
    # 5xx — server-side error, safe to retry with exponential backoff
    raise
except HalalTerminalError as e:
    # Catch-all for any other non-2xx response
    print(e.status_code, e.code, str(e))
```

Setiap pengecualian membawa `.status_code`, `.code` (kode kesalahan yang dapat dibaca mesin dari API), dan `.detail`.

### Penampilan Disclaimer

Setiap respons kepatuhan, data pasar, zakat, dan pemurnian membawa `disclaimers: list[Disclaimer]`. Setiap disclaimer diberi versi, ditandai dengan tingkat keparahan, dan memiliki tautan langsung ke bagian tertentu dari halaman legal Halal Terminal. **Anda harus menampilkan ini di setiap permukaan yang menghadap pengguna** - API menyediakan salinan kepatuhan untuk Anda.

```python
from halalterminal import Client

ht = Client(api_key="ht_…")
result = ht.screen("AAPL")

for d in result.disclaimers:
    print(d.id)        # "screening"
    print(d.version)   # "2026-05-12" — ISO date; advances when text is edited
    print(d.severity)  # "religious" (fatwa caveats) | "data" (freshness/sourcing)
    print(d.lang)      # "en"
    print(d.text)      # "Methodology-based screen, not a fatwa."
    print(d.url)       # deep link to the specific legal section

# You can also fetch the full public disclaimer registry (no API key required)
ht_public = Client()
all_disclaimers = ht_public.get_disclaimers()
```

Bandingkan `d.version` dengan apa yang UI Anda tampilkan terakhir kali dan tampilkan ulang ketika maju.

### Jalan Keluar Umum

Halal Terminal API memaparkan 60+ endpoint. Jalur apa pun yang belum dicakup oleh metode bertipe dapat dijangkau melalui pembantu tingkat rendah:

```python
from halalterminal import Client

ht = Client(api_key="ht_…")

# GET — returns parsed JSON (dict, list, or scalar)
trending = ht.get("/api/trending")
print(trending)                     # [{"symbol": "AAPL", …}, …]

# GET with query parameters
etf = ht.get("/api/etf/HLAL", params={"look_through": "true"})

# POST — returns parsed JSON
report = ht.post("/api/reports/portfolio", json={"symbols": ["AAPL", "MSFT"]})

# Both methods raise the same typed exceptions on non-2xx responses
```

---

## Referensi API

### Konstruktor Klien

```python
Client(
    api_key: str | None = None,
    *,
    base_url: str = "https://api.halalterminal.com",
    timeout: float = 30.0,
    session: requests.Session | None = None,
)
```

| Parameter | Tipe | Default | Deskripsi |
|-----------|------|---------|-------------|
| `api_key` | `str \| None` | `None` | Kunci `ht_…` Anda. Menggunakan variabel lingkungan `HALAL_TERMINAL_API_KEY` jika tidak disediakan. |
| `base_url` | `str` | `"https://api.halalterminal.com"` | Pengganti untuk deployment staging atau self-hosted. Garis miring di akhir dihapus secara otomatis. |
| `timeout` | `float` | `30.0` | Batas waktu per permintaan dalam detik. |
| `session` | `requests.Session \| None` | `None` | Sediakan sesi yang telah dikonfigurasi (misalnya dengan retries). Sesi baru dibuat jika tidak disediakan. |

### Metode

| Metode | Mengembalikan | Deskripsi |
|--------|---------|-------------|
| `screen(symbol, *, force_refresh=False)` | `ScreeningResult` | Penyaringan kepatuhan Syariah untuk satu ticker. Atur `force_refresh=True` untuk menghindari cache server-side. |
| `get_quote(symbol)` | `Quote` | Harga waktu nyata, perubahan, volume, dan kapitalisasi pasar. |
| `scan_portfolio(symbols)` | `PortfolioScanResult` | Pemindaian kepatuhan massal. `symbols` adalah iterable apa pun dari string ticker. |
| `calculate_zakat(holdings, *, gold_price_per_gram=None)` | `ZakatResult` | Hitung kewajiban zakat pada kepemilikan saham. Setiap kepemilikan adalah `{"symbol": str, "market_value": float}`. |
| `get_disclaimers()` | `list[Disclaimer]` | Ambil registri disclaimer kanonikal. Tidak diperlukan kunci API. |
| `health()` | `dict` | Pemeriksaan ketersediaan API. Tidak diperlukan kunci API. |
| `get(path, params=None)` | `Any` | GET umum. Mengembalikan JSON yang telah diurai. |
| `post(path, json=None)` | `Any` | POST umum. Mengembalikan JSON yang telah diurai. |

### Tipe Respons

**`ScreeningResult`**

| Atribut | Tipe | Deskripsi |
|-----------|------|-------------|
| `symbol` | `str` | Simbol ticker (huruf kapital). |
| `is_compliant` | `bool \| None` | `True` / `False` / `None` (data tidak mencukupi). |
| `shariah_compliance_status` | `str \| None` | `"compliant"` \| `"non_compliant"` \| `"questionable"`. |
| `business_screen_pass` | `bool \| None` | Apakah penyaringan aktivitas bisnis lulus. |
| `financial_screen_pass` | `bool \| None` | Apakah penyaringan rasio keuangan lulus. |
| `purification_rate` | `float \| None` | Bagian dari dividen yang harus dimurnikan (misalnya `0.009` = 0.9%). |
| `compliance_explanation` | `str \| None` | Ringkasan putusan dalam bahasa sederhana. |
| `by_methodology` | `dict[str, dict]` | Rincian per-metodologi dengan kunci `"AAOIFI"`, `"DJIM"`, `"FTSE"`, `"MSCI"`, `"SP500S"`. |
| `disclaimers` | `list[Disclaimer]` | Salinan kepatuhan inline. |
| `raw` | `dict` | Respons API lengkap untuk bidang yang belum dipromosikan ke atribut bertipe. |

**`Quote`**

| Atribut | Tipe | Deskripsi |
|-----------|------|-------------|
| `symbol` | `str` | Simbol ticker. |
| `name` | `str` | Nama perusahaan. |
| `price` | `float` | Harga terbaru. |
| `change` | `float` | Perubahan harga absolut. |
| `change_percent` | `float` | Perubahan persentase. |
| `volume` | `int` | Volume perdagangan. |
| `market_cap` | `float \| None` | Kapitalisasi pasar (mungkin `None` untuk saham yang lebih kecil). |
| `disclaimers` | `list[Disclaimer]` | Salinan kesegaran data inline. |
| `raw` | `dict` | Respons API lengkap. |

**`ZakatResult`**

| Atribut | Tipe | Deskripsi |
|-----------|------|-------------|
| `total_market_value` | `float` | Jumlah dari semua nilai pasar kepemilikan. |
| `nisab_threshold` | `float` | Nisab dalam mata uang yang sama dengan kepemilikan. |
| `is_above_nisab` | `bool` | Apakah zakat harus dibayarkan (`total_market_value >= nisab_threshold`). |
| `total_zakat` | `float` | Kewajiban zakat (2.5% dari aset yang memenuhi syarat jika di atas nisab, jika tidak 0). |
| `disclaimers` | `list[Disclaimer]` | Peringatan keagamaan dan perhitungan. |
| `raw` | `dict` | Respons API lengkap termasuk rincian per-kepemilikan. |

**`PortfolioScanResult`**

| Atribut | Tipe | Deskripsi |
|-----------|------|-------------|
| `total` | `int` | Jumlah total simbol yang dipindai. |
| `compliant_count` | `int` | Jumlah simbol yang patuh. |
| `non_compliant_count` | `int` | Jumlah simbol yang tidak patuh atau diragukan. |
| `disclaimers` | `list[Disclaimer]` | Salinan kepatuhan inline. |
| `raw` | `dict` | Respons API lengkap termasuk `raw["results"]` untuk rincian per-simbol. |

**`Disclaimer`**

| Atribut | Tipe | Deskripsi |
|-----------|------|-------------|
| `id` | `str` | Pengenal yang dapat dibaca mesin (misalnya `"screening"`, `"zakat"`). |
| `text` | `str` | Teks disclaimer yang dapat dibaca manusia. |
| `url` | `str` | Tautan langsung ke bagian tertentu dari halaman legal. |
| `version` | `str` | String tanggal ISO - maju setiap kali teks diedit. |
| `lang` | `str` | Kode bahasa (saat ini selalu `"en"`). |
| `severity` | `str` | `"religious"` (peringatan fatwa/ulama) \| `"data"` (kesegaran/sumber). |

### Kelas Kesalahan

Semua pengecualian mewarisi dari `HalalTerminalError` dan membawa `.status_code`, `.code`, dan `.detail`.

| Pengecualian | Status HTTP | Pemicu |
|-----------|-------------|---------|
| `ApiKeyError` | 401 / 403 | Kunci hilang, tidak valid, kedaluwarsa, atau dinonaktifkan. |
| `NotFoundError` | 404 | Simbol atau sumber daya tidak ditemukan. |
| `QuotaExceededError` | 429 (`QUOTA_EXCEEDED`) | Alokasi token bulanan habis. `.detail` berisi petunjuk peningkatan. |
| `RateLimitError` | 429 (lainnya) | Pembatas laju hulu. Coba ulang dengan backoff. |
| `ServerError` | 5xx | Kegagalan sisi server. Aman untuk dicoba ulang dengan backoff eksponensial. |
| `HalalTerminalError` | 4xx lainnya | Penangkap segala untuk respons non-2xx lainnya. |

---

## Penggunaan Async

SDK ini bersifat sinkron. Untuk menggunakannya di dalam aplikasi async, jalankan panggilan yang memblokir di pool thread:

```python
import asyncio
from halalterminal import Client

ht = Client(api_key="ht_…")

async def get_screening(symbol: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, ht.screen, symbol)

result = asyncio.run(get_screening("AAPL"))
print(result.is_compliant)
```

Atau gunakan `asyncio.to_thread` (Python 3.9+):

```python
result = await asyncio.to_thread(ht.screen, "AAPL")
```

---

## Pengujian

Suite pengujian sepenuhnya offline - HTTP di-mock melalui [`responses`](https://github.com/getsentry/responses):

```bash
pip install -e ".[dev]"
pytest
```

Untuk menyuntikkan requests.Session kustom (misalnya untuk pengujian integrasi terhadap server staging):

```python
import requests
from halalterminal import Client

session = requests.Session()
session.verify = False   # staging cert, for example
ht = Client(api_key="ht_staging_…", base_url="https://staging.api.halalterminal.com", session=session)
```

---

## Pelajari Lebih Lanjut

- [Referensi API](https://api.halalterminal.com/api-reference)
- [Panduan Penyaringan Sukuk](https://www.halalterminal.com/research/sukuk-screening)
- [ETF Patuh Syariah Dibandingkan (2026)](https://www.halalterminal.com/research/sharia-etf-comprehensive-analysis)
- [Apakah Saham Saya Halal? Screener](https://www.halalterminal.com/stocks)

## Bagian dari Ekosistem Halal Terminal

[Website](https://www.halalterminal.com) · [API](https://api.halalterminal.com/api-reference) · [JS SDK](https://github.com/goww7/halalterminal-sdk-js) · [MCP server](https://github.com/goww7/halalterminal-mcp) · [Claude plugin](https://github.com/goww7/halalterminal-claude-skills) · [Discord bot](https://github.com/goww7/halal-discord-bot) · [TradingView indicator](https://github.com/goww7/halal-pine) · [Portfolio tracker](https://github.com/goww7/halal-portfolio-tracker)

## Lisensi

MIT. © Halal Terminal. Lihat [LICENSE](LICENSE).


---

Bagian dari [ekosistem terbuka Halal Terminal](https://github.com/goww7/awesome-islamic-finance):
[API](https://api.halalterminal.com) · [MCP server](https://github.com/goww7/halalterminal-mcp) · [Python SDK](https://github.com/goww7/halalterminal-sdk-python) · [JS SDK](https://github.com/goww7/halalterminal-sdk-js) · [Datasets](https://github.com/goww7/sp500-shariah-compliance) · [Awesome Islamic Finance](https://github.com/goww7/awesome-islamic-finance)