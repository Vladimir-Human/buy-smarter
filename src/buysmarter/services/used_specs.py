"""OLX ads against the request's size limits ("высотой до 50 см").

An ad has no specs, so each ad climbs a ladder, cheapest first, and stops at the
first rung that answers:

1. the ad's own words: "высота 44 см" in the title or the description;
2. its model (the model book resolves the title and description): the model's
   specs in the book (learned from notes or the web), then a new card of that
   model in the pool, then a Kaspi search for the model (a few per run);
3. none answers: the ad stays, marked "не проверено".

An ad that fails is dropped; one that passes and no new product matched joins
the OLX section on its own. Photos are not read (docs/tasks/2026-10-31-olx-unknown-specs.md).
"""

import logging
import re
from dataclasses import dataclass

from market_sources.base import ProductSource

from buysmarter.knowledge.models_book import ModelBook, ModelEntry
from buysmarter.ranking.filters import size_limit, size_limit_met
from buysmarter.ranking.models import Candidate
from buysmarter.services.matching import UsedListing, ad_text, used_con_of

logger = logging.getLogger(__name__)

_MAX_KASPI_LOOKUPS = 5  # Kaspi searches for an ad's model, per run
_MAX_VERIFIED_EXTRA = 5  # passing ads no new product matched, shown on their own
_SIDE_WORDS = {"высот": "высота", "ширин": "ширина", "глубин": "глубина"}
_AD_SIZE_RE = re.compile(
    r"\b(высот|ширин|глубин)\w*\s*[:—–-]?\s*(\d+(?:[.,]\d+)?)\s*(мм|см)\b", re.IGNORECASE
)


@dataclass(frozen=True)
class Fit:
    """An ad against the size limits: passes (True), fails (False) or unknown (None)."""

    ok: bool | None
    note: str


def ad_sizes(text: str) -> dict[str, str]:
    """Sizes an ad states in words: {"Высота": "44 см"}; the first of each side."""
    sizes: dict[str, str] = {}
    for side, number, unit in _AD_SIZE_RE.findall(text):
        sizes.setdefault(_SIDE_WORDS[side.lower()].capitalize(), f"{number} {unit.lower()}")
    return sizes


def _judge(features: list[str], specs: dict[str, str]) -> bool | None:
    """Every limit met (True), one broken (False), or a side the specs lack (None)."""
    verdicts = [size_limit_met(f, specs) for f in features]
    if False in verdicts:
        return False
    return None if None in verdicts else True


def _fit(features: list[str], specs: dict[str, str], source: str) -> Fit | None:
    """The verdict these specs give, with what they say; None when they cannot tell."""
    ok = _judge(features, specs)
    return None if ok is None else Fit(ok, _sizes_note(features, specs, source))


def _sizes_note(features: list[str], specs: dict[str, str], source: str) -> str:
    """ "высота 50 см (карточка Kaspi)": the sides the limits ask about, as the source says."""
    sides = {limit[0] for f in features if (limit := size_limit(f)) is not None}
    shown = [
        f"{key.split(',')[0].lower()} {value}"
        for key, value in specs.items()
        if key.lower().startswith(tuple(sides)) and "упаков" not in key.lower()
    ]
    return f"{', '.join(shown) or 'размер'} ({source})"


class _ModelSpecs:
    """A model's specs: the book, a new card of it in the pool, or one Kaspi search."""

    def __init__(self, pool: list[Candidate], book: ModelBook, kaspi: ProductSource | None):
        self._book, self._kaspi = book, kaspi
        self._cache: dict[str, tuple[dict[str, str], str] | None] = {}
        self._lookups = 0
        self._pool: dict[str, Candidate] = {}
        for c in pool:
            entry = book.resolve_entry(c.title)
            if entry is not None and c.specs:
                self._pool.setdefault(entry.canonical, c)

    async def of(self, entry: ModelEntry) -> tuple[dict[str, str], str] | None:
        if entry.canonical not in self._cache:
            self._cache[entry.canonical] = await self._find(entry)
        return self._cache[entry.canonical]

    async def _find(self, entry: ModelEntry) -> tuple[dict[str, str], str] | None:
        if entry.specs:
            return entry.specs, f"книга моделей: {entry.canonical}"
        if (card := self._pool.get(entry.canonical)) is not None:
            return card.specs, f"карточка {card.source.capitalize()}: {card.title}"
        if self._kaspi is None or self._lookups >= _MAX_KASPI_LOOKUPS:
            return None
        self._lookups += 1
        try:
            return await self._kaspi_card(self._kaspi, entry)
        except Exception as exc:  # noqa: BLE001 - a lookup must never cost the OLX section
            logger.info("olx sizes: kaspi lookup for %r failed: %r", entry.canonical, exc)
            return None

    async def _kaspi_card(
        self, kaspi: ProductSource, entry: ModelEntry
    ) -> tuple[dict[str, str], str] | None:
        """The specs of the first Kaspi card the model book reads as this model."""
        for product in await kaspi.search(entry.canonical):
            if self._book.resolve(product.title) == entry.canonical:
                specs = await kaspi.specs(product.product_id)
                return specs, f"карточка Kaspi: {product.title}"
        return None


async def check_used_sizes(
    used: list[Candidate],
    pool: list[Candidate],
    features: list[str],
    book: ModelBook | None,
    kaspi: ProductSource | None,
) -> dict[str, Fit]:
    """Each ad's ``Fit`` by its url (title without one); {} when no size limit applies."""
    limits = [f for f in features if size_limit(f) is not None]
    if not limits:
        return {}
    unknown = "не проверено: " + ", ".join(limits)
    models = _ModelSpecs(pool, book, kaspi) if book is not None else None
    fits: dict[str, Fit] = {}
    for ad in used:
        fits[_key(ad)] = await _ad_fit(ad, limits, book, models) or Fit(None, unknown)
    logger.info("olx sizes: %s", {k[-40:]: f.ok for k, f in fits.items()})
    return fits


async def _ad_fit(
    ad: Candidate, limits: list[str], book: ModelBook | None, models: _ModelSpecs | None
) -> Fit | None:
    """The ad's fit by its own words, else by its model's sizes; None when neither tells."""
    text = ad_text(ad)
    fit = _fit(limits, ad_sizes(text), "по объявлению")
    if fit is not None or book is None or models is None:
        return fit
    entry = book.resolve_entry(text)
    found = await models.of(entry) if entry is not None else None
    return _fit(limits, *found) if found is not None else None


def _key(item: UsedListing | Candidate) -> str:
    return item.url or item.title


def apply_fits(
    listings: list[UsedListing],
    used: list[Candidate],
    fits: dict[str, Fit],
    budget: int | None,
    book: ModelBook | None,
) -> list[UsedListing]:
    """Drop the ads that fail, mark the rest, add passing ads no new product matched."""
    if not fits:
        return listings
    kept = _marked(listings, fits)
    shown = {_key(listing) for listing in kept}
    extra = [u for u in used if _key(u) not in shown]
    return kept + _verified(extra, fits, budget, book)


def _marked(listings: list[UsedListing], fits: dict[str, Fit]) -> list[UsedListing]:
    """The listings that do not fail, each with its size verdict."""
    return [
        listing.model_copy(update={"fit": fits[_key(listing)].note})
        if _key(listing) in fits
        else listing
        for listing in listings
        if _key(listing) not in fits or fits[_key(listing)].ok is not False
    ]


def _verified(
    used: list[Candidate], fits: dict[str, Fit], budget: int | None, book: ModelBook | None
) -> list[UsedListing]:
    """Ads that pass the size limits, within budget, cheapest first, as their own rows."""
    passing = sorted(
        (
            u
            for u in used
            if _key(u) in fits and fits[_key(u)].ok and 0 < u.price <= (budget or u.price)
        ),
        key=lambda u: u.price,
    )
    return [
        UsedListing(
            title=u.title,
            price=u.price,
            city=u.specs.get("city"),
            url=u.url,
            con=used_con_of(u),
            canonical=book.describe(u.title) if book is not None else None,
            standalone=True,
            fit=fits[_key(u)].note,
        )
        for u in passing[:_MAX_VERIFIED_EXTRA]
    ]
