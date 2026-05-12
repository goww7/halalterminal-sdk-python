"""Unit tests for the Python SDK using mocked HTTP via `responses`.

Each test pins a piece of the public contract: typed return shape,
disclaimer parsing, error-class routing, escape-hatch behavior, env
fallback for the API key. No network access — fully offline.
"""

from __future__ import annotations

import pytest
import responses

from halalterminal import (
    ApiKeyError,
    Client,
    Disclaimer,
    NotFoundError,
    PortfolioScanResult,
    QuotaExceededError,
    Quote,
    RateLimitError,
    ScreeningResult,
    ServerError,
    ZakatResult,
)


_DISCLAIMER = {
    "id": "screening",
    "version": "2026-05-12",
    "lang": "en",
    "severity": "religious",
    "text": "Methodology-based screen, not a fatwa.",
    "url": "https://halalterminal.com/legal/disclaimer#no-shariah-certification",
}


# ── Construction ────────────────────────────────────────────────────────


def test_constructor_uses_env_var_when_no_key_passed(monkeypatch):
    monkeypatch.setenv("HALAL_TERMINAL_API_KEY", "ht_env_key")
    c = Client()
    assert c.api_key == "ht_env_key"


def test_explicit_key_wins_over_env(monkeypatch):
    monkeypatch.setenv("HALAL_TERMINAL_API_KEY", "ht_env_key")
    c = Client(api_key="ht_explicit")
    assert c.api_key == "ht_explicit"


def test_base_url_trailing_slash_stripped():
    c = Client(api_key="k", base_url="https://api.halalterminal.com/")
    assert c.base_url == "https://api.halalterminal.com"


# ── screen() ────────────────────────────────────────────────────────────


@responses.activate
def test_screen_returns_typed_result_with_disclaimers():
    responses.add(
        responses.GET,
        "https://api.halalterminal.com/api/screen/AAPL",
        json={
            "symbol": "AAPL",
            "is_compliant": True,
            "shariah_compliance_status": "compliant",
            "business_screen_pass": True,
            "financial_screen_pass": True,
            "purification_rate": 0.012,
            "compliance_explanation": "Compliant under all 5 methodologies.",
            "by_methodology": {"AAOIFI": {"is_compliant": True, "verified": True, "reason": None}},
            "disclaimers": [_DISCLAIMER],
        },
        status=200,
    )

    result = Client(api_key="k").screen("AAPL")
    assert isinstance(result, ScreeningResult)
    assert result.symbol == "AAPL"
    assert result.is_compliant is True
    assert result.shariah_compliance_status == "compliant"
    assert result.by_methodology["AAOIFI"]["verified"] is True
    assert len(result.disclaimers) == 1
    assert isinstance(result.disclaimers[0], Disclaimer)
    assert result.disclaimers[0].severity == "religious"
    assert result.disclaimers[0].version == "2026-05-12"


@responses.activate
def test_screen_uppercases_symbol():
    responses.add(
        responses.GET,
        "https://api.halalterminal.com/api/screen/MSFT",
        json={"symbol": "MSFT", "is_compliant": True, "shariah_compliance_status": "compliant",
              "business_screen_pass": True, "financial_screen_pass": True, "purification_rate": 0.0,
              "compliance_explanation": "", "by_methodology": {}, "disclaimers": []},
        status=200,
    )
    Client(api_key="k").screen("msft")  # lowercase input
    assert responses.calls[0].request.url.endswith("/api/screen/MSFT")


@responses.activate
def test_screen_force_refresh_passes_param():
    responses.add(
        responses.GET,
        "https://api.halalterminal.com/api/screen/AAPL",
        json={"symbol": "AAPL", "is_compliant": True, "shariah_compliance_status": "compliant",
              "business_screen_pass": True, "financial_screen_pass": True, "purification_rate": 0.0,
              "compliance_explanation": "", "by_methodology": {}, "disclaimers": []},
        status=200,
    )
    Client(api_key="k").screen("AAPL", force_refresh=True)
    assert "force_refresh=true" in responses.calls[0].request.url


# ── get_quote / scan_portfolio / calculate_zakat ────────────────────────


@responses.activate
def test_get_quote_returns_typed_quote():
    responses.add(
        responses.GET,
        "https://api.halalterminal.com/api/quote/AAPL",
        json={
            "symbol": "AAPL", "name": "Apple Inc.", "price": 187.44, "change": 1.32,
            "changePercent": 0.71, "volume": 54638921, "high": 188.5, "low": 185.7,
            "open": 186.1, "previousClose": 186.12, "marketCap": 2890000000000,
            "disclaimers": [{"id": "market_data", "version": "2026-05-12", "lang": "en",
                             "severity": "data", "text": "Market data is delayed.",
                             "url": "https://halalterminal.com/legal/disclaimer#no-investment-advice"}],
        },
        status=200,
    )
    q = Client(api_key="k").get_quote("AAPL")
    assert isinstance(q, Quote)
    assert q.price == 187.44
    assert q.disclaimers[0].severity == "data"


@responses.activate
def test_scan_portfolio_unpacks_summary():
    responses.add(
        responses.POST,
        "https://api.halalterminal.com/api/portfolio/scan",
        json={
            "summary": {"total": 4, "compliant": 3, "non_compliant": 1},
            "results": [{"symbol": "AAPL", "is_compliant": True}],
            "disclaimers": [_DISCLAIMER],
        },
        status=200,
    )
    out = Client(api_key="k").scan_portfolio(["aapl", "msft", "jnj", "bac"])
    assert isinstance(out, PortfolioScanResult)
    assert out.total == 4
    assert out.compliant_count == 3
    assert out.non_compliant_count == 1
    # Symbols upper-cased on the way out
    import json
    body = json.loads(responses.calls[0].request.body)
    assert body["symbols"] == ["AAPL", "MSFT", "JNJ", "BAC"]


@responses.activate
def test_calculate_zakat_returns_typed_result():
    responses.add(
        responses.POST,
        "https://api.halalterminal.com/api/zakat/calculate",
        json={
            "total_market_value": 25000.0, "nisab_threshold": 5525.0,
            "gold_price_per_gram": 65.0, "is_above_nisab": True, "zakat_rate": 0.025,
            "total_zakat": 625.0, "holdings": [],
            "disclaimers": [{"id": "zakat", "version": "2026-05-12", "lang": "en",
                             "severity": "religious", "text": "Simplified zakat estimate…",
                             "url": "https://halalterminal.com/legal/disclaimer#zakat"}],
        },
        status=200,
    )
    z = Client(api_key="k").calculate_zakat(
        holdings=[{"symbol": "AAPL", "market_value": 25000}],
        gold_price_per_gram=65.0,
    )
    assert isinstance(z, ZakatResult)
    assert z.total_zakat == 625.0
    assert z.is_above_nisab is True
    assert z.disclaimers[0].id == "zakat"


# ── get_disclaimers (public registry, no key required) ──────────────────


@responses.activate
def test_get_disclaimers_returns_typed_list():
    responses.add(
        responses.GET,
        "https://api.halalterminal.com/api/disclaimers",
        json={"disclaimers": [_DISCLAIMER], "total": 1},
        status=200,
    )
    items = Client().get_disclaimers()  # no key
    assert len(items) == 1
    assert isinstance(items[0], Disclaimer)
    assert items[0].id == "screening"


# ── Error routing ───────────────────────────────────────────────────────


@responses.activate
def test_401_raises_api_key_error():
    responses.add(
        responses.GET, "https://api.halalterminal.com/api/screen/AAPL",
        json={"code": "API_KEY_REQUIRED", "message": "Missing X-API-Key", "detail": None},
        status=401,
    )
    with pytest.raises(ApiKeyError) as exc:
        Client(api_key="k").screen("AAPL")
    assert exc.value.status_code == 401
    assert exc.value.code == "API_KEY_REQUIRED"


@responses.activate
def test_404_raises_not_found_error():
    responses.add(
        responses.GET, "https://api.halalterminal.com/api/screen/NOPE",
        json={"code": "HTTP_404", "message": "Unknown symbol", "detail": None},
        status=404,
    )
    with pytest.raises(NotFoundError):
        Client(api_key="k").screen("NOPE")


@responses.activate
def test_429_quota_routes_to_quota_exceeded():
    responses.add(
        responses.GET, "https://api.halalterminal.com/api/screen/AAPL",
        json={"code": "QUOTA_EXCEEDED", "message": "Monthly limit exhausted", "detail": "Upgrade to Starter"},
        status=429,
    )
    with pytest.raises(QuotaExceededError) as exc:
        Client(api_key="k").screen("AAPL")
    assert exc.value.detail == "Upgrade to Starter"


@responses.activate
def test_429_non_quota_routes_to_rate_limit():
    responses.add(
        responses.GET, "https://api.halalterminal.com/api/screen/AAPL",
        json={"code": "RATE_LIMIT", "message": "Too many requests", "detail": None},
        status=429,
    )
    with pytest.raises(RateLimitError):
        Client(api_key="k").screen("AAPL")


@responses.activate
def test_500_routes_to_server_error():
    responses.add(
        responses.GET, "https://api.halalterminal.com/api/screen/AAPL",
        json={"code": "INTERNAL_ERROR", "message": "Boom", "detail": None},
        status=500,
    )
    with pytest.raises(ServerError):
        Client(api_key="k").screen("AAPL")


# ── Generic escape hatch ────────────────────────────────────────────────


@responses.activate
def test_get_escape_hatch_returns_raw_json():
    responses.add(
        responses.GET, "https://api.halalterminal.com/api/trending",
        json=[{"symbol": "AAPL"}, {"symbol": "MSFT"}], status=200,
    )
    out = Client(api_key="k").get("/api/trending")
    assert isinstance(out, list)
    assert out[0]["symbol"] == "AAPL"


@responses.activate
def test_post_escape_hatch_returns_raw_json():
    responses.add(
        responses.POST, "https://api.halalterminal.com/api/compare",
        json={"comparison": []}, status=200,
    )
    out = Client(api_key="k").post("/api/compare", json={"symbols": ["AAPL", "MSFT"]})
    assert out == {"comparison": []}


@responses.activate
def test_api_key_header_sent_when_set():
    responses.add(
        responses.GET, "https://api.halalterminal.com/api/health",
        json={"message": "ok"}, status=200,
    )
    Client(api_key="ht_test").health()
    assert responses.calls[0].request.headers["X-API-Key"] == "ht_test"


@responses.activate
def test_no_api_key_header_when_unset():
    """Public endpoints work without a key — don't send a blank header."""
    responses.add(
        responses.GET, "https://api.halalterminal.com/api/disclaimers",
        json={"disclaimers": [], "total": 0}, status=200,
    )
    Client().get_disclaimers()
    assert "X-API-Key" not in responses.calls[0].request.headers
