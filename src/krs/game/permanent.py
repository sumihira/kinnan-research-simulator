from __future__ import annotations

from dataclasses import dataclass, field

from krs.cards.card import Card


@dataclass(slots=True)
class Permanent:
    """
    Runtime representation of a permanent on the battlefield.
    """

    permanent_id: int
    card: Card
    owner_id: int
    controller_id: int

    tapped: bool = False
    summoning_sick: bool = True
    is_token: bool = False

    copied_from: Card | None = None

    entered_turn: int = 0

    counters: dict[str, int] = field(default_factory=dict)

    chosen_values: dict[str, str] = field(default_factory=dict)

    @property
    def effective_card(self) -> Card:
        """
        Return the characteristics copied by this permanent.

        The printed card remains available through `card`.
        """
        return self.copied_from or self.card

    @property
    def is_land(self) -> bool:
        type_part = self.effective_card.type_line.split(
            " — ",
            maxsplit=1,
        )[0]

        return "Land" in type_part.split()

    @property
    def is_creature(self) -> bool:
        type_part = self.effective_card.type_line.split(
            " — ",
            maxsplit=1,
        )[0]

        return "Creature" in type_part.split()

    @property
    def is_nonland(self) -> bool:
        return not self.is_land

    @property
    def creature_types(self) -> set[str]:
        """
        Return this permanent's creature subtypes.

        Noncreature permanents return an empty set.
        """
        if not self.is_creature:
            return set()

        type_line = self.effective_card.type_line

        if " — " not in type_line:
            return set()

        subtype_part = type_line.split(
            " — ",
            maxsplit=1,
        )[1]

        return set(subtype_part.split())