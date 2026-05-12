"""Typed exceptions matching the API's error envelope.

The API returns:
    {"code": "ERROR_CODE", "message": "...", "detail": null}

Each non-2xx status maps to a specific subclass so callers can catch
the cases they care about (e.g. `QuotaExceededError` to trigger an
upgrade flow) without parsing the body.
"""

from __future__ import annotations

from typing import Optional


class HalalTerminalError(Exception):
    """Base class. Carries the API's error envelope when available."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        code: Optional[str] = None,
        detail: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.detail = detail

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"{type(self).__name__}(status={self.status_code}, code={self.code!r}, message={str(self)!r})"


class ApiKeyError(HalalTerminalError):
    """401 / 403 — missing, invalid, or deactivated API key."""


class NotFoundError(HalalTerminalError):
    """404 — symbol or resource not found."""


class RateLimitError(HalalTerminalError):
    """429 from upstream rate limiter (distinct from quota)."""


class QuotaExceededError(HalalTerminalError):
    """429 with `QUOTA_EXCEEDED` — caller's monthly token allowance is exhausted."""


class ServerError(HalalTerminalError):
    """5xx — server-side failure. Safe to retry with backoff."""
