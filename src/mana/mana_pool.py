from __future__ import annotations

from collections import Counter

from mana.mana import Mana


class ManaPool:
    """
    Floating mana currently available.

    Does not know anything about permanents or lands.
    """

    def __init__(self) -> None:
        self._mana = Counter()

    def add(self, mana: Mana, amount: int = 1) -> None:
        self._mana[mana] += amount

    def remove(self, mana: Mana, amount: int = 1) -> None:
        if self._mana[mana] < amount:
            raise ValueError("Not enough mana.")

        self._mana[mana] -= amount

    def count(self, mana: Mana) -> int:
        return self._mana[mana]

    def clear(self) -> None:
        self._mana.clear()

    def total(self) -> int:
        return sum(self._mana.values())

    def __repr__(self) -> str:
        return f"ManaPool({dict(self._mana)})"