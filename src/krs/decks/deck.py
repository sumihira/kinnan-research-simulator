from __future__ import annotations

from dataclasses import dataclass, field

from krs.cards.card import Card


@dataclass(slots=True)
class Deck:
    """
    A Commander deck definition.

    The commander is stored separately from the 99-card main deck.
    Deck legality is handled by DeckValidator.
    """

    name: str
    commander: Card
    cards: list[Card] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Deck name must not be empty.")

    @property
    def main_deck_count(self) -> int:
        return len(self.cards)

    @property
    def total_card_count(self) -> int:
        return 1 + len(self.cards)

    @property
    def all_cards(self) -> list[Card]:
        return [self.commander, *self.cards]