"""Typed response models.

Built as small frozen dataclasses so callers can rely on attribute
access (`result.is_compliant`) while also keeping the raw JSON
accessible via `result.raw` for fields not yet promoted to typed
attributes.

Models deliberately permit unknown keys — the API extends responses
forward-compatibly, so the SDK should never crash on a new server
field. Unknown keys are preserved in `.raw`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Disclaimer:
    """Inline disclaimer object attached to relevant responses.

    The `severity` field groups disclaimers into "religious" (fatwa /
    scholar caveats) and "data" (freshness / sourcing). `version` is an
    ISO date that advances any time the text is edited — clients can
    detect and re-display when copy changes.
    """

    id: str
    text: str
    url: str
    version: str = ""
    lang: str = "en"
    severity: str = ""

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Disclaimer":
        return cls(
            id=d.get("id", ""),
            text=d.get("text", ""),
            url=d.get("url", ""),
            version=d.get("version", ""),
            lang=d.get("lang", "en"),
            severity=d.get("severity", ""),
        )


def _disclaimers_from(raw: Optional[List[Dict[str, Any]]]) -> List[Disclaimer]:
    if not raw:
        return []
    return [Disclaimer.from_dict(d) for d in raw]


@dataclass(frozen=True)
class ScreeningResult:
    """Per-symbol screening response.

    `is_compliant` is tri-state: True / False / None (insufficient data
    to score under any methodology). Use `shariah_compliance_status`
    for the canonical lowercase string mirror.
    """

    symbol: str
    is_compliant: Optional[bool]
    shariah_compliance_status: Optional[str]
    business_screen_pass: Optional[bool]
    financial_screen_pass: Optional[bool]
    purification_rate: Optional[float]
    compliance_explanation: Optional[str]
    by_methodology: Dict[str, Dict[str, Any]]
    disclaimers: List[Disclaimer]
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ScreeningResult":
        return cls(
            symbol=d.get("symbol", ""),
            is_compliant=d.get("is_compliant"),
            shariah_compliance_status=d.get("shariah_compliance_status"),
            business_screen_pass=d.get("business_screen_pass"),
            financial_screen_pass=d.get("financial_screen_pass"),
            purification_rate=d.get("purification_rate"),
            compliance_explanation=d.get("compliance_explanation"),
            by_methodology=d.get("by_methodology") or {},
            disclaimers=_disclaimers_from(d.get("disclaimers")),
            raw=d,
        )


@dataclass(frozen=True)
class Quote:
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: int
    market_cap: Optional[float]
    disclaimers: List[Disclaimer]
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Quote":
        return cls(
            symbol=d.get("symbol", ""),
            name=d.get("name", ""),
            price=float(d.get("price") or 0.0),
            change=float(d.get("change") or 0.0),
            change_percent=float(d.get("changePercent") or 0.0),
            volume=int(d.get("volume") or 0),
            market_cap=d.get("marketCap"),
            disclaimers=_disclaimers_from(d.get("disclaimers")),
            raw=d,
        )


@dataclass(frozen=True)
class ZakatResult:
    total_market_value: float
    nisab_threshold: float
    is_above_nisab: bool
    total_zakat: float
    disclaimers: List[Disclaimer]
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ZakatResult":
        return cls(
            total_market_value=float(d.get("total_market_value") or 0.0),
            nisab_threshold=float(d.get("nisab_threshold") or 0.0),
            is_above_nisab=bool(d.get("is_above_nisab")),
            total_zakat=float(d.get("total_zakat") or 0.0),
            disclaimers=_disclaimers_from(d.get("disclaimers")),
            raw=d,
        )


@dataclass(frozen=True)
class PortfolioScanResult:
    """Multi-symbol scan output. Per-symbol details are in `raw['results']`."""

    total: int
    compliant_count: int
    non_compliant_count: int
    disclaimers: List[Disclaimer]
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PortfolioScanResult":
        summary = d.get("summary") or {}
        return cls(
            total=int(summary.get("total") or 0),
            compliant_count=int(summary.get("compliant") or 0),
            non_compliant_count=int(summary.get("non_compliant") or 0),
            disclaimers=_disclaimers_from(d.get("disclaimers")),
            raw=d,
        )
