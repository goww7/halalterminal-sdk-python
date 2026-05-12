# Changelog

All notable changes to the `halalterminal` Python SDK will be documented in
this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-05-12

### Changed
- Source code moved out of the FinanceData2 monorepo into its own public
  repository at `github.com/goww7/halalterminal-sdk-python`. The `Source`
  and `Issues` URLs in `pyproject.toml` now point there. No code changes —
  the API surface is identical to 0.1.0.

## [0.1.0] - 2026-05-12

Initial public release.

### Added
- `Client` built on `requests`, supports Python 3.9+.
- API-key auth via constructor argument or the `HALAL_TERMINAL_API_KEY` env var.
- Typed endpoints: `screen`, `get_quote`, `scan_portfolio`, `calculate_zakat`,
  `get_disclaimers`, `health`.
- Generic `get` / `post` escape hatches for any endpoint not yet wrapped.
- Frozen-dataclass response models: `ScreeningResult`, `Quote`,
  `PortfolioScanResult`, `ZakatResult`, `Disclaimer` — with a `.raw` dict
  preserved for fields not yet promoted to typed attributes.
- Error hierarchy: `HalalTerminalError` (base), `ApiKeyError`, `NotFoundError`,
  `RateLimitError`, `QuotaExceededError`, `ServerError` — mapped from HTTP
  status and the API's `code` field.
