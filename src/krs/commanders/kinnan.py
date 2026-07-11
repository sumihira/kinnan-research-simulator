from __future__ import annotations

from krs.game.permanent import Permanent
from krs.game.zone import Zone
from krs.mana.mana import Mana


KINNAN_CARD_NAME = "Kinnan, Bonder Prodigy"
ROAMING_THRONE_CARD_NAME = "Roaming Throne"
CHOSEN_CREATURE_TYPE_KEY = "creature_type"


def is_kinnan(permanent: Permanent) -> bool:
    """
    Return whether this permanent currently has Kinnan's
    characteristics.
    """
    return permanent.effective_card.name == KINNAN_CARD_NAME


def is_roaming_throne(permanent: Permanent) -> bool:
    """
    Return whether this permanent currently has Roaming Throne's
    characteristics.
    """
    return (
        permanent.effective_card.name
        == ROAMING_THRONE_CARD_NAME
    )


def count_active_kinnan_effects(
    battlefield: Zone[Permanent],
) -> int:
    """
    Count permanents currently functioning as Kinnan.
    """
    return sum(
        1
        for permanent in battlefield
        if is_kinnan(permanent)
    )


def roaming_throne_applies_to_kinnan(
    permanent: Permanent,
) -> bool:
    """
    Return whether this Roaming Throne has selected a creature type
    shared by Kinnan.

    Kinnan's creature types are Human and Druid.
    """
    if not is_roaming_throne(permanent):
        return False

    chosen_type = permanent.chosen_values.get(
        CHOSEN_CREATURE_TYPE_KEY
    )

    if chosen_type is None:
        return False

    kinnan_types = {
        "Human",
        "Druid",
    }

    return chosen_type in kinnan_types


def count_kinnan_trigger_multipliers(
    battlefield: Zone[Permanent],
) -> int:
    """
    Count additional trigger occurrences applied to each Kinnan.

    The base trigger is represented by 1. Each applicable
    Roaming Throne adds one more occurrence.
    """
    applicable_thrones = sum(
        1
        for permanent in battlefield
        if roaming_throne_applies_to_kinnan(permanent)
    )

    return 1 + applicable_thrones


def count_kinnan_bonus_triggers(
    battlefield: Zone[Permanent],
) -> int:
    """
    Return the total number of Kinnan bonus-mana triggers.

    Example:
        2 Kinnans and 1 applicable Throne:
        2 * (1 + 1) = 4
    """
    kinnan_count = count_active_kinnan_effects(
        battlefield
    )

    if kinnan_count == 0:
        return 0

    multiplier = count_kinnan_trigger_multipliers(
        battlefield
    )

    return kinnan_count * multiplier


def choose_kinnan_bonus_mana(
    produced_mana: dict[Mana, int],
    selected_mana: Mana,
) -> Mana:
    """
    Choose the mana type added by Kinnan.

    Version 1 deterministically selects the mana type requested by
    the original mana Action.
    """
    if produced_mana.get(selected_mana, 0) <= 0:
        raise ValueError(
            "Kinnan bonus mana must match a produced mana type."
        )

    return selected_mana