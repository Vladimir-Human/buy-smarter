# Разработка и установка из исходников

Назад в [README](../README.ru.md).

Из исходников, для разработки ([uv](https://docs.astral.sh/uv/); Docker нужен только для серверного стека):

```bash
git clone https://github.com/octrow/buy-smarter && cd buy-smarter
uv sync
uv run buysmarter doctor      # скажет, чего не хватает и что от этого отключится

# По желанию
uv sync --extra server && make up        # стек HTTP API: Postgres :5434 + Redis :6380 (см. .env.example)
uv run playwright install chromium       # источник Ozon
uv sync --extra style                    # подбор одежды по вкусу: ONNX-модель на CPU
uv run buysmarter ozon-setup             # один раз пройти антибот Ozon в видимом браузере
cp .env.example .env                     # необязательные API-ключи и прокси
```

История цен, предпочтения и выученные категории лежат в **локальном хранилище** — файле SQLite в папке данных
пользователя (`~/.local/share/buysmarter/buysmarter.db` в Linux), он создаётся при первом запуске. Где он, показывает
`doctor`. Остальное по желанию: без `claude` CLI режим `--no-llm` использует простой парсер. В клоне перед командами ниже добавляйте `uv run`.

## Разработка

```bash
make check   # ruff + pytest (не нужны ни сеть, ни сервер БД)
make test
make up / make down
```

Структура: `src/buysmarter/{normalize,db,llm,ranking,services,cli,knowledge,mcp_server,api}`, а также `jobs.py`
(задачи в Redis), `worker.py` (воркер taskiq) и `telemetry.py`; в `deploy/` — Helm-чарт, kind-smoke и конфиги
наблюдаемости. Адаптеры площадок
вынесены в отдельную библиотеку [market-sources](https://github.com/octrow/market-sources)
(`kaspi`/`olx`/`ozon` поверх вежливого HTTP-клиента и сессии Playwright). Тесты парсеров идут на сохранённых
JSON-сэмплах в `tests/samples/`. Заметки по разведке источников — в [docs/spikes](spikes).
