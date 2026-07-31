# halalterminal - Python SDK

![AAPL halal status](https://api.halalterminal.com/api/badge/AAPL.svg) _lencana langsung daripada API, semat satu untuk sebarang simbol_

Klien Python rasmi untuk [Halal Terminal API](https://halalterminal.com) - Penapisan saham Shariah merentasi 5 metodologi diaudit (AAOIFI, DJIM, FTSE, MSCI, S&P), data pasaran masa nyata, analisis look-through ETF, kalkulator zakat & penyucian.

[![PyPI](https://img.shields.io/pypi/v/halalterminal)](https://pypi.org/project/halalterminal/)
[![Python](https://img.shields.io/pypi/pyversions/halalterminal)](https://pypi.org/project/halalterminal/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Kandungan

- [Pasang](#install)
- [Pengesahan](#authentication)
- [Permulaan pantas](#quickstart)
- [Contoh penggunaan](#usage-examples)
  - [Tapiskan saham](#screen-a-stock)
  - [Imbasan portfolio](#portfolio-scan)
  - [Petikan pasaran](#market-quote)
  - [Pengiraan zakat](#zakat-calculation)
  - [Pengendalian ralat](#error-handling)
  - [Paparan penafian](#disclaimer-rendering)
  - [Pintu keluar generik](#generic-escape-hatch)
- [Rujukan API](#api-reference)
  - [Pembina klien](#client-constructor)
  - [Kaedah](#methods)
  - [Jenis respons](#response-types)
  - [Kelas ralat](#error-classes)
- [Penggunaan async](#async-usage)
- [Ujian](#testing)

---

## Pasang

```bash
pip install halalterminal
```

Python ≥ 3.9. Kebergantungan runtime tunggal: [`requests`](https://docs.python-requests.org/).

---

## Pengesahan

Jana kunci API percuma - tiada kad kredit diperlukan:

```bash
curl -s -X POST https://api.halalterminal.com/api/keys/generate \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com"}'
# {"api_key": "ht_…", "tier": "free", "tokens_per_month": 500}
```

Luluskan kunci kepada klien **atau** tetapkan pemboleh ubah persekitaran `HALAL_TERMINAL_API_KEY`:

```python
from halalterminal import Client

# Explicit key
ht = Client(api_key="ht_…")

# Env var fallback — no argument needed
# export HALAL_TERMINAL_API_KEY=ht_…
ht = Client()
```

Segelintir titik akhir (`get_disclaimers`, `health`) adalah awam dan berfungsi tanpa sebarang kunci.

---

## Permulaan pantas

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

## Contoh penggunaan

### Tapiskan saham

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

### Imbasan portfolio

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

Simbol ditukar kepada huruf besar secara automatik - "aapl" dan "AAPL" adalah setara.

### Petikan pasaran

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

### Pengiraan zakat

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

### Pengendalian ralat

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

Setiap pengecualian membawa `.status_code`, `.code` (kod ralat boleh-baca-mesin API), dan `.detail`.

### Paparan penafian

Setiap respons pematuhan, data pasaran, zakat, dan penyucian membawa `disclaimers: list[Disclaimer]`. Setiap penafian mempunyai versi, tag keseriusan, dan pautan mendalam ke bahagian tertentu halaman undang-undang Halal Terminal. **Anda mesti memaparkan ini di mana-mana permukaan yang berdepan pengguna** - API menghantar salinan pematuhan untuk anda.

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

Bandingkan `d.version` dengan apa yang UI anda paparkan kali terakhir dan papar semula apabila ia maju.

### Pintu keluar generik

API Halal Terminal memaparkan 60+ titik akhir. Sebarang laluan yang belum dilindungi oleh kaedah berjenis boleh dicapai melalui pembantu peringkat rendah:

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

## Rujukan API

### Pembina klien

```python
Client(
    api_key: str | None = None,
    *,
    base_url: str = "https://api.halalterminal.com",
    timeout: float = 30.0,
    session: requests.Session | None = None,
)
```

| Parameter | Jenis | Lalai | Penerangan |
|-----------|------|---------|-------------|
| `api_key` | `str \| None` | `None` | Kunci `ht_…` anda. Jatuh balik ke pemboleh ubah persekitaran `HALAL_TERMINAL_API_KEY` jika diabaikan. |
| `base_url` | `str` | `"https://api.halalterminal.com"` | Tindihan untuk persekitaran peringkat atau hos sendiri. Tanda slash di hujung dipotong secara automatik. |
| `timeout` | `float` | `30.0` | Had masa tamat setiap permintaan dalam saat. |
| `session` | `requests.Session \| None` | `None` | Sediakan sesi pra-tetap (cth. dengan cubaan semula). Sesi baharu dicipta jika diabaikan. |

### Kaedah

| Kaedah | Pulangan | Penerangan |
|--------|---------|-------------|
| `screen(symbol, *, force_refresh=False)` | `ScreeningResult` | Penapisan pematuhan Shariah untuk satu simbol. Tetapkan `force_refresh=True` untuk melangkau cache pihak pelayan. |
| `get_quote(symbol)` | `Quote` | Harga masa nyata, perubahan, volum, dan nilai pasaran. |
| `scan_portfolio(symbols)` | `PortfolioScanResult` | Imbasan pematuhan pukal. `symbols` adalah sebarang iterasi rentetan simbol. |
| `calculate_zakat(holdings, *, gold_price_per_gram=None)` | `ZakatResult` | Kira kewajipan zakat ke atas pegangan saham. Setiap pegangan adalah `{"symbol": str, "market_value": float}`. |
| `get_disclaimers()` | `list[Disclaimer]` | Dapatkan daftar penafian piawai. Tiada kunci API diperlukan. |
| `health()` | `dict` | Pemeriksaan keaktifan API. Tiada kunci API diperlukan. |
| `get(path, params=None)` | `Any` | GET generik. Pulangkan JSON yang dihuraikan. |
| `post(path, json=None)` | `Any` | POST generik. Pulangkan JSON yang dihuraikan. |

### Jenis respons

**`ScreeningResult`**

| Atribut | Jenis | Penerangan |
|-----------|------|-------------|
| `symbol` | `str` | Simbol ticker (huruf besar). |
| `is_compliant` | `bool \| None` | `True` / `False` / `None` (data tidak mencukupi). |
| `shariah_compliance_status` | `str \| None` | `"compliant"` \| `"non_compliant"` \| `"questionable"`. |
| `business_screen_pass` | `bool \| None` | Sama ada penapisan aktiviti perniagaan lulus. |
| `financial_screen_pass` | `bool \| None` | Sama ada penapisan nisbah kewangan lulus. |
| `purification_rate` | `float \| None` | Pecahan dividen untuk disucikan (cth. `0.009` = 0.9%). |
| `compliance_explanation` | `str \| None` | Ringkasan penghakiman dalam bahasa mudah. |
| `by_methodology` | `dict[str, dict]` | Pecahan mengikut metodologi dikunci oleh `"AAOIFI"`, `"DJIM"`, `"FTSE"`, `"MSCI"`, `"SP500S"`. |
| `disclaimers` | `list[Disclaimer]` | Salinan pematuhan sebaris. |
| `raw` | `dict` | Respons API penuh untuk medan yang belum dinaikkan kepada atribut berjenis. |

**`Quote`**

| Atribut | Jenis | Penerangan |
|-----------|------|-------------|
| `symbol` | `str` | Simbol ticker. |
| `name` | `str` | Nama syarikat. |
| `price` | `float` | Harga terkini. |
| `change` | `float` | Perubahan harga mutlak. |
| `change_percent` | `float` | Perubahan peratusan. |
| `volume` | `int` | Volum dagangan. |
| `market_cap` | `float \| None` | Permodalan pasaran (mungkin `None` untuk saham kecil). |
| `disclaimers` | `list[Disclaimer]` | Salinan kesegaran data sebaris. |
| `raw` | `dict` | Respons API penuh. |

**`ZakatResult`**

| Atribut | Jenis | Penerangan |
|-----------|------|-------------|
| `total_market_value` | `float` | Jumlah semua nilai pasaran pegangan. |
| `nisab_threshold` | `float` | Nisab dalam mata wang yang sama dengan pegangan. |
| `is_above_nisab` | `bool` | Sama ada zakat wajib dibayar (`total_market_value >= nisab_threshold`). |
| `total_zakat` | `float` | Kewajipan zakat (2.5% daripada aset layak jika melebihi nisab, jika tidak 0). |
| `disclaimers` | `list[Disclaimer]` | Penafian agama dan pengiraan. |
| `raw` | `dict` | Respons API penuh termasuk perincian setiap pegangan. |

**`PortfolioScanResult`**

| Atribut | Jenis | Penerangan |
|-----------|------|-------------|
| `total` | `int` | Jumlah bilangan simbol diimbas. |
| `compliant_count` | `int` | Bilangan simbol patuh. |
| `non_compliant_count` | `int` | Bilangan simbol tidak patuh atau dipertikaikan. |
| `disclaimers` | `list[Disclaimer]` | Salinan pematuhan sebaris. |
| `raw` | `dict` | Respons API penuh termasuk `raw["results"]` untuk perincian setiap simbol. |

**`Disclaimer`**

| Atribut | Jenis | Penerangan |
|-----------|------|-------------|
| `id` | `str` | Pengenal boleh-baca-mesin (cth. `"screening"`, `"zakat"`). |
| `text` | `str` | Teks penafian boleh-baca-manusia. |
| `url` | `str` | Pautan mendalam ke bahagian tertentu halaman undang-undang. |
| `version` | `str` | Rentetan tarikh ISO - maju setiap kali teks diedit. |
| `lang` | `str` | Kod bahasa (kini sentiasa `"en"`). |
| `severity` | `str` | `"religious"` (penafian fatwa/ulama) \| `"data"` (kesegaran/sumber). |

### Kelas ralat

Semua pengecualian mewarisi `HalalTerminalError` dan membawa `.status_code`, `.code`, dan `.detail`.

| Pengecualian | Status HTTP | Pencetus |
|-----------|-------------|---------|
| `ApiKeyError` | 401 / 403 | Kunci hilang, tidak sah, tamat tempoh, atau dinyahaktifkan. |
| `NotFoundError` | 404 | Simbol atau sumber tidak dijumpai. |
| `QuotaExceededError` | 429 (`QUOTA_EXCEEDED`) | Ela token bulanan habis. `.detail` mengandungi petua naik taraf. |
| `RateLimitError` | 429 (lain) | Penghad kadar huluan. Cuba semula dengan penangguhan. |
| `ServerError` | 5xx | Kegagalan pihak pelayan. Selamat untuk dicuba semula dengan penangguhan eksponen. |
| `HalalTerminalError` | mana-mana 4xx lain | Penangkap semua untuk respons bukan-2xx yang tidak dijangka. |

---

## Penggunaan async

SDK adalah segerak. Untuk menggunakannya dalam aplikasi async, jalankan panggilan menyekat dalam kumpulan utas:

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

## Ujian

Suite ujian adalah sepenuhnya luar talian - HTTP ditiru melalui [`responses`](https://github.com/getsentry/responses):

```bash
pip install -e ".[dev]"
pytest
```

Untuk menyuntik `requests.Session` tersuai (cth. untuk ujian integrasi terhadap pelayan peringkat):

```python
import requests
from halalterminal import Client

session = requests.Session()
session.verify = False   # staging cert, for example
ht = Client(api_key="ht_staging_…", base_url="https://staging.api.halalterminal.com", session=session)
```

---

## Ketahui lebih lanjut

- [Rujukan API](https://api.halalterminal.com/api-reference)
- [Panduan penapisan Sukuk](https://www.halalterminal.com/research/sukuk-screening)
- [ETF patuh Shariah dibandingkan (2026)](https://www.halalterminal.com/research/sharia-etf-comprehensive-analysis)
- [Adakah saham saya halal? Penapis](https://www.halalterminal.com/stocks)

## Sebahagian daripada ekosistem Halal Terminal

[Laman web](https://www.halalterminal.com) · [API](https://api.halalterminal.com/api-reference) · [JS SDK](https://github.com/goww7/halalterminal-sdk-js) · [Pelayan MCP](https://github.com/goww7/halalterminal-mcp) · [Plugin Claude](https://github.com/goww7/halalterminal-claude-skills) · [Bot Discord](https://github.com/goww7/halal-discord-bot) · [Penunjuk TradingView](https://github.com/goww7/halal-pine) · [Penjejak portfolio](https://github.com/goww7/halal-portfolio-tracker)

## Lesen

MIT. © Halal Terminal. Lihat [LICENSE](LICENSE).

---

Sebahagian daripada [ekosistem terbuka Halal Terminal](https://github.com/goww7/awesome-islamic-finance):
[API](https://api.halalterminal.com) · [Pelayan MCP](https://github.com/goww7/halalterminal-mcp) · [SDK Python](https://github.com/goww7/halalterminal-sdk-python) · [SDK JS](https://github.com/goww7/halalterminal-sdk-js) · [Set data](https://github.com/goww7/sp500-shariah-compliance) · [Awesome Islamic Finance](https://github.com/goww7/awesome-islamic-finance)