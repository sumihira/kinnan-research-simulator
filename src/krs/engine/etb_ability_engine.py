from __future__ import annotations

from collections.abc import Mapping

from krs.abilities.etb import EtbAbility
from krs.game.permanent import Permanent
from krs.game.player import Player


class EtbAbilityEngine:
    """Validates and executes enters-the-battlefield abilities."""

    DRAW_CARD = "draw_card"

    def validate(
        self,
        *,
        permanent: Permanent,
        controller: Player,
    ) -> None:
        """
        Validate every ETB ability before runtime state changes.

        This method must not modify the player, permanent, or zones.
        """
        for ability in permanent.effective_card.etb_abilities:
            self._validate_ability(
                ability=ability,
                controller=controller,
            )

    def execute(
        self,
        *,
        permanent: Permanent,
        controller: Player,
    ) -> None:
        """Execute every previously validated ETB ability."""
        for ability in permanent.effective_card.etb_abilities:
            self._execute_ability(
                ability=ability,
                controller=controller,
            )

    def _validate_ability(
        self,
        *,
        ability: EtbAbility,
        controller: Player,
    ) -> None:
        if ability.ability_type == self.DRAW_CARD:
            amount = self._read_positive_amount(
                ability.parameters,
            )

            if len(controller.library) < amount:
                raise IndexError(
                    "Not enough cards in library for ETB draw."
                )

            return

        raise NotImplementedError(
            "Unsupported ETB ability type: "
            f"{ability.ability_type}"
        )

    def _execute_ability(
        self,
        *,
        ability: EtbAbility,
        controller: Player,
    ) -> None:
        if ability.ability_type == self.DRAW_CARD:
            amount = self._read_positive_amount(
                ability.parameters,
            )
            cards = controller.library.draw_many(amount)

            for card in cards:
                controller.hand.add(card)

            return

        raise NotImplementedError(
            "Unsupported ETB ability type: "
            f"{ability.ability_type}"
        )

    @staticmethod
    def _read_positive_amount(
        parameters: Mapping[str, object] | None,
    ) -> int:
        raw_amount = (parameters or {}).get(
            "amount",
            1,
        )

        if (
            not isinstance(raw_amount, int)
            or isinstance(raw_amount, bool)
        ):
            raise ValueError(
                "ETB draw amount must be an integer."
            )

        if raw_amount <= 0:
            raise ValueError(
                "ETB draw amount must be greater than zero."
            )

        return raw_amount