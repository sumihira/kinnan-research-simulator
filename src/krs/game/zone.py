
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, Iterator, TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class Zone(Generic[T]):
    """
    Represents a game zone.

    This class only stores objects.
    Game logic is handled by GameEngine.
    """

    cards: list[T] = field(default_factory=list)

    def add(self, card: T) -> None:
        self.cards.append(card)

    def remove(self, card: T) -> None:
        self.cards.remove(card)

    def clear(self) -> None:
        self.cards.clear()

    def __len__(self) -> int:
        return len(self.cards)

    def __iter__(self) -> Iterator[T]:
        return iter(self.cards)

    def __contains__(self, card: T) -> bool:
        return card in self.cards