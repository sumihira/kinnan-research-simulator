from __future__ import annotations

from collections import Counter

from krs.mana.mana import Mana


class ManaPool:
    """
    Floating mana currently available.

    ManaPool manages only the current mana balance.
    Mana production events and their sources are recorded separately.
    """

    def __init__(self) -> None:
        self._mana: Counter[Mana] = Counter()

    def add(self, mana: Mana, amount: int = 1) -> None:
        if amount <= 0:
            raise ValueError("Mana amount must be greater than zero.")

        self._mana[mana] += amount

    def remove(self, mana: Mana, amount: int = 1) -> None:
        if amount <= 0:
            raise ValueError("Mana amount must be greater than zero.")

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