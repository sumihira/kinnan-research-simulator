from __future__ import annotations

from collections.abc import Iterable, Mapping

from krs.abilities.static import StaticAbility
from krs.game.permanent import Permanent
from krs.mana.mana import Mana
from krs.abilities.triggered import TriggeredAbility
from krs.engine.trigger_engine import TriggerEngine


class StaticAbilityEngine:
    """Evaluates static abilities affecting game operations."""

    ADDITIONAL_NONLAND_MANA = "additional_nonland_mana"

    def __init__(
        self,
        trigger_engine: TriggerEngine | None = None,
    ) -> None:
        self._trigger_engine = trigger_engine or TriggerEngine()

    def calculate_additional_nonland_mana(
        self,
        *,
        source: Permanent,
        produced_mana: Mapping[Mana, int],
        selected_mana: Mana,
        battlefield: Iterable[Permanent],
    ) -> dict[Mana, int]:
        """
        Calculate additional mana produced by static abilities.

        Each matching additional_nonland_mana ability contributes its
        configured amount in the configured mana-selection mode.
        """
        if source.is_land:
            return {}

        additional_mana: dict[Mana, int] = {}

        for modifier_source in battlefield:
            if (
                modifier_source.controller_id
                != source.controller_id
            ):
                continue

            for ability in (
                modifier_source.effective_card.static_abilities
            ):
                mana_type, amount = self._resolve_additional_mana(
                    ability=ability,
                    source=source,
                    produced_mana=produced_mana,
                    selected_mana=selected_mana,
                )

                if mana_type is None or amount == 0:
                    continue

                trigger_count = self._count_additional_mana_triggers(
                    source=modifier_source,
                    battlefield=battlefield,
                )

                total_amount = amount * trigger_count

                additional_mana[mana_type] = (
                    additional_mana.get(mana_type, 0)
                    + total_amount
                )

        return additional_mana

    def _count_additional_mana_triggers(
        self,
        *,
        source: Permanent,
        battlefield: Iterable[Permanent],
    ) -> int:
        synthetic_ability = TriggeredAbility(
            ability_type="additional_nonland_mana",
            event="nonland_permanent_tapped_for_mana",
            parameters={},
        )

        return self._trigger_engine.count_triggers(
            source=source,
            ability=synthetic_ability,
            battlefield=battlefield,
        )

    def _resolve_additional_mana(
        self,
        *,
        ability: StaticAbility,
        source: Permanent,
        produced_mana: Mapping[Mana, int],
        selected_mana: Mana,
    ) -> tuple[Mana | None, int]:
        if ability.ability_type != self.ADDITIONAL_NONLAND_MANA:
            return None, 0

        parameters = ability.parameters or {}

        if not self._matches_source_filter(
            source=source,
            parameters=parameters,
        ):
            return None, 0

        additional_amount = self._read_additional_amount(
            parameters
        )
        mana_type = self._select_additional_mana_type(
            parameters=parameters,
            produced_mana=produced_mana,
            selected_mana=selected_mana,
        )

        return mana_type, additional_amount

    @staticmethod
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
                "source_filter must be a mapping."
            )

        permanent_type = raw_source_filter.get(
            "permanent_type"
        )

        if permanent_type is None:
            return True

        if not isinstance(permanent_type, str):
            raise ValueError(
                "source_filter.permanent_type must be a string."
            )

        normalized_type = permanent_type.strip().casefold()

        if normalized_type == "nonland":
            return source.is_nonland

        if normalized_type == "land":
            return source.is_land

        raise ValueError(
            "Unsupported source permanent type: "
            f"{permanent_type}"
        )

    @staticmethod
    def _read_additional_amount(
        parameters: Mapping[str, object],
    ) -> int:
        additional_amount = parameters.get(
            "additional_amount",
            0,
        )

        if (
            not isinstance(additional_amount, int)
            or isinstance(additional_amount, bool)
        ):
            raise ValueError(
                "additional_amount must be an integer."
            )

        if additional_amount < 0:
            raise ValueError(
                "additional_amount must not be negative."
            )

        return additional_amount

    @staticmethod
    def _select_additional_mana_type(
        *,
        parameters: Mapping[str, object],
        produced_mana: Mapping[Mana, int],
        selected_mana: Mana,
    ) -> Mana:
        mana_selection = parameters.get(
            "mana_selection",
            "produced_type",
        )

        if not isinstance(mana_selection, str):
            raise ValueError(
                "mana_selection must be a string."
            )

        normalized_selection = mana_selection.strip().casefold()

        if normalized_selection != "produced_type":
            raise ValueError(
                "Unsupported mana selection mode: "
                f"{mana_selection}"
            )

        if selected_mana not in produced_mana:
            raise ValueError(
                "Selected mana was not produced by the source: "
                f"{selected_mana}"
            )

        return selected_mana