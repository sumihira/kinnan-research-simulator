from __future__ import annotations

from krs.ai.card_score import CardScore
from krs.cards.card import Card


class CardEvaluator:
    """Evaluates cards for Kinnan activation."""

    KINNAN_HIT_SCORE = 100.0

    def evaluate(
        self,
        card: Card,
    ) -> CardScore:
        """
        Return the structured evaluation score for a card.

        Version 1 assigns a custom score to cards that are legal
        Kinnan activation hits.
        """
        custom_score = (
            self.KINNAN_HIT_SCORE
            if self._is_non_human_creature(card)
            else 0.0
        )

        return CardScore(
            custom_score=custom_score,
        )

    @staticmethod
    def _is_non_human_creature(
        card: Card,
    ) -> bool:
        type_part = card.type_line.split(
            " — ",
            maxsplit=1,
        )[0]

        if "Creature" not in type_part.split():
            return False

        if " — " not in card.type_line:
            return True

        subtype_part = card.type_line.split(
            " — ",
            maxsplit=1,
        )[1]

        creature_types = set(
            subtype_part.split()
        )

        return "Human" not in creature_types