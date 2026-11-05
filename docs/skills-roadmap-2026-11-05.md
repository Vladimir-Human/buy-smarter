# Навыки с рынка: что добавить (2026-11-05)

Источник: `~/dev/jobs/data/corpus_roadmap.md` (11.5k вакансий, 2026-11-05) против [system-design](system-design.md) и [logic-map](logic-map.md). Берём только то, что нужно самому проекту; чего проект не требует — в «Отвергнуто». Сводка по всем репо: `~/dev/docs/skills-roadmap-report-2026-11-05.md`.

## Предложения

- [ ] **[terraform, cloud, ci/cd]** Terraform + cloud-init для OCI Always Free ARM: поднять существующий `docker-compose.yml` как живой демо-URL. «Отложено» блокирует демо пунктом «нужны деньги», Always Free снимает эту причину. Секреты и юр. риск — решение владельца. Ценность — демо и навык, не нагрузка. Усилие M.

## Отвергнуто

- Уже есть, не дублировать: compose, GHCR, Helm+kind, OTel/Prometheus, MCP, Postgres+Redis+taskiq, CodeQL.
- pgvector для `style_vectors`: 615 строк, numpy хватает.
- RAG по отзывам: в `reviews` 0 строк.
