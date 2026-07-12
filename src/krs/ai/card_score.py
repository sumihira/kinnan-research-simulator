from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CardScore:
    """
    Detailed evaluation result for one card.

    Each component is kept separately so logs and reports can explain
    why a card was selected.
    """

    mana_value_score: float = 0.0
    mana_ability_score: float = 0.0
    untap_score: float = 0.0
    copy_score: float = 0.0
    combo_score: float = 0.0
    custom_score: float = 0.0

    @property
    def total(self) -> float:
        return (
            self.mana_value_score
            + self.mana_ability_score
            + self.untap_score
            + self.copy_score
            + self.combo_score
            + self.custom_score
        )