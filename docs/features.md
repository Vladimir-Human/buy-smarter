# Features in detail

Back to the [README](../README.md).

- **Kazakh marketplaces.** General assistants (ChatGPT shopping, Perplexity, Google AI Mode) barely see Kaspi
  or OLX.kz. buy-smarter reads their JSON endpoints directly and survives one source going down.
- **Ratings get gamed.** Review trust looks at the five-star share across the full distribution, bursts of
  reviews on the same dates, junk texts ("haven't tried it yet", "courier was fast"), unverified purchases
  and defect complaints. Then it discounts the reviews axis accordingly.
- **Your requirements are checked, not assumed.** A required feature the specs don't confirm is checked
  against reviews. The quote must exist verbatim in a review and appear at least twice, or the verdict stays
  "not enough data".
- **Brand and model knowledge.** Brand tiers and model aliases are seeded for water flossers. Any other
  category gets them via `learn-category`, so "me 705" on OLX resolves to "Xiaomi Water Flosser 2". Without it,
  every brand ranks as unknown: run `learn-category "смартфон"` once before phone queries. Knowledge goes to
  the local store.
- **Auto-learning.** A query for a category with no knowledge anywhere learns it first (opus with web search,
  1-3 minutes, paid), then searches with it. The desktop app shows the learning with a timer: "Искать без
  изучения" searches now while it goes on, "Отмена" stops both. The CLI offers the same choices on a terminal:
  learn first (default) or search now while it learns, then repeat the search; `--learn` learns first without
  asking, also off a terminal. A failed learn searches without the
  knowledge. MCP (with `parse_with_llm`) learns in the background after the report: repeat the query once it is
  done. At most 10 starts per hour (`BUYSMARTER_AUTO_LEARN_PER_HOUR`); `0` turns auto-learning off, and the
  report says so. The API never learns on its own unless `BUYSMARTER_AUTO_LEARN=true`.
- **How the category is judged.** Every report says which capabilities took part and who decided ("Как
  оценивали: состав — обучение"); the desktop app lets you switch a category capability on or off for your
  query's category, or reset it to automatic, on the report and on the «Категории» screen (`buysmarter
  category set/reset` in the CLI). That screen also lists the learned categories with their summary and
  learns or relearns one, with or without web search or from your notes, as `learn-category` and `learn`. "Рынок б/у" (OLX) and "Официальные магазины" (brand sites) are
  such switches too: on by default, off for a category when learning or you say so.
- **Used goods.** A query like "б/у ноутбук" ("только б/у") adds OLX by itself, even if you did not tick it, and
  puts the OLX section first in the CLI, the desktop app and the markdown report (CLI, MCP, API).
- **Phone specs from Kimovil.** For smartphone queries each model is looked up on Kimovil: its overall index
  (0–100) goes into the specs axis ("Kimovil 83/100"), and refresh rate, battery, fast charging, chipset, AnTuTu
  and IP rating are added in Kaspi's wording, so "120 Гц" or "5000 мАч" as a required feature can match. Results
  are cached in `~/.cache/buysmarter/kimovil.db` (30 days; misses 7 days).
- **Price history.** `refresh` and `history` record price and review-count snapshots per product.
  Kaspi has no public Keepa-style tracker.

Closest open-source projects and what was borrowed from them: [docs/analogs](analogs/README.md).
