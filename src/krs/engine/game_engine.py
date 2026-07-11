from __future__ import annotations

import random

from krs.actions.draw import DrawAction
from krs.engine.action_executor import ActionExecutor
from krs.game.game_state import GameState


class GameEngine:
    """
    Coordinates game flow.

    GameEngine creates and executes Actions through ActionExecutor.
    It does not directly manipulate player zones except for
    game setup operations such as shuffling.
    """

    INITIAL_HAND_SIZE = 7

    def __init__(
        self,
        action_executor: ActionExecutor | None = None,
    ) -> None:
        self._action_executor = action_executor or ActionExecutor()

    def start_game(self, state: GameState) -> None:
        """
        Shuffle each player's library and draw an opening hand.

        Version 1 does not perform mulligans yet.
        """
        if not state.players:
            raise ValueError("Cannot start a game without players.")

        if state.started:
            raise ValueError("Game has already started.")

        if state.game_over:
            raise ValueError("Cannot start a finished game.")

        self._validate_opening_libraries(state)

        for player in state.players:
            rng = self._create_player_rng(
                experiment_seed=state.seed,
                player_id=player.player_id,
            )

            player.library.shuffle(rng)

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

    def _validate_opening_libraries(
        self,
        state: GameState,
    ) -> None:
        """
        Validate all libraries before modifying any game state.

        This keeps game start atomic when one player has too few cards.
        """
        for player in state.players:
            if len(player.library) < self.INITIAL_HAND_SIZE:
                raise IndexError("Not enough cards in library.")

    @staticmethod
    def _create_player_rng(
        experiment_seed: int | None,
        player_id: int,
    ) -> random.Random:
        """
        Create a deterministic random generator for one player.

        Different players receive different derived seeds.
        """
        if experiment_seed is None:
            return random.Random()

        derived_seed = experiment_seed + player_id

        return random.Random(derived_seed)