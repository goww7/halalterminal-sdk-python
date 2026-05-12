# halalterminal — Python SDK

Official Python client for the [Halal Terminal API](https://halalterminal.com) — Shariah stock screening across 5 audited methodologies (AAOIFI, DJIM, FTSE, MSCI, S&P), real-time market data, ETF look-through analysis, zakat & purification calculators.

## Install

```bash
pip install halalterminal
```

Python ≥ 3.9, single runtime dependency (`requests`).

## Quickstart

```python
from halalterminal import Client

ht = Client(api_key="ht_…")          # or set HALAL_TERMINAL_API_KEY

# Screen a stock — works on 10,000+ tickers
aapl = ht.screen("AAPL")
print(aapl.is_compliant, aapl.compliance_explanation)

# Every relevant response carries typed disclaimers — render them in your UI
for d in aapl.disclaimers:
    print(f"[{d.severity}] {d.text}  ({d.url})")
```

Need a free API key? `POST https://api.halalterminal.com/api/keys/generate` with `{"email": "you@example.com"}` — no credit card.

## Typed endpoints

```python
quote     = ht.get_quote("MSFT")
portfolio = ht.scan_portfolio(["AAPL", "MSFT", "JNJ", "BAC"])
zakat     = ht.calculate_zakat(
    holdings=[{"symbol": "AAPL", "market_value": 25_000}],
    gold_price_per_gram=65.0,
)
disclaimers = ht.get_disclaimers()    # public registry, no API key required
```

Each call returns a frozen dataclass with the most-used fields promoted to attributes, plus a `.raw` dict for everything else.

## Generic escape hatch

The API surfaces 60+ endpoints. For anything not wrapped in a typed method:

```python
trending = ht.get("/api/trending")
report   = ht.post("/api/reports/portfolio", json={"symbols": ["AAPL", "MSFT"]})
```

## Error handling

```python
from halalterminal import ApiKeyError, QuotaExceededError, NotFoundError

try:
    ht.screen("NOTAREALTICKER")
except NotFoundError:
    ...
except QuotaExceededError as e:
    # e.detail carries the upgrade hint
    ...
except ApiKeyError:
    ...
```

## Disclaimers

Every compliance / market-data / zakat / purification response carries a `disclaimers: list[Disclaimer]`. Each disclaimer is versioned, severity-tagged (`religious` for fatwa caveats, `data` for freshness/sourcing), and deep-links to a specific section on the Halal Terminal legal page. Show them inline — the API ships your compliance copy for you.

```python
for d in aapl.disclaimers:
    print(d.id, d.version, d.severity, d.url)
```

## License

MIT. © Halal Terminal.
