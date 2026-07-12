from __future__ import annotations

from krs.abilities.activated import ActivatedAbility
from krs.game.permanent import Permanent


class AbilityExecutor:
    """Validates and applies structured activated ability effects."""

    UNTAP_SELF = "untap_self"

    def validate(
        self,
        *,
        source: Permanent,
        ability: ActivatedAbility,
    ) -> None:
        """
        Validate an activated ability before costs are paid.

        This method must not modify runtime state.
        """
        if ability.requires_tap:
            self._validate_tap_cost(
                source=source,
            )

        if ability.ability_type == self.UNTAP_SELF:
            self._validate_untap_self(
                source=source,
            )
            return

        raise NotImplementedError(
            "Unsupported activated ability type: "
            f"{ability.ability_type}"
        )

    def execute(
        self,
        *,
        source: Permanent,
        ability: ActivatedAbility,
    ) -> None:
        """Apply an already validated activated ability effect."""

        if ability.requires_tap:
            source.tapped = True

        if ability.ability_type == self.UNTAP_SELF:
            source.tapped = False
            return

        raise NotImplementedError(
            "Unsupported activated ability type: "
            f"{ability.ability_type}"
        )

    @staticmethod
    def _validate_tap_cost(
        *,
        source: Permanent,
    ) -> None:
        if source.tapped:
            raise ValueError(
                "Tapped permanent cannot pay a tap activation cost: "
                f"{source.effective_card.name}"
            )

        if (
            source.is_creature
            and not source.can_activate_tap_ability
        ):
            raise ValueError(
                "Summoning-sick creature cannot activate "
                f"a tap ability: {source.effective_card.name}"
            )

    @staticmethod
    def _validate_untap_self(
        *,
        source: Permanent,
    ) -> None:
        if not source.tapped:
            raise ValueError(
                "Permanent is already untapped: "
                f"{source.effective_card.name}"
            )