# halalterminal — Python SDK

Official Python client for the [Halal Terminal API](https://halalterminal.com) — Shariah stock screening across 5 audited methodologies (AAOIFI, DJIM, FTSE, MSCI, S&P), real-time market data, ETF look-through analysis, zakat & purification calculators.

[![PyPI](https://img.shields.io/pypi/v/halalterminal)](https://pypi.org/project/halalterminal/)
[![Python](https://img.shields.io/pypi/pyversions/halalterminal)](https://pypi.org/project/halalterminal/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Table of contents

- [Install](#install)
- [Authentication](#authentication)
- [Quickstart](#quickstart)
- [Usage examples](#usage-examples)
  - [Screen a stock](#screen-a-stock)
  - [Portfolio scan](#portfolio-scan)
  - [Market quote](#market-quote)
  - [Zakat calculation](#zakat-calculation)
  - [Error handling](#error-handling)
  - [Disclaimer rendering](#disclaimer-rendering)
  - [Generic escape hatch](#generic-escape-hatch)
- [API reference](#api-reference)
  - [Client constructor](#client-constructor)
  - [Methods](#methods)
  - [Response types](#response-types)
  - [Error classes](#error-classes)
- [Async usage](#async-usage)
- [Testing](#testing)

---

## Install

```bash
pip install halalterminal
```

Python ≥ 3.9. Single runtime dependency: [`requests`](https://docs.python-requests.org/).

---

## Authentication

Generate a free API key — no credit card required:

```bash
curl -s -X POST https://api.halalterminal.com/api/keys/generate \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com"}'
# {"api_key": "ht_…", "tier": "free", "tokens_per_month": 500}
```

Pass the key to the client **or** set the `HALAL_TERMINAL_API_KEY` environment variable:

```python
from halalterminal import Client

# Explicit key
ht = Client(api_key="ht_…")

# Env var fallback — no argument needed
# export HALAL_TERMINAL_API_KEY=ht_…
ht = Client()
```

A handful of endpoints (`get_disclaimers`, `health`) are public and work without any key.

---

## Quickstart

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

## Usage examples

### Screen a stock

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

### Portfolio scan

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

Symbols are uppercased automatically — `"aapl"` and `"AAPL"` are equivalent.

### Market quote

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

### Zakat calculation

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

### Error handling

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
    print("Check your API key at halalterminal.com/dashboard")
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

Every exception carries `.status_code`, `.code` (the API's machine-readable error code), and `.detail`.

### Disclaimer rendering

Every compliance, market-data, zakat, and purification response carries a `disclaimers: list[Disclaimer]`. Each disclaimer is versioned, severity-tagged, and deep-links to a specific section of the Halal Terminal legal page. **You must render these in any user-facing surface** — the API ships your compliance copy for you.

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

Compare `d.version` against what your UI last displayed and re-render when it advances.

### Generic escape hatch

The Halal Terminal API surfaces 60+ endpoints. Any path not yet covered by a typed method is reachable via the low-level helpers:

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

## API reference

### Client constructor

```python
Client(
    api_key: str | None = None,
    *,
    base_url: str = "https://api.halalterminal.com",
    timeout: float = 30.0,
    session: requests.Session | None = None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `str \| None` | `None` | Your `ht_…` key. Falls back to `HALAL_TERMINAL_API_KEY` env var if omitted. |
| `base_url` | `str` | `"https://api.halalterminal.com"` | Override for staging or self-hosted deployments. Trailing slash is stripped automatically. |
| `timeout` | `float` | `30.0` | Per-request timeout in seconds. |
| `session` | `requests.Session \| None` | `None` | Provide a pre-configured session (e.g. with retries). A fresh session is created if omitted. |

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `screen(symbol, *, force_refresh=False)` | `ScreeningResult` | Shariah compliance screen for a single ticker. Set `force_refresh=True` to bypass the server-side cache. |
| `get_quote(symbol)` | `Quote` | Real-time price, change, volume, and market cap. |
| `scan_portfolio(symbols)` | `PortfolioScanResult` | Bulk compliance scan. `symbols` is any iterable of ticker strings. |
| `calculate_zakat(holdings, *, gold_price_per_gram=None)` | `ZakatResult` | Compute zakat liability on stock holdings. Each holding is `{"symbol": str, "market_value": float}`. |
| `get_disclaimers()` | `list[Disclaimer]` | Fetch the canonical disclaimer registry. No API key required. |
| `health()` | `dict` | API liveness check. No API key required. |
| `get(path, params=None)` | `Any` | Generic GET. Returns parsed JSON. |
| `post(path, json=None)` | `Any` | Generic POST. Returns parsed JSON. |

### Response types

**`ScreeningResult`**

| Attribute | Type | Description |
|-----------|------|-------------|
| `symbol` | `str` | Ticker symbol (uppercased). |
| `is_compliant` | `bool \| None` | `True` / `False` / `None` (insufficient data). |
| `shariah_compliance_status` | `str \| None` | `"compliant"` \| `"non_compliant"` \| `"questionable"`. |
| `business_screen_pass` | `bool \| None` | Whether the business-activity screen passed. |
| `financial_screen_pass` | `bool \| None` | Whether the financial-ratio screen passed. |
| `purification_rate` | `float \| None` | Fraction of dividends to purify (e.g. `0.009` = 0.9%). |
| `compliance_explanation` | `str \| None` | Plain-English verdict summary. |
| `by_methodology` | `dict[str, dict]` | Per-methodology breakdown keyed by `"AAOIFI"`, `"DJIM"`, `"FTSE"`, `"MSCI"`, `"SP500S"`. |
| `disclaimers` | `list[Disclaimer]` | Inline compliance copy. |
| `raw` | `dict` | Full API response for fields not yet promoted to typed attributes. |

**`Quote`**

| Attribute | Type | Description |
|-----------|------|-------------|
| `symbol` | `str` | Ticker symbol. |
| `name` | `str` | Company name. |
| `price` | `float` | Latest price. |
| `change` | `float` | Absolute price change. |
| `change_percent` | `float` | Percentage change. |
| `volume` | `int` | Trading volume. |
| `market_cap` | `float \| None` | Market capitalisation (may be `None` for smaller stocks). |
| `disclaimers` | `list[Disclaimer]` | Inline data-freshness copy. |
| `raw` | `dict` | Full API response. |

**`ZakatResult`**

| Attribute | Type | Description |
|-----------|------|-------------|
| `total_market_value` | `float` | Sum of all holding market values. |
| `nisab_threshold` | `float` | Nisab in the same currency as the holdings. |
| `is_above_nisab` | `bool` | Whether zakat is due (`total_market_value >= nisab_threshold`). |
| `total_zakat` | `float` | Zakat liability (2.5% of eligible assets if above nisab, else 0). |
| `disclaimers` | `list[Disclaimer]` | Religious and calculation caveats. |
| `raw` | `dict` | Full API response including per-holding detail. |

**`PortfolioScanResult`**

| Attribute | Type | Description |
|-----------|------|-------------|
| `total` | `int` | Total number of symbols scanned. |
| `compliant_count` | `int` | Count of compliant symbols. |
| `non_compliant_count` | `int` | Count of non-compliant or questionable symbols. |
| `disclaimers` | `list[Disclaimer]` | Inline compliance copy. |
| `raw` | `dict` | Full API response including `raw["results"]` for per-symbol detail. |

**`Disclaimer`**

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `str` | Machine-readable identifier (e.g. `"screening"`, `"zakat"`). |
| `text` | `str` | Human-readable disclaimer text. |
| `url` | `str` | Deep link to the specific section of the legal page. |
| `version` | `str` | ISO date string — advances each time the text is edited. |
| `lang` | `str` | Language code (currently always `"en"`). |
| `severity` | `str` | `"religious"` (fatwa/scholar caveats) \| `"data"` (freshness/sourcing). |

### Error classes

All exceptions inherit from `HalalTerminalError` and carry `.status_code`, `.code`, and `.detail`.

| Exception | HTTP status | Trigger |
|-----------|-------------|---------|
| `ApiKeyError` | 401 / 403 | Key missing, invalid, expired, or deactivated. |
| `NotFoundError` | 404 | Symbol or resource not found. |
| `QuotaExceededError` | 429 (`QUOTA_EXCEEDED`) | Monthly token allowance exhausted. `.detail` contains the upgrade hint. |
| `RateLimitError` | 429 (other) | Upstream rate limiter. Retry with backoff. |
| `ServerError` | 5xx | Server-side failure. Safe to retry with exponential backoff. |
| `HalalTerminalError` | any other 4xx | Catch-all for unexpected non-2xx responses. |

---

## Async usage

The SDK is synchronous. To use it inside an async application, run blocking calls in a thread pool:

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

Or use `asyncio.to_thread` (Python 3.9+):

```python
result = await asyncio.to_thread(ht.screen, "AAPL")
```

---

## Testing

The test suite is fully offline — HTTP is mocked via [`responses`](https://github.com/getsentry/responses):

```bash
pip install -e ".[dev]"
pytest
```

To inject a custom `requests.Session` (e.g. for integration testing against a staging server):

```python
import requests
from halalterminal import Client

session = requests.Session()
session.verify = False   # staging cert, for example
ht = Client(api_key="ht_staging_…", base_url="https://staging.api.halalterminal.com", session=session)
```

---

## Learn more

- [API reference](https://api.halalterminal.com/api-reference)
- [Sukuk screening guide](https://www.halalterminal.com/research/sukuk-screening)
- [Shariah-compliant ETFs compared (2026)](https://www.halalterminal.com/research/sharia-etf-comprehensive-analysis)
- [Is my stock halal? Screener](https://www.halalterminal.com/stocks)

## Part of the Halal Terminal ecosystem

[Website](https://www.halalterminal.com) · [API](https://api.halalterminal.com/api-reference) · [JS SDK](https://github.com/goww7/halalterminal-sdk-js) · [MCP server](https://github.com/goww7/halalterminal-mcp) · [Claude plugin](https://github.com/goww7/halalterminal-claude-skills) · [Discord bot](https://github.com/goww7/halal-discord-bot) · [TradingView indicator](https://github.com/goww7/halal-pine) · [Portfolio tracker](https://github.com/goww7/halal-portfolio-tracker)

## License

MIT. © Halal Terminal. See [LICENSE](LICENSE).
