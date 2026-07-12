from __future__ import annotations

from krs.cards.card import Card
from krs.mana.mana_cost import ManaCost


KINNAN_ACTIVATION_COST = ManaCost(
    generic=5,
    green=1,
    blue=1,
)

KINNAN_LOOK_COUNT = 5


def card_types(card: Card) -> set[str]:
    type_part = card.type_line.split(
        " — ",
        maxsplit=1,
    )[0]

    return set(type_part.split())


def creature_types(card: Card) -> set[str]:
    if "Creature" not in card_types(card):
        return set()

    if " — " not in card.type_line:
        return set()

    subtype_part = card.type_line.split(
        " — ",
        maxsplit=1,
    )[1]

    return set(subtype_part.split())


def is_creature(card: Card) -> bool:
    return "Creature" in card_types(card)


def is_human(card: Card) -> bool:
    return "Human" in creature_types(card)


def is_valid_kinnan_hit(card: Card) -> bool:
    """
    Kinnan may put a non-Human creature card onto the battlefield.
    """

    return is_creature(card) and not is_human(card)


def find_selected_hit(
    revealed_cards: list[Card],
    selected_card_id: str | None,
) -> Card | None:
    if selected_card_id is None:
        return None

    for card in revealed_cards:
        if card.id == selected_card_id:
            if not is_valid_kinnan_hit(card):
                raise ValueError(
                    "Selected card is not a valid Kinnan hit: "
                    f"{card.name}"
                )

            return card

    raise ValueError(
        "Selected card was not found among Kinnan reveals: "
        f"{selected_card_id}"
    )