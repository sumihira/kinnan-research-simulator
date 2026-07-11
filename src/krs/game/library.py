from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class Library(Generic[T]):
    """
    Ordered library zone.

    Index 0 is treated as the top of the library.
    """

    cards: list[T] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.cards)

    def __iter__(self):
        return iter(self.cards)

    def __contains__(self, card: T) -> bool:
        return card in self.cards

    def shuffle(self, rng: random.Random) -> None:
        rng.shuffle(self.cards)

    def draw(self) -> T:
        if not self.cards:
            raise IndexError("Cannot draw from an empty library.")

        return self.cards.pop(0)

    def draw_many(self, amount: int) -> list[T]:
        if amount < 0:
            raise ValueError("Draw amount must not be negative.")

        if amount > len(self.cards):
            raise IndexError("Not enough cards in library.")

        return [self.draw() for _ in range(amount)]

    def peek(self, amount: int = 1) -> list[T]:
        if amount < 0:
            raise ValueError("Peek amount must not be negative.")

        return list(self.cards[:amount])

    def put_on_bottom(self, card: T) -> None:
        self.cards.append(card)

    def put_many_on_bottom(self, cards: list[T]) -> None:
        self.cards.extend(cards)

    def add_on_top(self, card: T) -> None:
        self.cards.insert(0, card)