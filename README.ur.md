# halalterminal - Python SDK

![AAPL halal status](https://api.halalterminal.com/api/badge/AAPL.svg) _API سے براہ راست badge، کسی بھی symbol کے لیے embed کریں_

[Halal Terminal API](https://halalterminal.com) کا رسمی Python client - 5 آڈٹ شدہ طریقہ کار (AAOIFI, DJIM, FTSE, MSCI, S&P) کے ذریعے Shariah stock screening، حقیقی وقت market data، ETF look-through تجزیہ، zakat اور purification calculators۔

[![PyPI](https://img.shields.io/pypi/v/halalterminal)](https://pypi.org/project/halalterminal/)
[![Python](https://img.shields.io/pypi/pyversions/halalterminal)](https://pypi.org/project/halalterminal/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## فہرست مضامین

- [انسٹال](#install)
- [تصدیق](#authentication)
- [فوری آغاز](#quickstart)
- [استعمال کی مثالیں](#usage-examples)
  - [اسٹاک اسکرین کریں](#screen-a-stock)
  - [پورٹ فولیو اسکین](#portfolio-scan)
  - [مارکیٹ کوٹ](#market-quote)
  - [زکوٰۃ کا حساب](#zakat-calculation)
  - [خرابی کا نظم](#error-handling)
  - [دستخطی رینڈرنگ](#disclaimer-rendering)
  - [عام ایسکیپ ہیچ](#generic-escape-hatch)
- [API حوالہ](#api-reference)
  - [کلائنٹ سازنده](#client-constructor)
  - [طریقے](#methods)
  - [جوابی اقسام](#response-types)
  - [خرابی کی کلاسیں](#error-classes)
- [ایسنک استعمال](#async-usage)
- [جانچ](#testing)

---

## انسٹال

```bash
pip install halalterminal
```

Python ≥ 3.9۔ ایک رن ٹائم انحصار: [`requests`](https://docs.python-requests.org/)۔

---

## تصدیق

مفت API key بنائیں - کریڈٹ کارڈ درکار نہیں:

```bash
curl -s -X POST https://api.halalterminal.com/api/keys/generate \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com"}'
# {"api_key": "ht_…", "tier": "free", "tokens_per_month": 500}
```

key کلائنٹ میں دیں **یا** `HALAL_TERMINAL_API_KEY` ماحولیاتی متغیر مقرر کریں:

```python
from halalterminal import Client

# Explicit key
ht = Client(api_key="ht_…")

# Env var fallback — no argument needed
# export HALAL_TERMINAL_API_KEY=ht_…
ht = Client()
```

چند endpoints (`get_disclaimers`, `health`) عوامی ہیں اور بغیر کسی key کے کام کرتے ہیں۔

---

## فوری آغاز

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

## استعمال کی مثالیں

### اسٹاک اسکرین کریں

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

### پورٹ فولیو اسکین

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

Symbols خود بخود uppercased ہو جاتے ہیں - `"aapl"` اور `"AAPL"` برابر ہیں۔

### مارکیٹ کوٹ

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

### زکوٰۃ کا حساب

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

### خرابی کا نظم

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

ہر استثنا `.status_code`، `.code` (API کا مشین پڑھنے کے قابل error code)، اور `.detail` لے کر آتا ہے۔

### دستخطی رینڈرنگ

ہر compliance، market-data، zakat، اور purification جواب ایک `disclaimers: list[Disclaimer]` لے کر آتا ہے۔ ہر disclaimer ورژن شدہ، severity-tagged، اور Halal Terminal legal page کے مخصوص سیکشن سے deep-link شدہ ہوتا ہے۔ **آپ کو یہ کسی بھی صارف کے سامنے آنے والی سطح پر رینڈر کرنا ہوگا** - API آپ کے لیے compliance copy فراہم کرتی ہے۔

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

`d.version` کا موازنہ اس سے کریں جو آپ کا UI آخری بار دکھا چکا ہے اور جب یہ آگے بڑھے تو دوبارہ رینڈر کریں۔

### عام ایسکیپ ہیچ

Halal Terminal API 60+ endpoints فراہم کرتا ہے۔ کسی بھی path تک جو ابھی تک typed method سے کور نہیں ہوا، low-level helpers کے ذریعے رسائی حاصل کی جا سکتی ہے:

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

## API حوالہ

### کلائنٹ سازنده

```python
Client(
    api_key: str | None = None,
    *,
    base_url: str = "https://api.halalterminal.com",
    timeout: float = 30.0,
    session: requests.Session | None = None,
)
```

| پیرامیٹر | قسم | ڈیفالٹ | تفصیل |
|-----------|------|---------|-------------|
| `api_key` | `str \| None` | `None` | آپ کی `ht_…` key۔ اگر چھوڑ دیا جائے تو `HALAL_TERMINAL_API_KEY` ماحولیاتی متغیر پر فال بیک کرتا ہے۔ |
| `base_url` | `str` | `"https://api.halalterminal.com"` | Staging یا self-hosted deployments کے لیے override۔ Trailing slash خود بخود ہٹا دیا جاتا ہے۔ |
| `timeout` | `float` | `30.0` | ہر درخواست کا timeout سیکنڈز میں۔ |
| `session` | `requests.Session \| None` | `None` | ایک پہلے سے تشکیل شدہ session فراہم کریں (مثلاً retries کے ساتھ)۔ اگر چھوڑ دیا جائے تو ایک نیا session بنایا جائے گا۔ |

### طریقے

| طریقہ | واپسی | تفصیل |
|--------|---------|-------------|
| `screen(symbol, *, force_refresh=False)` | `ScreeningResult` | کسی ایک ticker کے لیے Shariah compliance screen۔ server-side cache bypass کرنے کے لیے `force_refresh=True` مقرر کریں۔ |
| `get_quote(symbol)` | `Quote` | حقیقی وقت قیمت، تبدیلی، حجم، اور market cap۔ |
| `scan_portfolio(symbols)` | `PortfolioScanResult` | بلک compliance scan۔ `symbols` ticker strings کا کوئی بھی iterable ہے۔ |
| `calculate_zakat(holdings, *, gold_price_per_gram=None)` | `ZakatResult` | stock holdings پر zakat liability کا حساب۔ ہر holding `{"symbol": str, "market_value": float}` ہے۔ |
| `get_disclaimers()` | `list[Disclaimer]` | کینونیکل disclaimer registry حاصل کریں۔ API key درکار نہیں۔ |
| `health()` | `dict` | API liveness check۔ API key درکار نہیں۔ |
| `get(path, params=None)` | `Any` | عمومی GET۔ parsed JSON واپس کرتا ہے۔ |
| `post(path, json=None)` | `Any` | عمومی POST۔ parsed JSON واپس کرتا ہے۔ |

### جوابی اقسام

**`ScreeningResult`**

| خصوصیت | قسم | تفصیل |
|-----------|------|-------------|
| `symbol` | `str` | Ticker symbol (بڑے حروف میں)۔ |
| `is_compliant` | `bool \| None` | `True` / `False` / `None` (ناکافی data)۔ |
| `shariah_compliance_status` | `str \| None` | `"compliant"` \| `"non_compliant"` \| `"questionable"`۔ |
| `business_screen_pass` | `bool \| None` | کیا business-activity screen پاس ہوا۔ |
| `financial_screen_pass` | `bool \| None` | کیا financial-ratio screen پاس ہوا۔ |
| `purification_rate` | `float \| None` | dividends کی تطہیر کا حصہ (مثلاً `0.009` = 0.9%)۔ |
| `compliance_explanation` | `str \| None` | سادہ انگریزی میں فیصلے کا خلاصہ۔ |
| `by_methodology` | `dict[str, dict]` | فی methodology تفصیل، `"AAOIFI"`، `"DJIM"`، `"FTSE"`، `"MSCI"`، `"SP500S"` کے تحت۔ |
| `disclaimers` | `list[Disclaimer]` | Inline compliance copy۔ |
| `raw` | `dict` | typed attributes میں ابھی تک فروغ نہ پانے والے fields کے لیے مکمل API response۔ |

**`Quote`**

| خصوصیت | قسم | تفصیل |
|-----------|------|-------------|
| `symbol` | `str` | Ticker symbol۔ |
| `name` | `str` | Company name۔ |
| `price` | `float` | تازہ ترین قیمت۔ |
| `change` | `float` | مطلق قیمت میں تبدیلی۔ |
| `change_percent` | `float` | فیصد تبدیلی۔ |
| `volume` | `int` | ٹریڈنگ حجم۔ |
| `market_cap` | `float \| None` | Market capitalisation (چھوٹے stocks کے لیے `None` ہو سکتا ہے)۔ |
| `disclaimers` | `list[Disclaimer]` | Inline data-freshness copy۔ |
| `raw` | `dict` | مکمل API response۔ |

**`ZakatResult`**

| خصوصیت | قسم | تفصیل |
|-----------|------|-------------|
| `total_market_value` | `float` | تمام holding market values کا مجموعہ۔ |
| `nisab_threshold` | `float` | holdings والی ہی currency میں nisab۔ |
| `is_above_nisab` | `bool` | کیا zakat واجب ہے (`total_market_value >= nisab_threshold`)۔ |
| `total_zakat` | `float` | zakat liability (اگر nisab سے اوپر ہو تو eligible assets کا 2.5%، ورنہ 0)۔ |
| `disclaimers` | `list[Disclaimer]` | مذہبی اور حسابی caveats۔ |
| `raw` | `dict` | فی holding تفصیل سمیت مکمل API response۔ |

**`PortfolioScanResult`**

| خصوصیت | قسم | تفصیل |
|-----------|------|-------------|
| `total` | `int` | اسکین کی گئی symbols کی کل تعداد۔ |
| `compliant_count` | `int` | compliant symbols کی تعداد۔ |
| `non_compliant_count` | `int` | non-compliant یا questionable symbols کی تعداد۔ |
| `disclaimers` | `list[Disclaimer]` | Inline compliance copy۔ |
| `raw` | `dict` | فی symbol تفصیل کے لیے `raw["results"]` سمیت مکمل API response۔ |

**`Disclaimer`**

| خصوصیت | قسم | تفصیل |
|-----------|------|-------------|
| `id` | `str` | Machine-readable identifier (مثلاً `"screening"`، `"zakat"`)۔ |
| `text` | `str` | Human-readable disclaimer text۔ |
| `url` | `str` | legal page کے مخصوص سیکشن کے لیے deep link۔ |
| `version` | `str` | ISO date string - text میں ترمیم ہونے پر آگے بڑھتا ہے۔ |
| `lang` | `str` | Language code (فی الحال ہمیشہ `"en"`)۔ |
| `severity` | `str` | `"religious"` (fatwa/scholar caveats) \| `"data"` (freshness/sourcing)۔ |

### خرابی کی کلاسیں

تمام استثنیات `HalalTerminalError` سے وراثت میں آتی ہیں اور `.status_code`، `.code`، اور `.detail` لے کر آتی ہیں۔

| استثناء | HTTP status | ٹرگر |
|-----------|-------------|---------|
| `ApiKeyError` | 401 / 403 | key غائب، invalid، expired، یا deactivated۔ |
| `NotFoundError` | 404 | symbol یا resource نہیں ملا۔ |
| `QuotaExceededError` | 429 (`QUOTA_EXCEEDED`) | ماہانہ token allowance ختم ہو چکی ہے۔ `.detail` میں upgrade hint موجود ہے۔ |
| `RateLimitError` | 429 (other) | upstream rate limiter۔ backoff کے ساتھ دوبارہ کوشش کریں۔ |
| `ServerError` | 5xx | server-side ناکامی۔ exponential backoff کے ساتھ دوبارہ کوشش کرنا محفوظ ہے۔ |
| `HalalTerminalError` | any other 4xx | غیر متوقع non-2xx responses کے لیے catch-all۔ |

---

## ایسنک استعمال

SDK synchronous ہے۔ async application کے اندر اسے استعمال کرنے کے لیے، blocking calls کو ایک thread pool میں چلائیں:

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

یا `asyncio.to_thread` (Python 3.9+) استعمال کریں:

```python
result = await asyncio.to_thread(ht.screen, "AAPL")
```

---

## جانچ

ٹیسٹ سیٹ مکمل طور پر offline ہے - HTTP [`responses`](https://github.com/getsentry/responses) کے ذریعے mocked ہے:

```bash
pip install -e ".[dev]"
pytest
```

ایک custom `requests.Session` انجیکٹ کرنے کے لیے (مثلاً staging server کے خلاف integration testing کے لیے):

```python
import requests
from halalterminal import Client

session = requests.Session()
session.verify = False   # staging cert, for example
ht = Client(api_key="ht_staging_…", base_url="https://staging.api.halalterminal.com", session=session)
```

---

## مزید سیکھیں

- [API حوالہ](https://api.halalterminal.com/api-reference)
- [Sukuk screening guide](https://www.halalterminal.com/research/sukuk-screening)
- [Shariah-compliant ETFs compared (2026)](https://www.halalterminal.com/research/sharia-etf-comprehensive-analysis)
- [Is my stock halal? Screener](https://www.halalterminal.com/stocks)

## Halal Terminal ماحولیاتی نظام کا حصہ

[Website](https://www.halalterminal.com) · [API](https://api.halalterminal.com/api-reference) · [JS SDK](https://github.com/goww7/halalterminal-sdk-js) · [MCP server](https://github.com/goww7/halalterminal-mcp) · [Claude plugin](https://github.com/goww7/halalterminal-claude-skills) · [Discord bot](https://github.com/goww7/halal-discord-bot) · [TradingView indicator](https://github.com/goww7/halal-pine) · [Portfolio tracker](https://github.com/goww7/halal-portfolio-tracker)

## لائسنس

MIT۔ © Halal Terminal۔ [LICENSE](LICENSE) دیکھیں۔

---

[Halal Terminal open ecosystem](https://github.com/goww7/awesome-islamic-finance) کا حصہ:
[API](https://api.halalterminal.com) · [MCP server](https://github.com/goww7/halalterminal-mcp) · [Python SDK](https://github.com/goww7/halalterminal-sdk-python) · [JS SDK](https://github.com/goww7/halalterminal-sdk-js) · [Datasets](https://github.com/goww7/sp500-shariah-compliance) · [Awesome Islamic Finance](https://github.com/goww7/awesome-islamic-finance)