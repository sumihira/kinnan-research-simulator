from __future__ import annotations

from collections.abc import Mapping

from krs.abilities.replacement import ReplacementAbility
from krs.game.permanent import Permanent


class ReplacementAbilityEngine:
    """Applies replacement abilities to runtime permanents."""

    CHOOSE_CREATURE_TYPE = "choose_creature_type"
    ENTERS_BATTLEFIELD = "enters_battlefield"

    def apply_enters_battlefield_replacements(
        self,
        *,
        permanent: Permanent,
        chosen_values: Mapping[str, str],
    ) -> None:
        """
        Apply replacement abilities before a permanent enters.

        The permanent is not added to the battlefield by this method.
        """
        for ability in (
            permanent.effective_card.replacement_abilities
        ):
            if ability.event != self.ENTERS_BATTLEFIELD:
                continue

            self._apply_replacement(
                permanent=permanent,
                ability=ability,
                chosen_values=chosen_values,
            )

    def _apply_replacement(
        self,
        *,
        permanent: Permanent,
        ability: ReplacementAbility,
        chosen_values: Mapping[str, str],
    ) -> None:
        if ability.ability_type == self.CHOOSE_CREATURE_TYPE:
            self._apply_choose_creature_type(
                permanent=permanent,
                ability=ability,
                chosen_values=chosen_values,
            )
            return

        raise NotImplementedError(
            "Unsupported replacement ability type: "
            f"{ability.ability_type}"
        )

    @staticmethod
    def _apply_choose_creature_type(
        *,
        permanent: Permanent,
        ability: ReplacementAbility,
        chosen_values: Mapping[str, str],
    ) -> None:
        parameters = ability.parameters or {}
        choice_type = parameters.get("choice_type")

        if not isinstance(choice_type, str) or not choice_type.strip():
            raise ValueError(
                "choice_type must be a non-empty string."
            )

        normalized_choice_type = choice_type.strip()
        chosen_value = chosen_values.get(normalized_choice_type)

        if chosen_value is None:
            raise ValueError(
                "Required chosen value was not provided: "
                f"{normalized_choice_type}"
            )

        if not isinstance(chosen_value, str) or not chosen_value.strip():
            raise ValueError(
                "Chosen creature type must be a non-empty string."
            )

        permanent.chosen_values[normalized_choice_type] = (
            chosen_value.strip()
        )