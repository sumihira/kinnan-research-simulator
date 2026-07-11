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

    can_activate_tap_abilities_as_though_haste: bool = False

    @property
    def effective_card(self) -> Card:
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

    @property
    def has_haste(self) -> bool:
        return any(
            keyword.casefold() == "haste"
            for keyword in self.effective_card.keywords
        )

    @property
    def can_activate_tap_ability(self) -> bool:
        """
        Return whether this permanent may activate a tap ability.

        Summoning sickness only restricts creatures.
        """
        if not self.is_creature:
            return True

        if not self.summoning_sick:
            return True

        if self.has_haste:
            return True

        return self.can_activate_tap_abilities_as_though_haste