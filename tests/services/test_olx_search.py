"""Cheapest-first OLX pages run within the category the on-category ads share."""

from market_sources.base import RawProduct

from buysmarter.services.olx_search import olx_cheapest


def _ad(pid: str, title: str) -> RawProduct:
    return RawProduct(source="olx", product_id=pid, title=title)


class _Olx:
    name = "olx"

    def __init__(self, categories: dict[str, str]) -> None:
        self._categories = categories
        self.calls: list[dict] = []

    def category_of(self, product_id: str) -> str | None:
        return self._categories.get(product_id)

    async def search_cheapest(self, query, **kwargs):
        self.calls.append({"query": query, **kwargs})
        return [_ad("cheap", "Посудомоечная машина б/у за 55 000 тенге")]


async def test_the_category_most_on_category_ads_share_narrows_the_cheap_pages():
    found = [
        _ad("1", "Посудомоечная машина Hansa"),
        _ad("2", "Посудомоечная машина Midea"),
        _ad("3", "Дом отдыха, посудомоечная машина есть"),
        _ad("4", "Ремонт стиральных машин"),
    ]
    olx = _Olx({"1": "380", "2": "380", "3": "1485", "4": "826"})

    cheap = await olx_cheapest(olx, "посудомоечная машина", 90_000, "1", found, None)

    assert [p.product_id for p in cheap] == ["cheap"]
    assert olx.calls[0]["category_id"] == "380" and olx.calls[0]["region"] is True
    assert olx.calls[0]["budget"] == 90_000


async def test_no_category_or_no_such_call_fetches_nothing():
    found = [_ad("1", "Посудомоечная машина")]
    assert await olx_cheapest(_Olx({}), "посудомоечная машина", None, None, found, None) == []

    class _Plain:
        name = "olx"

    assert await olx_cheapest(_Plain(), "посудомоечная машина", None, None, found, None) == []
