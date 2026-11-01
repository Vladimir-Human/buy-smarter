"""OLX recall helpers: the head-noun query and the cheapest-first pages.

OLX's full-text search ANDs terms and sorts by relevance, so a narrow query misses
ads and a broad one shows only its first ~50 of hundreds: a bare noun widens the
first, cheapest-first pages within the ads' own category reach into the second.
"""

import logging
import re
from collections import Counter

from market_sources.base import ProductSource, RawProduct

from buysmarter.knowledge.brands import BrandBook
from buysmarter.services.matching import matches_category_or_stripped

logger = logging.getLogger(__name__)

_OLX_HEAD_NOUN_MIN_LEN = 4  # shortest token treated as a searchable head noun
# Cheapest-first OLX pages within the ads' category: a broad query around a city has
# hundreds of ads and the relevance order shows ~50 (a 55 000 ₸ dishwasher sat at ~260).
_OLX_CHEAPEST = 300


def head_noun(category: str, book: BrandBook | None = None) -> str | None:
    """Last content token of a category (RU/EN head noun), or ``None`` if
    searching it separately would just repeat the exact same query.

    OLX classifieds full-text search ANDs terms, so a multi-word category like
    "портативный ирригатор" returns far fewer ads than the bare noun
    "ирригатор" — we broaden recall by also searching the head noun. Short
    jargon tokens (len < ``_OLX_HEAD_NOUN_MIN_LEN``, e.g. "TWS") are dropped
    before picking the head noun, same reasoning as ``strip_latin_tokens``;
    a SINGLE surviving token still broadens recall whenever it differs from
    the full (lowercased) category string — e.g. "TWS наушники" drops to one
    token, "наушники", which is strictly narrower than the two-word original.

    ``book``, when given, ALSO drops a token that is itself a known brand/
    model name (e.g. "Sony" in "беспроводные наушники Sony", "Dyson" in "фен
    Dyson Supersonic") — searching a bare brand name on OLX with no category
    filter downstream floods the pool with that brand's unrelated catalog
    (docs/PLAN.md "Ranking-фиксы"); the previous non-brand token is used
    instead, falling out naturally once brand tokens are filtered before
    picking the tail.
    """
    lowered_category = category.lower().strip()
    tokens: list[str] = [
        t for t in re.findall(r"[^\W\d_]+", lowered_category) if len(t) >= _OLX_HEAD_NOUN_MIN_LEN
    ]
    if book is not None:
        tokens = [t for t in tokens if book.resolve(t)[0] is None]
    if not tokens:
        return None
    noun = tokens[-1]
    if len(tokens) >= 2:
        return noun
    return noun if noun != lowered_category else None


async def olx_cheapest(
    source: ProductSource,
    query: str,
    budget: int | None,
    city: str | None,
    found: list[RawProduct],
    book: BrandBook | None,
) -> list[RawProduct]:
    """Cheapest-first OLX pages within the category most on-category ads ``found`` share.

    No such category (or a source without the call) → nothing: cheapest first over the
    whole site is houses and services a fuzzy query matched.
    """
    category_of = getattr(source, "category_of", None)
    search_cheapest = getattr(source, "search_cheapest", None)
    if category_of is None or search_cheapest is None:
        return []
    categories = Counter(
        category_of(p.product_id)
        for p in found
        if matches_category_or_stripped(p.title, query, book)
    )
    categories.pop(None, None)
    if not categories:
        return []
    category_id = categories.most_common(1)[0][0]
    try:
        return await search_cheapest(
            query,
            city=city,
            budget=budget,
            region=True,
            category_id=category_id,
            limit=_OLX_CHEAPEST,
        )
    except Exception as exc:  # noqa: BLE001 - the extra pages must not cost the OLX pool
        logger.info("olx: cheapest-first search failed: %r", exc)
        return []
