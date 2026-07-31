# halalterminal - Python SDK

![AAPL halal status](https://api.halalterminal.com/api/badge/AAPL.svg) _live badge from the API, embed one for any symbol_

عميل Python الرسمي لـ [Halal Terminal API](https://halalterminal.com) - فحص الأسهم الشرعية عبر 5 منهجيات مدققة (AAOIFI، DJIM، FTSE، MSCI، S&P)، وبيانات السوق في الوقت الفعلي، وتحليل الاستيعاب لصناديق الاستثمار المتداولة، وحاسبات الزكاة والتطهير.

[![PyPI](https://img.shields.io/pypi/v/halalterminal)](https://pypi.org/project/halalterminal/)
[![Python](https://img.shields.io/pypi/pyversions/halalterminal)](https://pypi.org/project/halalterminal/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## فهرس المحتويات

- [التثبيت](#install)
- [المصادقة](#authentication)
- [البدء السريع](#quickstart)
- [أمثلة الاستخدام](#usage-examples)
  - [فحص سهم](#screen-a-stock)
  - [فحص المحفظة](#portfolio-scan)
  - [بيانات السوق](#market-quote)
  - [حساب الزكاة](#zakat-calculation)
  - [معالجة الأخطاء](#error-handling)
  - [عرض إخلاء المسؤولية](#disclaimer-rendering)
  - [الوصول العام](#generic-escape-hatch)
- [مرجع واجهة البرمجة](#api-reference)
  - [منشئ العميل](#client-constructor)
  - [الطرق](#methods)
  - [أنواع الاستجابة](#response-types)
  - [أصناف الأخطاء](#error-classes)
- [الاستخدام غير المتزامن](#async-usage)
- [الاختبار](#testing)

---

## التثبيت

```bash
pip install halalterminal
```

Python ≥ 3.9. تبعية وقت التشغيل الوحيدة: [`requests`](https://docs.python-requests.org/).

---

## المصادقة

أنشئ مفتاح API مجاني - لا يلزم بطاقة ائتمان:

```bash
curl -s -X POST https://api.halalterminal.com/api/keys/generate \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com"}'
# {"api_key": "ht_…", "tier": "free", "tokens_per_month": 500}
```

مرر المفتاح إلى العميل **أو** اضبط متغير البيئة `HALAL_TERMINAL_API_KEY`:

```python
from halalterminal import Client

# Explicit key
ht = Client(api_key="ht_…")

# Env var fallback — no argument needed
# export HALAL_TERMINAL_API_KEY=ht_…
ht = Client()
```

بعض نقاط النهاية (`get_disclaimers`، `health`) عامة وتعمل دون أي مفتاح.

---

## البدء السريع

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

## أمثلة الاستخدام

### فحص سهم

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

### فحص المحفظة

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

يتم تحويل الرموز إلى أحرف كبيرة تلقائيًا - "aapl" و "AAPL" متكافئان.

### بيانات السوق

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

### حساب الزكاة

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

### معالجة الأخطاء

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

تحمل كل استثناء `.status_code` و`.code` (رمز الخطأ الآلي لواجهة البرمجة) و`.detail`.

### عرض إخلاء المسؤولية

تحمل كل استجابة للامتثال أو بيانات السوق أو الزكاة أو التطهير قائمة `disclaimers: list[Disclaimer]`. يتم إصدار رقم لكل إخلاء مسؤولية، وتصنيفه حسب الخطورة، وربطه برابط مباشر بقسم محدد من الصفحة القانونية لـ Halal Terminal. **يجب عليك عرض هذه الإخلاءات في أي واجهة موجهة للمستخدم** - توفر واجهة البرمجة نص الامتثال الخاص بك.

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

قارن `d.version` بما عرضه واجهة المستخدم آخر مرة، وأعد العرض عندما يتقدم.

### الوصول العام

تُتيح Halal Terminal API أكثر من 60 نقطة نهاية. أي مسار لم تغطه طريقة مكتوبة بعد يمكن الوصول إليه عبر المساعدين منخفضي المستوى:

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

## مرجع واجهة البرمجة

### منشئ العميل

```python
Client(
    api_key: str | None = None,
    *,
    base_url: str = "https://api.halalterminal.com",
    timeout: float = 30.0,
    session: requests.Session | None = None,
)
```

| المعامل | النوع | الافتراضي | الوصف |
|-----------|------|---------|-------------|
| `api_key` | `str \| None` | `None` | مفتاح `ht_…` الخاص بك. يعود إلى متغير البيئة `HALAL_TERMINAL_API_KEY` في حال التجاهل. |
| `base_url` | `str` | `"https://api.halalterminal.com"` | تجاوز لنشر التجريب أو الاستضافة الذاتية. يتم إزالة الشرطة المائلة اللاحقة تلقائيًا. |
| `timeout` | `float` | `30.0` | مهلة كل طلب بالثواني. |
| `session` | `requests.Session \| None` | `None` | توفير جلسة مهيأة مسبقًا (مثلاً مع إعادة المحاولات). يتم إنشاء جلسة جديدة في حال التجاهل. |

### الطرق

| الطريقة | الإرجاع | الوصف |
|--------|---------|-------------|
| `screen(symbol, *, force_refresh=False)` | `ScreeningResult` | فحص الامتثال الشرعي لرمز واحد. اضبط `force_refresh=True` لتجاوز ذاكرة التخزين المؤقت من جانب الخادم. |
| `get_quote(symbol)` | `Quote` | السعر في الوقت الفعلي، والتغير، وحجم التداول، والقيمة السوقية. |
| `scan_portfolio(symbols)` | `PortfolioScanResult` | فحص الامتثال المجمع. `symbols` هو أي مجموعة قابلة للتكرار من سلاسل الرموز. |
| `calculate_zakat(holdings, *, gold_price_per_gram=None)` | `ZakatResult` | حساب الزكاة المستحقة على ممتلكات الأسهم. كل أصل هو `{"symbol": str, "market_value": float}`. |
| `get_disclaimers()` | `list[Disclaimer]` | جلب سجل إخلاء المسؤولية القانوني. لا يتطلب مفتاح API. |
| `health()` | `dict` | فحص حيوية واجهة البرمجة. لا يتطلب مفتاح API. |
| `get(path, params=None)` | `Any` | GET عام. يُرجع JSON محلل. |
| `post(path, json=None)` | `Any` | POST عام. يُرجع JSON محلل. |

### أنواع الاستجابة

**`ScreeningResult`**

| الخاصية | النوع | الوصف |
|-----------|------|-------------|
| `symbol` | `str` | رمز السهم (بأحرف كبيرة). |
| `is_compliant` | `bool \| None` | `True` / `False` / `None` (بيانات غير كافية). |
| `shariah_compliance_status` | `str \| None` | `"compliant" \| "non_compliant" \| "questionable"`. |
| `business_screen_pass` | `bool \| None` | ما إذا كان فحص النشاط التجاري قد نجح. |
| `financial_screen_pass` | `bool \| None` | ما إذا كان فحص النسب المالية قد نجح. |
| `purification_rate` | `float \| None` | نسبة الأرباح المراد تطهيرها (مثلاً `0.009` = 0.9%). |
| `compliance_explanation` | `str \| None` | ملخص الحكم باللغة الإنجليزية البسيطة. |
| `by_methodology` | `dict[str, dict]` | التفصيل حسب المنهجية مفهرس بـ `"AAOIFI"`، `"DJIM"`، `"FTSE"`، `"MSCI"`، `"SP500S"`. |
| `disclaimers` | `list[Disclaimer]` | نص الامتثال المضمن. |
| `raw` | `dict` | استجابة واجهة البرمجة الكاملة للحقول التي لم تُرفع بعد إلى خصائص مكتوبة. |

**`Quote`**

| الخاصية | النوع | الوصف |
|-----------|------|-------------|
| `symbol` | `str` | رمز السهم. |
| `name` | `str` | اسم الشركة. |
| `price` | `float` | آخر سعر. |
| `change` | `float` | التغير المطلق للسعر. |
| `change_percent` | `float` | التغير بالنسبة المئوية. |
| `volume` | `int` | حجم التداول. |
| `market_cap` | `float \| None` | القيمة السوقية (قد تكون `None` للأسهم الأصغر). |
| `disclaimers` | `list[Disclaimer]` | نص حداثة البيانات المضمن. |
| `raw` | `dict` | استجابة واجهة البرمجة الكاملة. |

**`ZakatResult`**

| الخاصية | النوع | الوصف |
|-----------|------|-------------|
| `total_market_value` | `float` | مجموع قيم جميع الأصول السوقية. |
| `nisab_threshold` | `float` | النصاب بنفس عملة الأصول. |
| `is_above_nisab` | `bool` | ما إذا كانت الزكاة مستحقة (`total_market_value >= nisab_threshold`). |
| `total_zakat` | `float` | الزكاة المستحقة (2.5% من الأصول المؤهلة إذا كانت فوق النصاب، وإلا 0). |
| `disclaimers` | `list[Disclaimer]` | تحذيرات دينية وحسابية. |
| `raw` | `dict` | استجابة واجهة البرمجة الكاملة بما في ذلك التفاصيل لكل أصل. |

**`PortfolioScanResult`**

| الخاصية | النوع | الوصف |
|-----------|------|-------------|
| `total` | `int` | إجمالي عدد الرموز التي تم فحصها. |
| `compliant_count` | `int` | عدد الرموز المتوافقة. |
| `non_compliant_count` | `int` | عدد الرموز غير المتوافقة أو المشكوك فيها. |
| `disclaimers` | `list[Disclaimer]` | نص الامتثال المضمن. |
| `raw` | `dict` | استجابة واجهة البرمجة الكاملة بما في ذلك `raw["results"]` لتفاصيل كل رمز. |

**`Disclaimer`**

| الخاصية | النوع | الوصف |
|-----------|------|-------------|
| `id` | `str` | معرف آلي (مثلاً `"screening"`، `"zakat"`). |
| `text` | `str` | نص إخلاء مسؤولية مقروء للبشر. |
| `url` | `str` | رابط مباشر للقسم المحدد من الصفحة القانونية. |
| `version` | `str` | سلسلة تاريخ ISO - يتقدم في كل مرة يُحرر فيها النص. |
| `lang` | `str` | رمز اللغة (حاليًا دائمًا `"en"`). |
| `severity` | `str` | `"religious"` (تحذيرات فتوى) \| `"data"` (الحداثة/المصدر). |

### أصناف الأخطاء

ترث جميع الاستثناءات من `HalalTerminalError` وتحمل `.status_code` و`.code` و`.detail`.

| الاستثناء | حالة HTTP | المحفز |
|-----------|-------------|---------|
| `ApiKeyError` | 401 / 403 | المفتاح مفقود أو غير صالح أو منتهي الصلاحية أو معطل. |
| `NotFoundError` | 404 | الرمز أو المورد غير موجود. |
| `QuotaExceededError` | 429 (`QUOTA_EXCEEDED`) | استنفد الحصة الشهرية للرموز. تحتوي `.detail` على تلميح الترقية. |
| `RateLimitError` | 429 (other) | مقيد المعدل من المصدر الأعلى. أعد المحاولة مع تراجع. |
| `ServerError` | 5xx | فشل من جانب الخادم. من الآمن إعادة المحاولة مع تراجع أسي. |
| `HalalTerminalError` | any other 4xx | مصيدة شاملة لاستجابات non-2xx غير المتوقعة. |

---

## الاستخدام غير المتزامن

الحزمة متزامنة. لاستخدامها داخل تطبيق غير متزامن، شغل المكالمات المحجوبة في تجمع مؤشرات ترابط:

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

أو استخدم `asyncio.to_thread` (Python 3.9+):

```python
result = await asyncio.to_thread(ht.screen, "AAPL")
```

---

## الاختبار

مجموعة الاختبارات غير متصلة بالإنترنت بالكامل - يتم محاكاة HTTP عبر [`responses`](https://github.com/getsentry/responses):

```bash
pip install -e ".[dev]"
pytest
```

لحقن `requests.Session` مخصص (مثلاً للاختبار التكاملي مقابل خادم التجريب):

```python
import requests
from halalterminal import Client

session = requests.Session()
session.verify = False   # staging cert, for example
ht = Client(api_key="ht_staging_…", base_url="https://staging.api.halalterminal.com", session=session)
```

---

## معرفة المزيد

- [مرجع واجهة البرمجة](https://api.halalterminal.com/api-reference)
- [دليل فحص الصكوك](https://www.halalterminal.com/research/sukuk-screening)
- [مقارنة صناديق الاستثمار المتداولة المتوافقة مع الشريعة (2026)](https://www.halalterminal.com/research/sharia-etf-comprehensive-analysis)
- [هل سهمي حلال؟ أداة الفحص](https://www.halalterminal.com/stocks)

## جزء من نظام Halal Terminal البيئي

[Website](https://www.halalterminal.com) · [API](https://api.halalterminal.com/api-reference) · [JS SDK](https://github.com/goww7/halalterminal-sdk-js) · [MCP server](https://github.com/goww7/halalterminal-mcp) · [Claude plugin](https://github.com/goww7/halalterminal-claude-skills) · [Discord bot](https://github.com/goww7/halal-discord-bot) · [TradingView indicator](https://github.com/goww7/halal-pine) · [Portfolio tracker](https://github.com/goww7/halal-portfolio-tracker)

## الترخيص

MIT. © Halal Terminal. راجع [LICENSE](LICENSE).

---

جزء من [Halal Terminal open ecosystem](https://github.com/goww7/awesome-islamic-finance):
[API](https://api.halalterminal.com) · [MCP server](https://github.com/goww7/halalterminal-mcp) · [Python SDK](https://github.com/goww7/halalterminal-sdk-python) · [JS SDK](https://github.com/goww7/halalterminal-sdk-js) · [Datasets](https://github.com/goww7/sp500-shariah-compliance) · [Awesome Islamic Finance](https://github.com/goww7/awesome-islamic-finance)