from __future__ import annotations

from collections.abc import Mapping

from krs.cards.cache import CardCache
from krs.cards.card import Card


class CardLoader:
    """
    Resolves card definitions by name.

    It can use an in-memory mapping for unit tests or a local
    Scryfall-backed CardCache for production.
    """

    def __init__(
        self,
        cards_by_name: Mapping[str, Card] | None = None,
        *,
        cache: CardCache | None = None,
    ) -> None:
        if cards_by_name is not None and cache is not None:
            raise ValueError(
                "Specify either cards_by_name or cache, not both."
            )

        self._cards_by_name = {
            CardCache.normalize_name(name): card
            for name, card in (
                cards_by_name or {}
            ).items()
        }
        self._cache = cache

    @classmethod
    def from_cache(
        cls,
        cache: CardCache,
    ) -> CardLoader:
        return cls(cache=cache)

    def load_by_name(
        self,
        name: str,
    ) -> Card:
        normalized_name = CardCache.normalize_name(
            name
        )

        if not normalized_name:
            raise ValueError(
                "Card name must not be empty."
            )

        if self._cache is not None:
            return self._cache.get_by_name(name)

        try:
            return self._cards_by_name[
                normalized_name
            ]
        except KeyError as error:
            raise ValueError(
                f"Card not found: {name}"
            ) from error