**[English](README.md)** | **Русский**

<p align="center">
  <img src="./assets/readme/hero.ru.svg" width="100%" alt="buy-smarter: опишите, что нужно, и получите предложения с Kaspi, Ozon и OLX под ваш бюджет и город. Лучший вариант из реального запуска набрал 66 из 100, с полосой по каждой оси: ingredient 25/25, brand 1.5/10, price 11/25, reviews 3.4/12, specs 15/15, popularity 0.3/3, availability 10/10.">
</p>

[![CI](https://github.com/octrow/buy-smarter/actions/workflows/ci.yml/badge.svg)](https://github.com/octrow/buy-smarter/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)

Ранжирует предложения Kaspi, Ozon и OLX под ваш бюджет и город и объясняет выбор.

Вы описываете, что нужно («портативный ирригатор, IPX7, до 40 000 тг, Алматы»).
buy-smarter ищет на Kaspi.kz, Ozon.kz и OLX.kz (б/у) и ранжирует предложения под ваш бюджет, город и обязательные функции.
Для каждого варианта видно, по каким осям он набрал баллы и почему, и что проверить не удалось.
Работает как CLI, десктоп-приложение, MCP-сервер для Claude и HTTP API.

## Быстрый старт

Для Kaspi нужен казахстанский IP: датацентровым IP он отвечает HTTP 429 (задайте `KASPI_PROXY` с резидентным прокси).

macOS / Linux:

```bash
curl -LsSf https://raw.githubusercontent.com/octrow/buy-smarter/main/install.sh | sh
```

Windows (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/octrow/buy-smarter/main/install.ps1 | iex"
```

Установщик ставит [uv](https://docs.astral.sh/uv/) (он сам принесёт Python), последний релиз с десктоп-приложением и запускает `buysmarter doctor`.
`doctor` скажет, чего не хватает и что от этого отключится.
Обновление: `buysmarter update`. Удаление: `sh -s -- --uninstall`.
API-ключи и прокси кладутся в `~/.config/buysmarter/.env` (образец в [.env.example](.env.example)).

Затем запустите первый поиск:

```bash
buysmarter recommend "нужен ирригатор, портативный, IPX7, до 40000 тг, Алматы"
```

Без терминала? В каждом релизе есть `.deb` и сборки для Windows, macOS и Linux: [установка приложения](docs/install-desktop.ru.md).
Разработка? См. [установку из исходников](docs/development.ru.md).

## Как выглядит приложение

Десктоп-приложение (`buysmarter gui`) открывает те же отчёты, есть тёмная тема.

<table>
  <tr>
    <td width="50%"><img src="./assets/readme/desktop-report.png" alt="Десктоп-приложение, светлая тема, экран «Прошлые поиски»: слева четыре реальных запуска (ирригатор до 40 000, смартфон до 150 000, робот-пылесос, крем с адапаленом); справа отчёт по ирригатору, лучший выбор Xiaomi Mijia Electric Flusher 2 MEO705 на Kaspi, 62 из 100, 15 562 тенге, с таблицей баллов по осям и причиной для каждой."></td>
    <td width="50%"><img src="./assets/readme/desktop-search-dark.png" alt="Десктоп-приложение, тёмная тема, экран «Поиск»: поле запроса, город и бюджет, флажки площадок Kaspi, Ozon (недоступен без Chrome) и OLX, опции AI-разбора запроса, сводки отзывов и только известных брендов, и недавние поиски с кнопкой «Повторить»."></td>
  </tr>
</table>

## Что умеет

- Читает JSON-эндпоинты Kaspi и OLX напрямую и работает, даже если один источник недоступен.
- Занижает вес накрученных отзывов: всплески пятёрок, мусорные тексты, непроверенные покупки, жалобы на брак.
- Проверяет ваши обязательные функции по характеристикам, затем по цитатам из отзывов.
- Изучает бренды и модели новой категории (`learn-category`), в том числе при первом запросе.
- Добавляет б/у с OLX, характеристики телефонов с Kimovil и историю цен.

Подробнее: [возможности](docs/features.ru.md). Ближайшие открытые проекты: [аналоги](docs/analogs/README.md).

## Как это работает

За CLI, MCP-сервером и API стоит один пайплайн.
Подбор идёт десятки секунд, поэтому API кладёт его в Redis Stream, выполняет воркер, а клиент опрашивает результат.

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

## Ещё документация

- [CLI и кэш LLM](docs/usage.ru.md)
- [MCP-сервер](docs/mcp.ru.md): инструменты и настройка Claude Desktop
- [HTTP API](docs/http-api.ru.md): задачи, статусы, лимиты
- [Docker, Kubernetes, наблюдаемость](docs/deploy.ru.md), со скриншотами Grafana и Jaeger
- [Разработка](docs/development.ru.md): `make check`, структура, тесты

## Ограничения

- Для Kaspi нужен резидентный казахстанский IP или `KASPI_PROXY`.
- Ozon может показать антибот-страницу; `ozon-setup` обновляет сохранённую сессию.
- Скорость появления отзывов показывается, но пока не входит в оценку.
- Kimovil после всплеска запросов может на время заблокировать IP; тогда используются только кэшированные характеристики телефонов.
- Эндпоинты площадок неофициальные и могут измениться без предупреждения.

## Лицензия

[MIT](LICENSE). Сторонний код перечислен в [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
