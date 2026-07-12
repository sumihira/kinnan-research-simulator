from __future__ import annotations

from collections.abc import Mapping

from krs.abilities.activated import ActivatedAbility
from krs.abilities.mana_ability import ManaAbility
from krs.abilities.replacement import ReplacementAbility
from krs.abilities.static import StaticAbility
from krs.abilities.triggered import TriggeredAbility
from krs.mana.mana import Mana


class AbilityFactory:
    """Creates structured abilities from card configuration data."""

    @staticmethod
    def create_mana_ability(
        definition: Mapping[str, object],
    ) -> ManaAbility:
        """Create a mana ability from a YAML definition."""

        raw_produces = definition.get("produces")

        if not isinstance(raw_produces, Mapping):
            raise ValueError(
                "Mana ability requires a produces mapping."
            )

        produced_mana: dict[Mana, int] = {}

        for raw_mana, raw_amount in raw_produces.items():
            if not isinstance(raw_mana, str):
                raise ValueError(
                    "Produced mana name must be a string."
                )

            if (
                not isinstance(raw_amount, int)
                or isinstance(raw_amount, bool)
            ):
                raise ValueError(
                    "Produced mana amount must be an integer."
                )

            if raw_amount <= 0:
                raise ValueError(
                    "Produced mana amount must be greater than zero."
                )

            normalized_mana = raw_mana.strip().upper()

            try:
                mana = Mana[normalized_mana]
            except KeyError as error:
                raise ValueError(
                    f"Unknown mana type: {raw_mana}"
                ) from error

            produced_mana[mana] = raw_amount

        requires_tap = definition.get(
            "requires_tap",
            True,
        )

        if not isinstance(requires_tap, bool):
            raise ValueError(
                "requires_tap must be a boolean."
            )

        return ManaAbility(
            produced_mana=produced_mana,
            requires_tap=requires_tap,
        )

    @staticmethod
    def create_activated_ability(
        definition: Mapping[str, object],
    ) -> ActivatedAbility:
        """Create an activated ability from a YAML definition."""

        return ActivatedAbility(
            ability_type=AbilityFactory._required_string(
                definition,
                "ability_type",
            ),
            mana_cost=AbilityFactory._optional_string(
                definition,
                "mana_cost",
            ),
            requires_tap=AbilityFactory._optional_bool(
                definition,
                "requires_tap",
                default=False,
            ),
            parameters=AbilityFactory._parameters(definition),
        )

    @staticmethod
    def create_static_ability(
        definition: Mapping[str, object],
    ) -> StaticAbility:
        """Create a static ability from a YAML definition."""

        return StaticAbility(
            ability_type=AbilityFactory._required_string(
                definition,
                "ability_type",
            ),
            parameters=AbilityFactory._parameters(definition),
        )

    @staticmethod
    def create_triggered_ability(
        definition: Mapping[str, object],
    ) -> TriggeredAbility:
        """Create a triggered ability from a YAML definition."""

        return TriggeredAbility(
            ability_type=AbilityFactory._required_string(
                definition,
                "ability_type",
            ),
            event=AbilityFactory._required_string(
                definition,
                "event",
            ),
            parameters=AbilityFactory._parameters(definition),
        )

    @staticmethod
    def create_replacement_ability(
        definition: Mapping[str, object],
    ) -> ReplacementAbility:
        """Create a replacement ability from a YAML definition."""

        return ReplacementAbility(
            ability_type=AbilityFactory._required_string(
                definition,
                "ability_type",
            ),
            event=AbilityFactory._required_string(
                definition,
                "event",
            ),
            parameters=AbilityFactory._parameters(definition),
        )

    @staticmethod
    def _required_string(
        definition: Mapping[str, object],
        field_name: str,
    ) -> str:
        value = definition.get(field_name)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"{field_name} must be a non-empty string."
            )

        return value.strip()

    @staticmethod
    def _optional_string(
        definition: Mapping[str, object],
        field_name: str,
    ) -> str:
        value = definition.get(field_name, "")

        if not isinstance(value, str):
            raise ValueError(
                f"{field_name} must be a string."
            )

        return value.strip()

    @staticmethod
    def _optional_bool(
        definition: Mapping[str, object],
        field_name: str,
        *,
        default: bool,
    ) -> bool:
        value = definition.get(field_name, default)

        if not isinstance(value, bool):
            raise ValueError(
                f"{field_name} must be a boolean."
            )

        return value

    @staticmethod
    def _parameters(
        definition: Mapping[str, object],
    ) -> Mapping[str, object]:
        value = definition.get("parameters", {})

        if not isinstance(value, Mapping):
            raise ValueError(
                "parameters must be a mapping."
            )

        return dict(value)