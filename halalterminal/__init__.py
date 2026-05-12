"""Halal Terminal API — official Python SDK.

Thin, dependency-light client around https://api.halalterminal.com.
Covers the most common endpoints with typed responses, plus a generic
escape hatch (`client.get`, `client.post`) for everything else.

Quickstart:

    from halalterminal import Client

    ht = Client(api_key="ht_…")          # free tier: 500 tokens/mo

    aapl = ht.screen("AAPL")
    print(aapl.is_compliant, aapl.shariah_compliance_status)
    for d in aapl.disclaimers:
        print(f"[{d.severity}] {d.text}")

Every relevant response carries a typed `disclaimers` list. Render
them in your UI — they're versioned, severity-tagged, and link to
the long-form legal page.
"""

from halalterminal._client import Client
from halalterminal._exceptions import (
    ApiKeyError,
    HalalTerminalError,
    NotFoundError,
    QuotaExceededError,
    RateLimitError,
    ServerError,
)
from halalterminal._models import (
    Disclaimer,
    PortfolioScanResult,
    Quote,
    ScreeningResult,
    ZakatResult,
)

__all__ = [
    "Client",
    "Disclaimer",
    "ScreeningResult",
    "Quote",
    "ZakatResult",
    "PortfolioScanResult",
    "HalalTerminalError",
    "ApiKeyError",
    "QuotaExceededError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
]

__version__ = "0.1.0"
