from __future__ import annotations

from krs.game.permanent import Permanent
from krs.mana.mana import Mana


KINNAN_CARD_NAME = "Kinnan, Bonder Prodigy"


def is_kinnan(permanent: Permanent) -> bool:
    """
    Return whether the permanent currently has Kinnan's characteristics.

    `effective_card` allows copied permanents to be recognized later.
    """
    return permanent.effective_card.name == KINNAN_CARD_NAME


def count_active_kinnan_effects(
    battlefield: list[Permanent] | object,
) -> int:
    """
    Count active Kinnan static effects on the battlefield.

    Version 1 counts each untapped or tapped Kinnan equally because
    Kinnan's mana-modifying ability does not require tapping.
    """
    return sum(
        1
        for permanent in battlefield
        if is_kinnan(permanent)
    )


def choose_kinnan_bonus_mana(
    produced_mana: dict[Mana, int],
    selected_mana: Mana,
) -> Mana:
    """
    Choose the mana type added by Kinnan.

    Kinnan must add a type of mana the permanent produced.
    Version 1 uses the selected mana type deterministically.
    """
    if produced_mana.get(selected_mana, 0) <= 0:
        raise ValueError(
            "Kinnan bonus mana must match a produced mana type."
        )

    return selected_mana