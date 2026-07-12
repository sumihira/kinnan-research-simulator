from __future__ import annotations

from krs.actions.activate_kinnan import ActivateKinnanAction
from krs.game.game_state import GameState


class KinnanAbilityExecutor:
    """Executes Kinnan-specific activated abilities."""

    def execute(
        self,
        state: GameState,
        action: ActivateKinnanAction,
    ) -> None:
        """
        Execute Kinnan activation.

        Implementation is moved from ActionExecutor
        without behavior changes.
        """
        raise NotImplementedError