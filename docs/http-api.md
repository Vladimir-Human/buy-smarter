# HTTP API

Back to the [README](../README.md).

The API queues a recommend run and a worker executes it (taskiq on a Redis stream), because one run takes tens of
seconds. OpenAPI lives at `/docs`.

```bash
curl -s -X POST localhost:8000/recommend -H 'content-type: application/json' \
  -d '{"query": "ирригатор до 40000", "sources": ["kaspi"]}'
# 202 {"job_id": "…", "status": "queued", "status_url": "/recommend/…"}
curl -s localhost:8000/recommend/<job_id>
# {"status": "done", "result": {"report_markdown": "…", "best": {…}, "alternatives": {…}, …}}
curl -s 'localhost:8000/history?q=wp-100'
```

- Statuses: `queued` → `running` → `done`, `no_match` (no product has the required substance, or nothing passed the
  filters) or `failed` (`timeout`, `internal`). Jobs are kept for 24 hours.
- A request that needs a clarification ends as `no_match` with `result.reason = "needs_clarification"` and
  `result.clarification` (`kind`, `question`, `options`, `round`, `restricted_note`). Ask the user and post the
  request again with `answer` (an option or their own words) and `clarify_round` = `round` + 1 (at most 2);
  `no_clarify: true` searches the first option instead. `result.constraints` shows the parse (`intent`,
  `search_phrase`, `product_type`, ...); its `category` is a deprecated copy of `search_phrase`.
- A `no_match` where no new product passed the filters has `result.rejected_reasons` (reason → count) and
  `result.used_listings` (the OLX ads within the budget, possibly empty); `report_markdown` shows both.
- The same request within 15 minutes returns the same job (200). Each client may start 10 new jobs per 10 minutes,
  then gets 429 with `Retry-After` (`BUYSMARTER_RATE_LIMIT_JOBS`, `BUYSMARTER_RATE_LIMIT_WINDOW_S`).
- Auto-learning is off in the API: `BUYSMARTER_AUTO_LEARN=true` queues a separate `buysmarter.learn_category`
  task after a job for a new category (once per category, 600 s limit, `BUYSMARTER_AUTO_LEARN_PER_HOUR`).
  `result.assessed_by` lists the capabilities that took part and who decided.
- `BUYSMARTER_API_KEYS=k1,k2` requires `X-API-Key`. `BUYSMARTER_SOURCES` lists the marketplaces the API accepts:
  `kaspi,olx` by default, `ozon` needs the worker's Chromium image.
- A worker that dies mid-run loses nothing: its job is picked up by another worker after twice the job timeout
  (`BUYSMARTER_JOB_TIMEOUT_S`, 300 s by default).
- From cloud IPs the marketplaces often refuse requests (Kaspi answers 429 to datacenter addresses; see `KASPI_PROXY`),
  so most jobs there end as `no_match` or `failed`.
