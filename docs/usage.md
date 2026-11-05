# CLI usage and LLM cache

Back to the [README](../README.md).

```bash
# LLM request parsing via the claude-cli library (no API key needed)
buysmarter recommend "need a water flosser, portable, IPX7, under 40000 tg, Almaty"

# Saved search settings, the app's «Настройки поиска»: city, budget, marketplaces, excluded brands
buysmarter prefs
buysmarter prefs set marketplaces kaspi,olx
buysmarter prefs set excluded_brands "Noname, Generic"
buysmarter prefs clear budget

# Clothing taste («Стиль» in the app; needs the `style` extra for photos)
buysmarter style
buysmarter style add ~/style/like                # photos or folders; --no for what you never want
buysmarter style brands "Salomon, New Balance"   # searched on Kaspi for clothing
buysmarter style strength 30                     # the «Стиль» axis weight; 0 = off, 20 by default
buysmarter style never "белая глянцевая пластиковая подошва"   # translated by the LLM once
buysmarter style remove 3f2a9c1d0e4b5a67.jpg
buysmarter style like https://kaspi.kz/shop/p/...   # a found product's photo as a sample; dislike for «нет»

# The saved marketplaces (else all three) or a subset; more candidates; no markdown report
buysmarter recommend "ирригатор до 40000 тг" --sources kaspi,olx --top 10 --no-save

# Trusted brands only; no LLM (naive parser, features are not filtered)
buysmarter recommend "ирригатор" --city Алматы --budget 40000 --trusted-only --no-llm

# Category knowledge: generate it (opus) or extract it from your own notes (sonnet)
buysmarter learn-category "робот-пылесос"
buysmarter learn-category "смартфон"      # brand tiers + model aliases for phones
buysmarter learn ~/notes/robot-vacuum.md --category "робот пылесос"

# Learned categories, the app's «Категории»: list, summary, how a category is judged
buysmarter category list
buysmarter category show "робот-пылесос"
buysmarter category set "робот-пылесос" used_market off   # composition, benchmark, official_stores
buysmarter category reset "робот-пылесос" used_market

# Smartphones: Kimovil index in the specs axis, "120 Гц" / "5000 мАч" as required features
buysmarter recommend "смартфон до 250000 тг, 120 Гц, 5000 мАч" --city Алматы

# Price history: re-scan tracked categories, list the recent products, then look up one
buysmarter refresh
buysmarter history
buysmarter history "F300"

# Past searches, the app's «Прошлые поиски»: list, read one, search it again
buysmarter reports
buysmarter reports show 1
buysmarter reports repeat 1
```

Output: the best pick with a score out of 100, confidence, a per-axis breakdown (brand, price with a 30-day
trend, reviews, specs, popularity, availability with the delivery date), a review summary
(pros, cons, frequent complaints, requirement checks), alternatives, the top N with links and the
OLX used section. Reports are saved to `~/.local/share/buysmarter/reports/` (`--no-save` turns that off), logs
go to `~/.cache/buysmarter/logs/buysmarter.log` (`BUYSMARTER_LOG_FILE` moves it). Nothing is written to the
folder you run it from.

Sources: **Kaspi** (JSON endpoints), **Ozon.kz** (Playwright browser session), **OLX.kz** (open REST,
used items). Accessories and off-topic listings are dropped by a heuristic filter with an LLM fallback.
In the used section, defects the seller admits to in the ad text (cracks, "doesn't turn on", water damage, weak
battery, past repairs) are listed under Con, and ads sold for parts are dropped.
Ranking also discounts reviews of unknown brands and penalizes suspiciously low prices.

**Request understanding.** Before any search the request is read for what kind of request it is. An ambiguous one
gets a question instead of a ranking: "подарок для мамы" asks what to look for, "iPhone 15 или S24" asks which one
to start with, "ремонт телефона" says it is a service, "аыавыа" asks to rephrase. On a terminal you pick a number or
type your own answer; at most two rounds, then the first option is searched and the report says so ("Искал: …").
`--no-clarify` never asks. Restricted goods (alcohol, tobacco and vapes, weapons, prescription medicines with an
LLM) are searched with a warning on the first line, never refused. Budgets are read by rules that never take a unit
for money: "до 50 штук" is 50 000 ₸, "до 2 м" or "4K" is no budget, "$500" adds a note instead.

Exit codes of `recommend`: `0` a recommendation (or OLX ads when no new product fits), `1` nothing to recommend
(including "nothing to search" after the last clarification round), `2` a marketplace request failed, `3` the request
needs a clarification and stdin is not a terminal (the question is printed).

## LLM: models and cache

All LLM calls go through [claude-cli](https://github.com/octrow/claude-cli): an OmniRoute gateway when one is
configured, otherwise the local `claude` CLI. Each task uses a fixed model: a cheap one for request parsing,
review summaries and classification fallbacks; sonnet for extracting knowledge from files; opus for
generating category knowledge. Every request/response pair is cached, so a repeat call is a free cache hit:

```bash
sqlite3 ~/.cache/buysmarter/llm_cache.db \
  "SELECT model, substr(cache_key,1,8), cost_usd, created_at FROM llm_cache ORDER BY created_at DESC LIMIT 10;"
grep "llm cache" ~/.cache/buysmarter/logs/buysmarter.log   # hit/miss for every call
```
