# halalterminal - SDK Python

![AAPL halal status](https://api.halalterminal.com/api/badge/AAPL.svg) _badge en direct de l'API, intégrez-en un pour n'importe quel symbole_

Client Python officiel pour l'[Halal Terminal API](https://halalterminal.com) - Screening boursier sharia selon 5 méthodologies auditées (AAOIFI, DJIM, FTSE, MSCI, S&P), données de marché en temps réel, analyse look-through ETF, calculateurs de zakat et de purification.

[![PyPI](https://img.shields.io/pypi/v/halalterminal)](https://pypi.org/project/halalterminal/)
[![Python](https://img.shields.io/pypi/pyversions/halalterminal)](https://pypi.org/project/halalterminal/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Table des matières

- [Installation](#install)
- [Authentification](#authentication)
- [Démarrage rapide](#quickstart)
- [Exemples d'utilisation](#usage-examples)
  - [Analyser une action](#screen-a-stock)
  - [Analyse de portefeuille](#portfolio-scan)
  - [Cotation de marché](#market-quote)
  - [Calcul de zakat](#zakat-calculation)
  - [Gestion des erreurs](#error-handling)
  - [Affichage des avertissements](#disclaimer-rendering)
  - [Accès générique](#generic-escape-hatch)
- [Référence API](#api-reference)
  - [Constructeur du client](#client-constructor)
  - [Méthodes](#methods)
  - [Types de réponse](#response-types)
  - [Classes d'erreur](#error-classes)
- [Utilisation asynchrone](#async-usage)
- [Tests](#testing)

---

## Installation

```bash
pip install halalterminal
```

Python ≥ 3.9. Dépendance d'exécution unique : [`requests`](https://docs.python-requests.org/).

---

## Authentification

Générez une clé API gratuite - aucune carte de crédit requise :

```bash
curl -s -X POST https://api.halalterminal.com/api/keys/generate \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com"}'
# {"api_key": "ht_…", "tier": "free", "tokens_per_month": 500}
```

Passez la clé au client **ou** définissez la variable d'environnement `HALAL_TERMINAL_API_KEY` :

```python
from halalterminal import Client

# Explicit key
ht = Client(api_key="ht_…")

# Env var fallback — no argument needed
# export HALAL_TERMINAL_API_KEY=ht_…
ht = Client()
```

Quelques points de terminaison (`get_disclaimers`, `health`) sont publics et fonctionnent sans aucune clé.

---

## Démarrage rapide

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

## Exemples d'utilisation

### Analyser une action

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

### Analyse de portefeuille

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

Les symboles sont mis en majuscules automatiquement - `"aapl"` et `"AAPL"` sont équivalents.

### Cotation de marché

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

### Calcul de zakat

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

### Gestion des erreurs

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

Chaque exception porte `.status_code`, `.code` (le code d'erreur lisible par machine de l'API) et `.detail`.

### Affichage des avertissements

Chaque réponse de conformité, de données de marché, de zakat et de purification contient `disclaimers: list[Disclaimer]`. Chaque avertissement est versionné, étiqueté par sévérité et contient un lien profond vers une section spécifique de la page légale de Halal Terminal. **Vous devez les afficher sur toute surface destinée aux utilisateurs** - l'API vous fournit votre texte de conformité.

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

Comparez `d.version` avec ce que votre interface a affiché en dernier et réaffichez lorsqu'il évolue.

### Accès générique

L'API Halal Terminal expose plus de 60 points de terminaison. Tout chemin non encore couvert par une méthode typée est accessible via les aides bas niveau :

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

## Référence API

### Constructeur du client

```python
Client(
    api_key: str | None = None,
    *,
    base_url: str = "https://api.halalterminal.com",
    timeout: float = 30.0,
    session: requests.Session | None = None,
)
```

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `api_key` | `str \| None` | `None` | Votre clé `ht_…`. Revient à la variable d'environnement `HALAL_TERMINAL_API_KEY` si omise. |
| `base_url` | `str` | `"https://api.halalterminal.com"` | Remplacement pour les déploiements de staging ou auto-hébergés. Le slash de fin est retiré automatiquement. |
| `timeout` | `float` | `30.0` | Délai d'attente par requête en secondes. |
| `session` | `requests.Session \| None` | `None` | Fournit une session préconfigurée (par exemple avec des retries). Une nouvelle session est créée si omise. |

### Méthodes

| Méthode | Retour | Description |
|--------|---------|-------------|
| `screen(symbol, *, force_refresh=False)` | `ScreeningResult` | Analyse de conformité sharia pour un seul ticker. Définissez `force_refresh=True` pour contourner le cache côté serveur. |
| `get_quote(symbol)` | `Quote` | Prix, variation, volume et capitalisation boursière en temps réel. |
| `scan_portfolio(symbols)` | `PortfolioScanResult` | Analyse de conformité en masse. `symbols` est n'importe quel itérable de chaînes de tickers. |
| `calculate_zakat(holdings, *, gold_price_per_gram=None)` | `ZakatResult` | Calcule la zakat due sur les participations boursières. Chaque participation est `{"symbol": str, "market_value": float}`. |
| `get_disclaimers()` | `list[Disclaimer]` | Récupère le registre canonique des avertissements. Aucune clé API requise. |
| `health()` | `dict` | Vérification de disponibilité de l'API. Aucune clé API requise. |
| `get(path, params=None)` | `Any` | GET générique. Retourne du JSON parsé. |
| `post(path, json=None)` | `Any` | POST générique. Retourne du JSON parsé. |

### Types de réponse

**`ScreeningResult`**

| Attribut | Type | Description |
|-----------|------|-------------|
| `symbol` | `str` | Symbole du ticker (mis en majuscules). |
| `is_compliant` | `bool \| None` | `True` / `False` / `None` (données insuffisantes). |
| `shariah_compliance_status` | `str \| None` | `"compliant"` \| `"non_compliant"` \| `"questionable"`. |
| `business_screen_pass` | `bool \| None` | Indique si le screening d'activité a été réussi. |
| `financial_screen_pass` | `bool \| None` | Indique si le screening financier a été réussi. |
| `purification_rate` | `float \| None` | Fraction des dividendes à purifier (par exemple `0.009` = 0,9 %). |
| `compliance_explanation` | `str \| None` | Résumé du verdict en anglais simple. |
| `by_methodology` | `dict[str, dict]` | Répartition par méthodologie indexée par `"AAOIFI"`, `"DJIM"`, `"FTSE"`, `"MSCI"`, `"SP500S"`. |
| `disclaimers` | `list[Disclaimer]` | Texte de conformité intégré. |
| `raw` | `dict` | Réponse API complète pour les champs pas encore promus en attributs typés. |

**`Quote`**

| Attribut | Type | Description |
|-----------|------|-------------|
| `symbol` | `str` | Symbole du ticker. |
| `name` | `str` | Nom de l'entreprise. |
| `price` | `float` | Dernier prix. |
| `change` | `float` | Variation absolue du prix. |
| `change_percent` | `float` | Variation en pourcentage. |
| `volume` | `int` | Volume d'échanges. |
| `market_cap` | `float \| None` | Capitalisation boursière (peut être `None` pour les petites actions). |
| `disclaimers` | `list[Disclaimer]` | Texte intégré sur la fraîcheur des données. |
| `raw` | `dict` | Réponse API complète. |

**`ZakatResult`**

| Attribut | Type | Description |
|-----------|------|-------------|
| `total_market_value` | `float` | Somme de toutes les valeurs de marché des participations. |
| `nisab_threshold` | `float` | Nisab dans la même devise que les participations. |
| `is_above_nisab` | `bool` | Indique si la zakat est due (`total_market_value >= nisab_threshold`). |
| `total_zakat` | `float` | Montant de zakat (2,5 % des actifs éligibles si au-dessus du nisab, sinon 0). |
| `disclaimers` | `list[Disclaimer]` | Avertissements religieux et de calcul. |
| `raw` | `dict` | Réponse API complète incluant le détail par participation. |

**`PortfolioScanResult`**

| Attribut | Type | Description |
|-----------|------|-------------|
| `total` | `int` | Nombre total de symboles analysés. |
| `compliant_count` | `int` | Nombre de symboles conformes. |
| `non_compliant_count` | `int` | Nombre de symboles non conformes ou questionnables. |
| `disclaimers` | `list[Disclaimer]` | Texte de conformité intégré. |
| `raw` | `dict` | Réponse API complète incluant `raw["results"]` pour le détail par symbole. |

**`Disclaimer`**

| Attribut | Type | Description |
|-----------|------|-------------|
| `id` | `str` | Identifiant lisible par machine (par exemple `"screening"`, `"zakat"`). |
| `text` | `str` | Texte d'avertissement lisible par un humain. |
| `url` | `str` | Lien profond vers la section spécifique de la page légale. |
| `version` | `str` | Chaîne de date ISO - évolue à chaque modification du texte. |
| `lang` | `str` | Code de langue (actuellement toujours `"en"`). |
| `severity` | `str` | `"religious"` (avertissements de fatwa/érudits) \| `"data"` (fraîcheur/source). |

### Classes d'erreur

Toutes les exceptions héritent de `HalalTerminalError` et portent `.status_code`, `.code` et `.detail`.

| Exception | Statut HTTP | Déclencheur |
|-----------|-------------|---------|
| `ApiKeyError` | 401 / 403 | Clé manquante, invalide, expirée ou désactivée. |
| `NotFoundError` | 404 | Symbole ou ressource introuvable. |
| `QuotaExceededError` | 429 (`QUOTA_EXCEEDED`) | Quota mensuel de jetons épuisé. `.detail` contient l'indication de mise à niveau. |
| `RateLimitError` | 429 (autre) | Limiteur de débit en amont. Réessayez avec backoff. |
| `ServerError` | 5xx | Échec côté serveur. Réessai sécurisé avec backoff exponentiel. |
| `HalalTerminalError` | tout autre 4xx | Filet de sécurité pour les réponses non-2xx inattendues. |

---

## Utilisation asynchrone

Le SDK est synchrone. Pour l'utiliser dans une application asynchrone, exécutez les appels bloquants dans un pool de threads :

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

Ou utilisez `asyncio.to_thread` (Python 3.9+) :

```python
result = await asyncio.to_thread(ht.screen, "AAPL")
```

---

## Tests

La suite de tests est entièrement hors ligne - HTTP est simulé via [`responses`](https://github.com/getsentry/responses) :

```bash
pip install -e ".[dev]"
pytest
```

Pour injecter une `requests.Session` personnalisée (par exemple pour des tests d'intégration contre un serveur de staging) :

```python
import requests
from halalterminal import Client

session = requests.Session()
session.verify = False   # staging cert, for example
ht = Client(api_key="ht_staging_…", base_url="https://staging.api.halalterminal.com", session=session)
```

---

## En savoir plus

- [Référence API](https://api.halalterminal.com/api-reference)
- [Guide de screening des sukuk](https://www.halalterminal.com/research/sukuk-screening)
- [Comparaison des ETF conformes à la sharia (2026)](https://www.halalterminal.com/research/sharia-etf-comprehensive-analysis)
- [Mon action est-elle halal ? Screener](https://www.halalterminal.com/stocks)

## Fait partie de l'écosystème Halal Terminal

[Website](https://www.halalterminal.com) · [API](https://api.halalterminal.com/api-reference) · [JS SDK](https://github.com/goww7/halalterminal-sdk-js) · [MCP server](https://github.com/goww7/halalterminal-mcp) · [Claude plugin](https://github.com/goww7/halalterminal-claude-skills) · [Discord bot](https://github.com/goww7/halal-discord-bot) · [TradingView indicator](https://github.com/goww7/halal-pine) · [Portfolio tracker](https://github.com/goww7/halal-portfolio-tracker)

## Licence

MIT. © Halal Terminal. Voir [LICENSE](LICENSE).

---

Fait partie de l'[Halal Terminal open ecosystem](https://github.com/goww7/awesome-islamic-finance) :
[API](https://api.halalterminal.com) · [MCP server](https://github.com/goww7/halalterminal-mcp) · [Python SDK](https://github.com/goww7/halalterminal-sdk-python) · [JS SDK](https://github.com/goww7/halalterminal-sdk-js) · [Datasets](https://github.com/goww7/sp500-shariah-compliance) · [Awesome Islamic Finance](https://github.com/goww7/awesome-islamic-finance)