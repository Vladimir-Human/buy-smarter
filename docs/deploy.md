# Docker, Kubernetes, observability

Back to the [README](../README.md).

<p align="center">
  <img src="../assets/readme/api-demo.gif" width="100%" alt="Terminal: POST /recommend for a portable IPX7 water flosser under 38,000 tenge returns a job id with status queued. Polling the job later shows status done, the best pick Xiaomi Mijia Electric Flusher 2 MEO705 at 15,999 tenge from Kaspi with score 65.78, and the start of the markdown report.">
</p>

`make observe` adds Prometheus, Grafana and Jaeger to the compose stack. The screenshots below come from nine real
jobs: the dashboard with HTTP, marketplace, ranking and queue panels, and one job as a single trace, from
`POST /recommend` through the worker to the Postgres queries and the marketplace HTTP calls.

<p align="center">
  <img src="../assets/readme/grafana.png" width="100%" alt="Grafana dashboard buy-smarter over the last 30 minutes: requests per route, p95 latency, marketplace searches by outcome for Kaspi and OLX, LLM calls (none in this run), recommend p95 duration around 45 seconds, about 12 ranked offers per run, and a Queue row with finished jobs and about 5 seconds p95 time in queue.">
</p>
<p align="center">
  <img src="../assets/readme/jaeger.png" width="100%" alt="Jaeger trace buysmarter: POST /recommend, 43.8 seconds, 426 spans. The POST span (202) leads to the taskiq send span and the execute span in the worker, which holds Postgres connect and SELECT spans followed by a row of HTTP GET 200 calls of 350 to 730 milliseconds each.">
</p>

Every PR runs the tests, builds the image (non-root, healthcheck), starts the compose stack and installs, tests
and upgrades the Helm chart in kind with one job end to end. More in [HTTP API](http-api.md),
[Kubernetes](#kubernetes) and [Observability](#observability).

## Docker

```bash
docker compose up -d --build        # Postgres, Redis, migrations, API on :8000, worker; keys come from .env
docker compose run --rm app buysmarter recommend "…" --budget 30000
docker compose -f docker-compose.yml -f docker-compose.browser.yml up -d --build   # worker with Chromium: Ozon
docker compose down                 # add -v to drop the data
```

Prebuilt images: `ghcr.io/octrow/buy-smarter:latest` (releases), `:main` (every commit to main), `-browser`
suffix for Chromium. `TAG=main docker compose pull && docker compose up -d` runs them without building.
Check where an image came from with `gh attestation verify oci://ghcr.io/octrow/buy-smarter:latest -R octrow/buy-smarter`.

The image has no `claude` CLI: LLM calls use the API fallback (`DEFAULT_LLM_MODEL` plus a provider key in `.env`).
Without compose: `docker build -t buysmarter .` (`--target browser` for Chromium), then run `alembic upgrade head`
from the same image before the API.

## Kubernetes

A Helm chart lives in [`deploy/helm/buysmarter`](../deploy/helm/buysmarter): the API, the worker (`worker.browser=true`
for Ozon) and the migration Job. Postgres and Redis are yours (managed or in-cluster):

```bash
helm install buysmarter deploy/helm/buysmarter -n buysmarter --create-namespace \
  --set secret.data.DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/buysmarter \
  --set secret.data.REDIS_URL=redis://host:6379/0
helm test buysmarter -n buysmarter
```

Migrations run as a pre-install/pre-upgrade hook Job, once per release. Probes: `/health` (liveness, no
dependencies) and `/ready` (readiness, 503 until the database answers). Pods pass the Pod Security Standard
`restricted`. Keys go in `secret.data` or in your own Secret (`secret.existing`). CI installs and upgrades the chart in
kind on every PR and runs one job through API → Redis → worker ([`deploy/kind/smoke.sh`](../deploy/kind/smoke.sh)); it
checks the wiring, not the ranking, since the marketplaces may refuse CI traffic.

## Observability

The API serves Prometheus metrics on `GET /metrics` and the worker on `:9000/metrics` (OpenTelemetry SDK with the Prometheus exporter): HTTP request
rate and latency by route, plus `buysmarter_recommend_duration_seconds` (by outcome), `buysmarter_source_requests_total`
(by marketplace and outcome), `buysmarter_llm_calls_total` (by model, cache hit or miss) and
`buysmarter_recommend_offers_ranked`, plus the queue: `buysmarter_jobs_total` (by status), `buysmarter_job_wait_seconds`
and `buysmarter_rate_limited_total`. One trace follows a job from `POST /recommend` through the worker. Set `OTEL_EXPORTER_OTLP_ENDPOINT` to also export traces (FastAPI, httpx calls to
the marketplaces, SQL) over OTLP/HTTP; `BUYSMARTER_METRICS=0` turns `/metrics` off.

```bash
make observe   # the compose stack + Prometheus :9090, Grafana :3000 (dashboard "buy-smarter"), Jaeger :16686
```

The chart adds `prometheus.io/scrape` annotations, an optional `ServiceMonitor` (`metrics.serviceMonitor.enabled`) and
`otel.endpoint` for traces.
