# HTTP API

Назад в [README](../README.ru.md).

API ставит подбор в очередь, а выполняет его воркер (taskiq поверх Redis Streams): один подбор идёт десятки секунд.
OpenAPI — на `/docs`.

```bash
curl -s -X POST localhost:8000/recommend -H 'content-type: application/json' \
  -d '{"query": "ирригатор до 40000", "sources": ["kaspi"]}'
# 202 {"job_id": "…", "status": "queued", "status_url": "/recommend/…"}
curl -s localhost:8000/recommend/<job_id>
# {"status": "done", "result": {"report_markdown": "…", "best": {…}, "alternatives": {…}, …}}
curl -s 'localhost:8000/history?q=wp-100'
```

- Статусы: `queued` → `running` → `done`, `no_match` (нужного вещества нет ни в одном товаре или фильтры никого не
  пропустили) или `failed` (`timeout`, `internal`). Задачи хранятся 24 часа.
- Запрос, которому нужно уточнение, заканчивается `no_match` с `result.reason = "needs_clarification"` и
  `result.clarification` (`kind`, `question`, `options`, `round`, `restricted_note`). Спросите пользователя и
  отправьте запрос снова с `answer` (вариант или свои слова) и `clarify_round` = `round` + 1 (не больше 2);
  `no_clarify: true` вместо вопроса ищет первый вариант. `result.constraints` показывает разбор (`intent`,
  `search_phrase`, `product_type`, …); его `category` — устаревшая копия `search_phrase`.
- Тот же запрос в течение 15 минут возвращает ту же задачу (200). Клиент может запустить 10 новых задач за 10 минут,
  дальше 429 с `Retry-After` (`BUYSMARTER_RATE_LIMIT_JOBS`, `BUYSMARTER_RATE_LIMIT_WINDOW_S`).
- Автообучение в API выключено: `BUYSMARTER_AUTO_LEARN=true` ставит после задания по новой категории
  отдельную задачу `buysmarter.learn_category` (раз на категорию, лимит 600 с, `BUYSMARTER_AUTO_LEARN_PER_HOUR`).
  `result.assessed_by` — какие возможности работали и кто это решил.
- `BUYSMARTER_API_KEYS=k1,k2` требует заголовок `X-API-Key`. `BUYSMARTER_SOURCES` — какие площадки принимает API:
  по умолчанию `kaspi,olx`, `ozon` требует воркер с Chromium.
- Воркер, упавший посреди подбора, ничего не теряет: его задачу заберёт другой воркер через два таймаута задачи
  (`BUYSMARTER_JOB_TIMEOUT_S`, по умолчанию 600 с).
- С облачных IP площадки часто отказывают (Kaspi отвечает 429 адресам датацентров, см. `KASPI_PROXY`), поэтому там
  большинство задач закончится `no_match` или `failed`.
