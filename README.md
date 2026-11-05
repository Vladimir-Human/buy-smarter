**English** | **[Русский](README.ru.md)**

<p align="center">
  <img src="./assets/readme/hero.svg" width="100%" alt="buy-smarter: describe what you need, get offers from Kaspi, Ozon and OLX ranked for your budget and city. A real best pick scores 66 of 100, with a bar for each axis: ingredient 25/25, brand 1.5/10, price 11/25, reviews 3.4/12, specs 15/15, popularity 0.3/3, availability 10/10.">
</p>

[![CI](https://github.com/octrow/buy-smarter/actions/workflows/ci.yml/badge.svg)](https://github.com/octrow/buy-smarter/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)

Ranks Kaspi, Ozon and OLX offers for your budget and city, and shows why.

You describe what you need ("a portable water flosser, IPX7, under 40,000 ₸, Almaty").
buy-smarter searches Kaspi.kz, Ozon.kz and OLX.kz (used items).
It ranks offers for your budget, city and must-have features.
Each pick shows which axes scored it and why.

It runs as a CLI, a desktop app, an MCP server for Claude and an HTTP API.

## Quick start

Kaspi needs a Kazakhstan IP: datacenter IPs get HTTP 429 (set `KASPI_PROXY` to a residential proxy).

macOS / Linux:

```bash
curl -LsSf https://raw.githubusercontent.com/octrow/buy-smarter/main/install.sh | sh
```

Windows (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/octrow/buy-smarter/main/install.ps1 | iex"
```

The installer gets [uv](https://docs.astral.sh/uv/) (it brings its own Python), installs the latest release with the desktop app, and runs `buysmarter doctor`.
`doctor` says what is missing and what that turns off.
Update with `buysmarter update`. Remove with `sh -s -- --uninstall`.
API keys and a proxy go in `~/.config/buysmarter/.env` (see [.env.example](.env.example)).

Then run your first search:

```bash
buysmarter recommend "need a water flosser, portable, IPX7, under 40000 tg, Almaty"
```

No terminal? Each release has a `.deb` and builds for Windows, macOS and Linux: [install the desktop app](docs/install-desktop.md).
Developing? See [install from source](docs/development.md).

## What the app looks like

The desktop app (`buysmarter gui`) opens the same reports and has a dark theme.

<table>
  <tr>
    <td width="50%"><img src="./assets/readme/desktop-report.png" alt="Desktop app, light theme, Past searches screen: four real runs on the left (water flosser under 40,000, smartphone under 150,000, robot vacuum, adapalene cream); on the right the water flosser report, best pick Xiaomi Mijia Electric Flusher 2 MEO705 on Kaspi, 62 of 100, 15,562 tenge, with a table of axis scores and the reason for each."></td>
    <td width="50%"><img src="./assets/readme/desktop-search-dark.png" alt="Desktop app, dark theme, Search screen: a query field, city and budget, marketplace checkboxes Kaspi, Ozon (unavailable without Chrome) and OLX, options for AI query parsing, review summary and known brands only, and the recent searches with a Repeat button."></td>
  </tr>
</table>

## What it does

- Reads the Kaspi and OLX JSON endpoints directly, and keeps working when one source is down.
- Discounts gamed reviews: five-star bursts, junk texts, unverified purchases, defect complaints.
- Checks your must-have features against specs, then against review quotes.
- Learns brands and models for a new category (`learn-category`), also on the first query.
- Adds used items from OLX, phone specs from Kimovil and price history.

More in [features in detail](docs/features.md). Closest open-source projects: [analogs](docs/analogs/README.md).

## How it runs

One pipeline sits behind the CLI, the MCP server and the API.
A run takes tens of seconds.
The API puts it on a Redis stream, a worker runs it, and the client polls for the result.

```mermaid
flowchart TD
    client([client]) -->|"POST /recommend, GET /recommend/{id}"| api[FastAPI]
    api -->|"job, dedupe, rate limit"| redis[(Redis)]
    redis -->|"stream, ack after the run"| worker[taskiq worker]
    worker -->|result| redis
    worker -->|"search, offers, reviews"| markets[Kaspi · Ozon · OLX]
    worker -->|price history| pg[(Postgres)]
    api -.->|metrics, traces| obs[Prometheus · Grafana · Jaeger]
    worker -.-> obs
```

## More docs

- [CLI usage and LLM cache](docs/usage.md)
- [MCP server](docs/mcp.md): tools and Claude Desktop setup
- [HTTP API](docs/http-api.md): jobs, statuses, rate limits
- [Docker, Kubernetes, observability](docs/deploy.md), with Grafana and Jaeger screenshots
- [Development](docs/development.md): `make check`, layout, tests

## Limits

- Kaspi needs a Kazakhstan residential IP or `KASPI_PROXY`.
- Ozon may still show its anti-bot page; `ozon-setup` refreshes the saved session.
- Review velocity is displayed but not scored yet.
- A burst of requests can get the IP blocked by Kimovil for a while.
  Until it clears, only cached phone specs are used.
- The marketplace endpoints are unofficial and can change without notice.

## License

[MIT](LICENSE). Third-party code is listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
