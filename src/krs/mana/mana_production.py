from __future__ import annotations

from collections.abc import Iterable, Mapping

from krs.abilities.static import StaticAbility
from krs.game.permanent import Permanent


MANA_PRODUCTION_MULTIPLIER = "mana_production_multiplier"


def mana_production_multiplier(
    *,
    source: Permanent,
    battlefield: Iterable[Permanent],
) -> int:
    """
    Return the multiplier applied to mana produced by one permanent.

    Multipliers are read from static abilities controlled by the same
    player as the mana source. Multiple multipliers are multiplicative.

    A multiplier applies to both land and nonland permanents unless its
    source_filter restricts the affected permanent type.
    """
    multiplier = 1

    for modifier_source in battlefield:
        if (
            modifier_source.controller_id
            != source.controller_id
        ):
            continue

        for ability in (
            modifier_source.effective_card.static_abilities
        ):
            multiplier *= _ability_multiplier(
                ability=ability,
                source=source,
            )

    return multiplier


def _ability_multiplier(
    *,
    ability: StaticAbility,
    source: Permanent,
) -> int:
    if ability.ability_type != MANA_PRODUCTION_MULTIPLIER:
        return 1

    parameters = ability.parameters

    if not isinstance(parameters, Mapping):
        raise ValueError(
            "Mana production multiplier parameters "
            "must be a mapping."
        )

    if not _matches_source_filter(
        source=source,
        parameters=parameters,
    ):
        return 1

    raw_multiplier = parameters.get(
        "multiplier",
    )

    if (
        not isinstance(raw_multiplier, int)
        or isinstance(raw_multiplier, bool)
        or raw_multiplier < 1
    ):
        raise ValueError(
            "Mana production multiplier must be "
            "an integer of at least 1."
        )

    return raw_multiplier


def _matches_source_filter(
    *,
    source: Permanent,
    parameters: Mapping[str, object],
) -> bool:
    raw_source_filter = parameters.get(
        "source_filter",
        {},
    )

    if not isinstance(raw_source_filter, Mapping):
        raise ValueError(
            "Mana production source_filter "
            "must be a mapping."
        )

    raw_permanent_type = raw_source_filter.get(
        "permanent_type",
    )

    if raw_permanent_type is None:
        return True

    if not isinstance(raw_permanent_type, str):
        raise ValueError(
            "Mana production source_filter.permanent_type "
            "must be a string."
        )

    permanent_type = (
        raw_permanent_type.strip().casefold()
    )

    if permanent_type == "land":
        return source.is_land

    if permanent_type == "nonland":
        return source.is_nonland

    if permanent_type == "creature":
        return source.is_creature

    raise ValueError(
        "Unsupported mana production source type: "
        f"{raw_permanent_type}"
    )