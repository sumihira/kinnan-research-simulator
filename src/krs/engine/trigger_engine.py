from __future__ import annotations

from collections.abc import Iterable, Mapping

from krs.abilities.static import StaticAbility
from krs.abilities.triggered import TriggeredAbility
from krs.game.permanent import Permanent


class TriggerEngine:
    """Calculates triggered ability occurrence counts."""

    ADDITIONAL_TRIGGER_ABILITY_TYPE = "additional_trigger"
    CREATURE_TYPE_CHOICE_KEY = "creature_type"

    def count_triggers(
        self,
        *,
        source: Permanent,
        ability: TriggeredAbility,
        battlefield: Iterable[Permanent],
    ) -> int:
        """
        Return the number of times a triggered ability should trigger.

        A triggered ability normally triggers once. Static abilities such
        as Roaming Throne may increase that count when all configured
        source filters are satisfied.
        """
        del ability

        trigger_count = 1

        for permanent in battlefield:
            for static_ability in (
                permanent.effective_card.static_abilities
            ):
                trigger_count += self._additional_trigger_count(
                    source=source,
                    modifier_source=permanent,
                    ability=static_ability,
                )

        return trigger_count

    def _additional_trigger_count(
        self,
        *,
        source: Permanent,
        modifier_source: Permanent,
        ability: StaticAbility,
    ) -> int:
        if (
            ability.ability_type
            != self.ADDITIONAL_TRIGGER_ABILITY_TYPE
        ):
            return 0

        parameters = ability.parameters or {}

        if not self._matches_controller_filter(
            source=source,
            modifier_source=modifier_source,
            parameters=parameters,
        ):
            return 0

        source_filter = self._source_filter(parameters)

        if not self._matches_other_creature_filter(
            source=source,
            modifier_source=modifier_source,
            source_filter=source_filter,
        ):
            return 0

        if not self._matches_chosen_creature_type_filter(
            source=source,
            modifier_source=modifier_source,
            source_filter=source_filter,
        ):
            return 0

        return self._read_additional_trigger_count(parameters)

    @staticmethod
    def _matches_controller_filter(
        *,
        source: Permanent,
        modifier_source: Permanent,
        parameters: Mapping[str, object],
    ) -> bool:
        controller_only = parameters.get(
            "controller_only",
            False,
        )

        if not isinstance(controller_only, bool):
            raise ValueError(
                "controller_only must be a boolean."
            )

        if not controller_only:
            return True

        return (
            source.controller_id
            == modifier_source.controller_id
        )

    @staticmethod
    def _matches_other_creature_filter(
        *,
        source: Permanent,
        modifier_source: Permanent,
        source_filter: Mapping[str, object],
    ) -> bool:
        other_creature = source_filter.get(
            "other_creature",
            False,
        )

        if not isinstance(other_creature, bool):
            raise ValueError(
                "other_creature must be a boolean."
            )

        if not other_creature:
            return True

        return (
            source.is_creature
            and source.permanent_id
            != modifier_source.permanent_id
        )

    def _matches_chosen_creature_type_filter(
        self,
        *,
        source: Permanent,
        modifier_source: Permanent,
        source_filter: Mapping[str, object],
    ) -> bool:
        chosen_creature_type = source_filter.get(
            "chosen_creature_type",
            False,
        )

        if not isinstance(chosen_creature_type, bool):
            raise ValueError(
                "chosen_creature_type must be a boolean."
            )

        if not chosen_creature_type:
            return True

        chosen_type = modifier_source.chosen_values.get(
            self.CREATURE_TYPE_CHOICE_KEY
        )

        if chosen_type is None:
            return False

        normalized_chosen_type = chosen_type.casefold()

        return any(
            creature_type.casefold() == normalized_chosen_type
            for creature_type in source.creature_types
        )

    @staticmethod
    def _source_filter(
        parameters: Mapping[str, object],
    ) -> Mapping[str, object]:
        source_filter = parameters.get(
            "source_filter",
            {},
        )

        if not isinstance(source_filter, Mapping):
            raise ValueError(
                "source_filter must be a mapping."
            )

        return source_filter

    @staticmethod
    def _read_additional_trigger_count(
        parameters: Mapping[str, object],
    ) -> int:
        additional_trigger_count = parameters.get(
            "additional_trigger_count",
            0,
        )

        if (
            not isinstance(additional_trigger_count, int)
            or isinstance(additional_trigger_count, bool)
        ):
            raise ValueError(
                "additional_trigger_count must be an integer."
            )

        if additional_trigger_count < 0:
            raise ValueError(
                "additional_trigger_count must not be negative."
            )

        return additional_trigger_count