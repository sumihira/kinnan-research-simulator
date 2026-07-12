from __future__ import annotations

from collections.abc import Sequence

from krs.ai.evaluator import CardEvaluator
from krs.cards.card import Card
from krs.commanders.kinnan_ability import (
    is_valid_kinnan_hit,
)


class KinnanHitSelector:
    """
    Selects the highest-scoring valid Kinnan hit.

    Reveal order is preserved when scores are tied.
    """

    def __init__(
        self,
        evaluator: CardEvaluator | None = None,
    ) -> None:
        self._evaluator = (
            evaluator or CardEvaluator()
        )

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
            key=lambda card: (
                self._evaluator
                .evaluate(card)
                .total
            ),
        )