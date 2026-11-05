# Docker, Kubernetes, наблюдаемость

Назад в [README](../README.ru.md).

<p align="center">
  <img src="../assets/readme/api-demo.gif" width="100%" alt="Терминал: POST /recommend на портативный ирригатор IPX7 до 38 000 тенге возвращает job id со статусом queued. Опрос задачи позже показывает статус done, лучший вариант Xiaomi Mijia Electric Flusher 2 MEO705 за 15 999 тенге с Kaspi с оценкой 65.78 и начало markdown-отчёта.">
</p>

`make observe` добавляет к compose-стеку Prometheus, Grafana и Jaeger. Скриншоты ниже сняты после девяти настоящих
задач: дашборд с панелями HTTP, площадок, ранжирования и очереди и одна задача одним трейсом, от `POST /recommend`
через воркер до запросов в Postgres и HTTP-запросов к площадкам.

<p align="center">
  <img src="../assets/readme/grafana.png" width="100%" alt="Дашборд Grafana buy-smarter за последние 30 минут: запросы по маршрутам, p95 задержки, поиски по площадкам Kaspi и OLX по исходу, вызовы LLM (в этом прогоне их нет), p95 длительности подбора около 45 секунд, около 12 кандидатов в рейтинге и ряд Queue с завершёнными задачами и p95 ожидания в очереди около 5 секунд.">
</p>
<p align="center">
  <img src="../assets/readme/jaeger.png" width="100%" alt="Трейс Jaeger buysmarter: POST /recommend, 43,8 секунды, 426 спанов. Спан POST (202) ведёт к спану отправки taskiq и спану выполнения в воркере, внутри которого спаны подключения и SELECT к Postgres, а за ними ряд HTTP GET 200 по 350–730 миллисекунд.">
</p>

Каждый PR гоняет тесты, собирает образ (не root, healthcheck), поднимает compose-стек и ставит, тестирует и
обновляет Helm-чарт в kind с одной задачей от начала до конца. Подробнее — в разделах [HTTP API](http-api.ru.md),
[Kubernetes](#kubernetes) и [Наблюдаемость](#наблюдаемость).

## Docker

```bash
docker compose up -d --build        # Postgres, Redis, миграции, API на :8000, воркер; ключи берутся из .env
docker compose run --rm app buysmarter recommend "…" --budget 30000
docker compose -f docker-compose.yml -f docker-compose.browser.yml up -d --build   # воркер с Chromium: Ozon
docker compose down                 # с -v удалит и данные
```

Готовые образы: `ghcr.io/octrow/buy-smarter:latest` (релизы), `:main` (каждый коммит в main), суффикс `-browser`
для Chromium. `TAG=main docker compose pull && docker compose up -d` запускает их без сборки.
Происхождение образа: `gh attestation verify oci://ghcr.io/octrow/buy-smarter:latest -R octrow/buy-smarter`.

В образе нет `claude` CLI: LLM работает через API-фолбэк (`DEFAULT_LLM_MODEL` и ключ провайдера в `.env`).
Без compose: `docker build -t buysmarter .` (`--target browser` для Chromium), затем `alembic upgrade head` из того же
образа перед запуском API.

## Kubernetes

Helm-чарт лежит в [`deploy/helm/buysmarter`](../deploy/helm/buysmarter): API, воркер (`worker.browser=true` для Ozon) и
Job миграций. Postgres и Redis свои (managed или в кластере):

```bash
helm install buysmarter deploy/helm/buysmarter -n buysmarter --create-namespace \
  --set secret.data.DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/buysmarter \
  --set secret.data.REDIS_URL=redis://host:6379/0
helm test buysmarter -n buysmarter
```

Миграции идут Job'ом-хуком pre-install/pre-upgrade, один раз на релиз. Пробы: `/health` (liveness, без зависимостей)
и `/ready` (readiness, 503, пока не отвечает БД). Поды проходят Pod Security Standard `restricted`. Ключи — в
`secret.data` или в своём Secret (`secret.existing`). CI ставит и обновляет чарт в kind на каждом PR
и прогоняет одну задачу через API → Redis → воркер ([`deploy/kind/smoke.sh`](../deploy/kind/smoke.sh)); проверяется
проводка, а не рейтинг: площадки могут не отвечать трафику из CI.

## Наблюдаемость

API отдаёт метрики Prometheus на `GET /metrics`, воркер — на `:9000/metrics` (OpenTelemetry SDK с Prometheus-экспортером): частота и задержка
HTTP-запросов по маршрутам, а также `buysmarter_recommend_duration_seconds` (по исходу),
`buysmarter_source_requests_total` (по площадке и исходу), `buysmarter_llm_calls_total` (по модели, попадание в кэш или
промах) и `buysmarter_recommend_offers_ranked`, а также очередь: `buysmarter_jobs_total` (по статусу),
`buysmarter_job_wait_seconds` и `buysmarter_rate_limited_total`. Один трейс ведёт задачу от `POST /recommend` через воркер. С `OTEL_EXPORTER_OTLP_ENDPOINT` уходят ещё и трейсы (FastAPI, httpx-запросы
к площадкам, SQL) по OTLP/HTTP; `BUYSMARTER_METRICS=0` выключает `/metrics`.

```bash
make observe   # compose-стек + Prometheus :9090, Grafana :3000 (дашборд «buy-smarter»), Jaeger :16686
```

В чарте — аннотации `prometheus.io/scrape`, опциональный `ServiceMonitor` (`metrics.serviceMonitor.enabled`) и
`otel.endpoint` для трейсов.
