"""OLX ads against a size limit: the ad's words, then its model's specs; fails drop."""

from market_sources.base import RawProduct

from buysmarter.knowledge.models_book import ModelBook, ModelEntry
from buysmarter.ranking.models import Candidate
from buysmarter.services.matching import UsedListing
from buysmarter.services.used_specs import Fit, ad_sizes, apply_fits, check_used_sizes

_LIMIT = ["высотой до 50 см"]
_BOOK = ModelBook(
    entries=[
        ModelEntry(
            canonical="Midea MDWT-527TFG",
            brand="Midea",
            codes=["MDWT-527TFG"],
            specs={"Ширина": "55 см", "Глубина": "34.5 см", "Высота": "50 см"},
        ),
        ModelEntry(canonical="Hansa ZWM536", brand="Hansa", codes=["ZWM536"]),
        ModelEntry(canonical="Midea MDWT-827LWW", brand="Midea", codes=["MDWT-827LWW"]),
    ]
)


def _ad(title: str, price: int = 50_000, description: str = "") -> Candidate:
    return Candidate(
        source="olx",
        source_product_id=title,
        title=title,
        price=price,
        url=f"https://olx.kz/{abs(hash(title))}",
        availability=True,
        specs={"description": description, "city": "Коксай"},
    )


class _Kaspi:
    name = "kaspi"

    def __init__(self) -> None:
        self.searched: list[str] = []

    async def search(self, query: str, city=None):
        self.searched.append(query)
        return [RawProduct(source="kaspi", product_id="1", title="Midea MDWT-827LWW белый")]

    async def specs(self, product_id: str):
        return {"Высота": "59 см"}


def test_an_ad_states_its_sizes_in_words():
    text = "Компактная, высота 44 см, ширина: 42см, глубина — 440 мм"
    assert ad_sizes(text) == {"Высота": "44 см", "Ширина": "42 см", "Глубина": "440 мм"}


async def test_each_ad_climbs_the_ladder_to_the_first_answer():
    words = _ad("Посудомойка мини", description="высота 45 см")
    booked = _ad("Посудомоечная машина Midea MDWT-527TFG")
    pooled = _ad("Hansa ZWM536 посудомойка")
    searched = _ad("Midea MDWT-827LWW б/у")
    unknown = _ad("Посудомоечная машина б/у")
    card = Candidate(
        source="ozon",
        source_product_id="9",
        title="Hansa ZWM536SH",
        price=90_000,
        availability=True,
        specs={"Размер (ДхШхВ), см": "50х55х43,8"},
    )
    kaspi = _Kaspi()

    fits = await check_used_sizes(
        [words, booked, pooled, searched, unknown], [card], _LIMIT, _BOOK, kaspi
    )

    assert fits[words.url] == Fit(True, "высота 45 см (по объявлению)")
    assert fits[booked.url].ok is True and "книга моделей" in fits[booked.url].note
    assert fits[pooled.url].ok is True and "карточка Ozon" in fits[pooled.url].note
    assert fits[searched.url].ok is False and kaspi.searched == ["Midea MDWT-827LWW"]
    assert fits[unknown.url] == Fit(None, "не проверено: высотой до 50 см")


async def test_no_size_limit_checks_nothing():
    assert await check_used_sizes([_ad("x")], [], ["Wi-Fi"], _BOOK, None) == {}


def test_failing_ads_drop_and_passing_ones_no_product_matched_join():
    matched, failing = _ad("matched"), _ad("failing")
    extra, over_budget = _ad("extra", 55_000), _ad("pricey", 200_000)
    listings = [UsedListing(title=a.title, price=a.price, url=a.url) for a in (matched, failing)]
    fits = {
        matched.url: Fit(None, "не проверено: высотой до 50 см"),
        failing.url: Fit(False, "высота 59 см"),
        extra.url: Fit(True, "высота 50 см (книга моделей)"),
        over_budget.url: Fit(True, "высота 44 см"),
    }

    shown = apply_fits(listings, [matched, failing, extra, over_budget], fits, 100_000, None)

    assert [(s.title, s.fit, s.standalone) for s in shown] == [
        ("matched", "не проверено: высотой до 50 см", False),
        ("extra", "высота 50 см (книга моделей)", True),
    ]
    assert shown[1].city == "Коксай"
