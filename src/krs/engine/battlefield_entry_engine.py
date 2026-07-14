from __future__ import annotations

from collections.abc import Mapping

from krs.engine.etb_ability_engine import EtbAbilityEngine
from krs.engine.replacement_ability_engine import (
    ReplacementAbilityEngine,
)
from krs.game.game_state import GameState
from krs.game.permanent import Permanent
from krs.game.player import Player


class BattlefieldEntryEngine:
    """Validates and executes battlefield entry processing."""

    def __init__(
        self,
        replacement_ability_engine: (
            ReplacementAbilityEngine | None
        ) = None,
        etb_ability_engine: EtbAbilityEngine | None = None,
    ) -> None:
        self._replacement_ability_engine = (
            replacement_ability_engine
            or ReplacementAbilityEngine()
        )
        self._etb_ability_engine = (
            etb_ability_engine
            or EtbAbilityEngine()
        )

    def validate(
        self,
        *,
        permanent: Permanent,
        controller: Player,
        chosen_values: Mapping[str, str] | None = None,
    ) -> None:
        """
        Apply entry replacements and validate ETB abilities.

        The permanent is not added to the battlefield by this method.
        Runtime zones, mana, and GameState counters are not modified.
        """
        self._replacement_ability_engine.apply_enters_battlefield_replacements(
            permanent=permanent,
            chosen_values=chosen_values or {},
        )

        self._etb_ability_engine.validate(
            permanent=permanent,
            controller=controller,
        )

    def enter(
        self,
        *,
        state: GameState,
        controller: Player,
        permanent: Permanent,
    ) -> None:
        """
        Put a previously validated permanent onto the battlefield.

        Replacement abilities and ETB validation must be performed by
        validate() before this method is called.
        """
        controller.battlefield.add(permanent)

        self._etb_ability_engine.execute(
            permanent=permanent,
            controller=controller,
        )

        state.next_permanent_id += 1