"""HTTP client. Sync only — wrap calls in a thread / asyncio.to_thread
if you need to drive it from an event loop."""

from __future__ import annotations

import os
from typing import Any, Dict, Iterable, List, Optional

import requests

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
    _disclaimers_from,
)

DEFAULT_BASE_URL = "https://api.halalterminal.com"
DEFAULT_TIMEOUT = 30.0
DEFAULT_USER_AGENT = "halalterminal-python/0.1.0"


class Client:
    """Halal Terminal API client.

    Args:
        api_key: Your `ht_…` key. If omitted, falls back to the
            `HALAL_TERMINAL_API_KEY` env var. Public endpoints
            (`get_disclaimers`, `health`) work without a key.
        base_url: Override for self-hosted / staging deployments.
        timeout: Per-request timeout in seconds.
        session: Provide your own `requests.Session` (e.g. with retries
            already configured); a fresh one is created otherwise.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        session: Optional[requests.Session] = None,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self.api_key = api_key or os.environ.get("HALAL_TERMINAL_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = session or requests.Session()
        self._user_agent = user_agent

    # ── Low-level request helpers ───────────────────────────────────────

    def _headers(self) -> Dict[str, str]:
        h = {"User-Agent": self._user_agent}
        if self.api_key:
            h["X-API-Key"] = self.api_key
        return h

    def _raise_for_status(self, response: requests.Response) -> None:
        if response.status_code < 400:
            return
        try:
            body = response.json()
        except ValueError:
            body = {}
        code = body.get("code") if isinstance(body, dict) else None
        message = (body.get("message") if isinstance(body, dict) else None) or response.text or "request failed"
        detail = body.get("detail") if isinstance(body, dict) else None

        kwargs = {"status_code": response.status_code, "code": code, "detail": detail}
        if response.status_code in (401, 403):
            raise ApiKeyError(message, **kwargs)
        if response.status_code == 404:
            raise NotFoundError(message, **kwargs)
        if response.status_code == 429:
            if code == "QUOTA_EXCEEDED":
                raise QuotaExceededError(message, **kwargs)
            raise RateLimitError(message, **kwargs)
        if response.status_code >= 500:
            raise ServerError(message, **kwargs)
        raise HalalTerminalError(message, **kwargs)

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Generic GET escape hatch — returns parsed JSON."""
        url = f"{self.base_url}{path if path.startswith('/') else '/' + path}"
        r = self._session.get(url, params=params, headers=self._headers(), timeout=self.timeout)
        self._raise_for_status(r)
        return r.json()

    def post(self, path: str, json: Optional[Dict[str, Any]] = None) -> Any:
        """Generic POST escape hatch — returns parsed JSON."""
        url = f"{self.base_url}{path if path.startswith('/') else '/' + path}"
        r = self._session.post(url, json=json, headers=self._headers(), timeout=self.timeout)
        self._raise_for_status(r)
        return r.json()

    # ── Typed endpoints ─────────────────────────────────────────────────

    def screen(self, symbol: str, *, force_refresh: bool = False) -> ScreeningResult:
        """Screen a single symbol for Shariah compliance."""
        params = {"force_refresh": "true"} if force_refresh else None
        body = self.get(f"/api/screen/{symbol.upper()}", params=params)
        return ScreeningResult.from_dict(body)

    def get_quote(self, symbol: str) -> Quote:
        body = self.get(f"/api/quote/{symbol.upper()}")
        return Quote.from_dict(body)

    def scan_portfolio(self, symbols: Iterable[str]) -> PortfolioScanResult:
        body = self.post("/api/portfolio/scan", json={"symbols": [s.upper() for s in symbols]})
        return PortfolioScanResult.from_dict(body)

    def calculate_zakat(
        self,
        holdings: List[Dict[str, Any]],
        *,
        gold_price_per_gram: Optional[float] = None,
    ) -> ZakatResult:
        """Compute zakat on stock holdings.

        Each holding is a dict like `{"symbol": "AAPL", "market_value": 25000}`.
        """
        payload: Dict[str, Any] = {"holdings": holdings}
        if gold_price_per_gram is not None:
            payload["gold_price_per_gram"] = gold_price_per_gram
        body = self.post("/api/zakat/calculate", json=payload)
        return ZakatResult.from_dict(body)

    def get_disclaimers(self) -> List[Disclaimer]:
        """Fetch the canonical disclaimer registry. No API key required."""
        body = self.get("/api/disclaimers")
        return _disclaimers_from(body.get("disclaimers"))

    def health(self) -> Dict[str, Any]:
        return self.get("/api/health")
