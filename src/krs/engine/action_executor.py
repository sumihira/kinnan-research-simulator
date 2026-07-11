from __future__ import annotations

from krs.actions.action import Action
from krs.actions.draw import DrawAction
from krs.game.game_state import GameState


class ActionExecutor:
    """
    Applies Action objects to GameState.

    Only ActionExecutor and GameEngine may mutate game state.
    """

    def execute(
        self,
        state: GameState,
        action: Action,
    ) -> None:
        if isinstance(action, DrawAction):
            self._execute_draw(state, action)
            return

        raise NotImplementedError(
            f"Unsupported action type: {type(action).__name__}"
        )

    def _execute_draw(
        self,
        state: GameState,
        action: DrawAction,
    ) -> None:
        player = self._get_player(state, action.player_id)

        cards = player.library.draw_many(action.amount)

        for card in cards:
            player.hand.add(card)

        state.action_count += 1

    @staticmethod
    def _get_player(
        state: GameState,
        player_id: int,
    ):
        for player in state.players:
            if player.player_id == player_id:
                return player

        raise ValueError(f"Player not found: {player_id}")