from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from krs.mana.mana import Mana


@dataclass(frozen=True, slots=True, kw_only=True)
class ManaAbility:
    """
    Defines an activated mana ability.

    Version 1 supports abilities that:
    - require tapping the source;
    - produce a fixed amount of mana;
    - have no additional activation cost.
    """

    produced_mana: Mapping[Mana, int]
    requires_tap: bool = True

    def __post_init__(self) -> None:
        if not self.produced_mana:
            raise ValueError(
                "Mana ability must produce at least one mana."
            )

        if any(
            amount <= 0
            for amount in self.produced_mana.values()
        ):
            raise ValueError(
                "Produced mana amounts must be greater than zero."
            )

        # 外部から辞書を書き換えられないようにコピーして固定する
        immutable_mana = MappingProxyType(
            dict(self.produced_mana)
        )

        object.__setattr__(
            self,
            "produced_mana",
            immutable_mana,
        )

    @property
    def total_produced(self) -> int:
        return sum(self.produced_mana.values())

    def can_produce(self, mana: Mana) -> bool:
        return self.produced_mana.get(mana, 0) > 0