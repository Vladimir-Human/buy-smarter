# MCP-сервер

Назад в [README](../README.ru.md).

buy-smarter работает и как MCP-сервер (fastmcp, stdio). Подключённый Claude ведёт разговор и передаёт
структурированные аргументы (город, бюджет). Инструменты — тонкие обёртки над теми же слоями service и
render, что и CLI.

```bash
uv run python -m buysmarter.mcp_server   # блокируется на stdio; обычно его запускает клиент
```

**Claude Code** подхватит `.mcp.json` из корня репозитория. Для **Claude Desktop** добавьте в
`claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "buy-smarter": {
      "command": "uv",
      "args": ["run", "python", "-m", "buysmarter.mcp_server"],
      "cwd": "/path/to/buy-smarter"
    }
  }
}
```

| Инструмент | Назначение |
|---|---|
| `recommend` | Полный пайплайн → markdown-отчёт (лучший выбор с осями, альтернативы, топ-N, б/у на OLX). Параметры: `query`, `city`, `budget`, `sources`, `trusted_only`, `top`, `parse_with_llm` (по умолчанию `False`: Claude сам разбирает запрос), `answer`, `clarify_round`, `no_clarify`. На неоднозначный запрос возвращает вопрос с вариантами: спросите человека и вызовите снова с `answer` и указанным `clarify_round`. |
| `search_products` | Сырой поиск по одной площадке без ранжирования (title, price, rating, url). |
| `compare` | 2–4 товара через запятую → сравнение спецификаций (Kaspi). |
| `get_preferences` / `set_preference` | Чтение и запись предпочтений (город, бюджет…). Хранятся в локальном хранилище. |
