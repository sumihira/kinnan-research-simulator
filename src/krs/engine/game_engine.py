from __future__ import annotations

from krs.actions.draw import DrawAction
from krs.engine.action_executor import ActionExecutor
from krs.game.game_state import GameState


class GameEngine:
    """
    Coordinates game flow.

    GameEngine creates and executes Actions through ActionExecutor.
    It does not directly manipulate player zones.
    """

    INITIAL_HAND_SIZE = 7

    def __init__(
        self,
        action_executor: ActionExecutor | None = None,
    ) -> None:
        self._action_executor = action_executor or ActionExecutor()

    def start_game(self, state: GameState) -> None:
        """
        Start a game and draw the opening hand for every player.

        Version 1 does not perform mulligans yet.
        """
        if not state.players:
            raise ValueError("Cannot start a game without players.")
        
        if state.started:
            raise ValueError("Game has already started.")

        if state.game_over:
            raise ValueError("Cannot start a finished game.")

        for player in state.players:
            self._action_executor.execute(
                state,
                DrawAction(
                    player_id=player.player_id,
                    turn_number=state.turn_number,
                    amount=self.INITIAL_HAND_SIZE,
                ),
            )

        state.started = True