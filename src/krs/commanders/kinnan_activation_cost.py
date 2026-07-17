from __future__ import annotations

from krs.commanders.kinnan_ability import (
    KINNAN_ACTIVATION_COST,
)
from krs.game.player import Player
from krs.mana.mana_cost import ManaCost


ACTIVATED_ABILITY_COST_REDUCTION = (
    "activated_ability_cost_reduction"
)
CREATURE_ABILITY_SOURCE = "creature"


def kinnan_activation_cost(
    player: Player,
) -> ManaCost:
    """
    Return Kinnan's effective activated-ability cost.

    Training Grounds and Biomancer's Familiar reduce only the generic
    portion of activated abilities of creature sources. Multiple effects
    stack.

    Kinnan's colored requirements remain unchanged.
    """
    generic_reduction = sum(
        _cost_reduction_from_permanent(permanent)
        for permanent in player.battlefield
    )

    return ManaCost(
        generic=max(
            0,
            (
                KINNAN_ACTIVATION_COST.generic
                - generic_reduction
            ),
        ),
        white=KINNAN_ACTIVATION_COST.white,
        blue=KINNAN_ACTIVATION_COST.blue,
        black=KINNAN_ACTIVATION_COST.black,
        red=KINNAN_ACTIVATION_COST.red,
        green=KINNAN_ACTIVATION_COST.green,
        colorless=KINNAN_ACTIVATION_COST.colorless,
    )


def _cost_reduction_from_permanent(
    permanent: object,
) -> int:
    effective_card = getattr(
        permanent,
        "effective_card",
        None,
    )

    if effective_card is None:
        return 0

    static_abilities = getattr(
        effective_card,
        "static_abilities",
        (),
    )

    reduction = 0

    for ability in static_abilities:
        if (
            ability.ability_type
            != ACTIVATED_ABILITY_COST_REDUCTION
        ):
            continue

        parameters = ability.parameters

        source_type = parameters.get(
            "source_type",
        )

        if source_type != CREATURE_ABILITY_SOURCE:
            continue

        amount = parameters.get(
            "amount",
        )

        if (
            not isinstance(amount, int)
            or isinstance(amount, bool)
            or amount < 0
        ):
            raise ValueError(
                "Activated ability cost reduction amount "
                "must be a non-negative integer."
            )

        reduction += amount

    return reduction