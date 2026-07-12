from __future__ import annotations

from collections.abc import Mapping

from krs.cards.card import Card


class CardLoader:
    """
    Resolves card definitions by card name.

    Version 1 uses an injected in-memory mapping.
    Scryfall and cache integration will be added later.
    """

    def __init__(
        self,
        cards_by_name: Mapping[str, Card] | None = None,
    ) -> None:
        self._cards_by_name = {
            name.casefold(): card
            for name, card in (
                cards_by_name or {}
            ).items()
        }

    def load_by_name(
        self,
        name: str,
    ) -> Card:
        normalized_name = name.strip().casefold()

        if not normalized_name:
            raise ValueError(
                "Card name must not be empty."
            )

        try:
            return self._cards_by_name[
                normalized_name
            ]
        except KeyError as error:
            raise ValueError(
                f"Card not found: {name}"
            ) from error