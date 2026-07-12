from __future__ import annotations

from collections.abc import Mapping

from krs.cards.cache import CardCache
from krs.cards.card import Card
from krs.cards.card_enricher import CardEnricher


class CardLoader:
    """Resolves and enriches card definitions by name."""

    def __init__(
        self,
        cards_by_name: Mapping[str, Card] | None = None,
        *,
        cache: CardCache | None = None,
        enricher: CardEnricher | None = None,
    ) -> None:
        if cards_by_name is not None and cache is not None:
            raise ValueError(
                "Specify either cards_by_name or cache, not both."
            )

        self._cards_by_name = {
            CardCache.normalize_name(name): card
            for name, card in (cards_by_name or {}).items()
        }
        self._cache = cache
        self._enricher = enricher

    @classmethod
    def from_cache(
        cls,
        cache: CardCache,
        *,
        enricher: CardEnricher | None = None,
    ) -> CardLoader:
        return cls(
            cache=cache,
            enricher=enricher,
        )

    def load_by_name(
        self,
        name: str,
    ) -> Card:
        normalized_name = CardCache.normalize_name(name)

        if not normalized_name:
            raise ValueError(
                "Card name must not be empty."
            )

        card = self._load_base_card(
            name=name,
            normalized_name=normalized_name,
        )

        if self._enricher is None:
            return card

        return self._enricher.enrich(card)

    def _load_base_card(
        self,
        *,
        name: str,
        normalized_name: str,
    ) -> Card:
        if self._cache is not None:
            return self._cache.get_by_name(name)

        try:
            return self._cards_by_name[normalized_name]
        except KeyError as error:
            raise ValueError(
                f"Card not found: {name}"
            ) from error