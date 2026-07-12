from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Mapping

from krs.ai.card_score import CardScore
from krs.cards.card import Card

if TYPE_CHECKING:
    from krs.ai.strategy_config import StrategyConfig


@dataclass(slots=True)
class CardEvaluator:
    mana_value_weight: float = 1.0
    mana_ability_bonus: float = 2.0
    untap_bonus: float = 5.0
    copy_bonus: float = 4.0
    combo_bonus: float = 3.0

    custom_scores: Mapping[str, float] = field(
        default_factory=dict
    )
    combo_card_ids: frozenset[str] = frozenset()

    @classmethod
    def from_strategy(
        cls,
        config: StrategyConfig,
    ) -> CardEvaluator:
        return cls(
            mana_value_weight=config.mana_value_weight,
            mana_ability_bonus=config.mana_ability_bonus,
            untap_bonus=config.untap_bonus,
            copy_bonus=config.copy_bonus,
            combo_bonus=config.combo_bonus,
            custom_scores=config.custom_scores,
            combo_card_ids=config.combo_card_ids,
        )

    def evaluate(self, card: Card) -> CardScore:
        oracle_text = card.oracle_text.casefold()

        mana_ability_score = (
            self.mana_ability_bonus
            if card.mana_abilities
            else 0.0
        )

        untap_score = (
            self.untap_bonus
            if self._has_untap_effect(oracle_text)
            else 0.0
        )

        copy_score = (
            self.copy_bonus
            if self._has_copy_effect(oracle_text)
            else 0.0
        )

        combo_score = (
            self.combo_bonus
            if card.id in self.combo_card_ids
            else 0.0
        )

        return CardScore(
            mana_value_score=(
                card.mana_value
                * self.mana_value_weight
            ),
            mana_ability_score=mana_ability_score,
            untap_score=untap_score,
            copy_score=copy_score,
            combo_score=combo_score,
            custom_score=self.custom_scores.get(
                card.id,
                0.0,
            ),
        )

    @staticmethod
    def _has_untap_effect(
        oracle_text: str,
    ) -> bool:
        return (
            "untap" in oracle_text
            or "アンタップ" in oracle_text
        )

    @staticmethod
    def _has_copy_effect(
        oracle_text: str,
    ) -> bool:
        return (
            "copy of" in oracle_text
            or "as a copy" in oracle_text
            or "コピーとして" in oracle_text
        )