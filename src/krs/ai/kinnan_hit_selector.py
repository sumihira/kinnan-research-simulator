from __future__ import annotations

from collections.abc import Sequence

from krs.cards.card import Card
from krs.commanders.kinnan_ability import (
    is_valid_kinnan_hit,
)


class KinnanHitSelector:
    """
    Selects a card from Kinnan's revealed cards.

    Version 1 policy:
    - only non-Human creature cards are valid;
    - prefer the highest mana value;
    - preserve reveal order when mana values are tied.
    """

    def select(
        self,
        revealed_cards: Sequence[Card],
    ) -> Card | None:
        valid_hits = [
            card
            for card in revealed_cards
            if is_valid_kinnan_hit(card)
        ]

        if not valid_hits:
            return None

        return max(
            valid_hits,
            key=lambda card: card.mana_value,
        )