from __future__ import annotations

import random

from krs.actions.draw import DrawAction
from krs.engine.action_executor import ActionExecutor
from krs.game.game_state import GameState
from krs.game.phase import Phase
from krs.game.turn import Turn

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

    def start_turn(self, state: GameState) -> None:
        """
        Start the active player's turn.

        Resets turn-specific player state, untaps permanents,
        and removes summoning sickness from permanents that
        entered before the current turn.
        """
        self._validate_running_game(state)

        player = state.active_player

        if player is None:
            raise ValueError("Active player could not be resolved.")

        state.phase = Phase.UNTAP

        player.land_played_this_turn = 0
        player.mana_pool.clear()

        for permanent in player.battlefield:
            permanent.tapped = False

            if permanent.entered_turn < state.turn_number:
                permanent.summoning_sick = False


    def advance_phase(self, state: GameState) -> None:
        """
        Advance to the next phase in the current turn.

        Entering the draw phase automatically draws one card
        for the active player.
        """
        self._validate_running_game(state)

        if state.phase is Phase.END:
            raise ValueError(
                "Cannot advance beyond END phase. Start a new turn instead."
            )

        next_phase = Turn.next_phase(state.phase)
        state.phase = next_phase

        self._handle_phase_entry(state)

    def _handle_phase_entry(self, state: GameState) -> None:
        """
        Execute automatic processing that occurs when entering a phase.
        """
        if state.phase is Phase.DRAW:
            self._execute_draw_step(state)


    def _execute_draw_step(self, state: GameState) -> None:
        """
        Draw one card for the active player during the draw step.

        Version 1 draws one card on every turn, including turn one.
        """
        player = state.active_player

        if player is None:
            raise ValueError("Active player could not be resolved.")

        self._action_executor.execute(
            state,
            DrawAction(
                player_id=player.player_id,
                turn_number=state.turn_number,
                amount=1,
            ),
        )

    def end_turn(self, state: GameState) -> None:
        """
        End the current turn and begin the next turn.

        Version 1 uses one active player, but active_player_index
        is still advanced for future multiplayer support.
        """
        self._validate_running_game(state)

        if state.phase is not Phase.END:
            raise ValueError(
                "A turn can only end during the END phase."
            )

        for player in state.players:
            player.mana_pool.clear()

        state.turn_number += 1

        if state.players:
            state.active_player_index = (
                state.active_player_index + 1
            ) % len(state.players)

        self.start_turn(state)


    @staticmethod
    def _validate_running_game(state: GameState) -> None:
        if not state.started:
            raise ValueError("Game has not started.")

        if state.game_over:
            raise ValueError("Game has already finished.")

        if not state.players:
            raise ValueError("Game has no players.")
    
    def start_turn(self, state: GameState) -> None:
        """
        Start the active player's turn.

        Resets turn-specific player state, untaps permanents,
        and removes summoning sickness from permanents that
        entered before the current turn.
        """
        self._validate_running_game(state)

        player = state.active_player

        if player is None:
            raise ValueError("Active player could not be resolved.")

        state.phase = Phase.UNTAP

        player.land_played_this_turn = 0
        player.mana_pool.clear()

        for permanent in player.battlefield:
            permanent.tapped = False

            if permanent.entered_turn < state.turn_number:
                permanent.summoning_sick = False


    def advance_phase(self, state: GameState) -> None:
        """
        Advance to the next phase in the current turn.
        """
        self._validate_running_game(state)

        if state.phase is Phase.END:
            raise ValueError(
                "Cannot advance beyond END phase. Start a new turn instead."
            )

        state.phase = Turn.next_phase(state.phase)


    def end_turn(self, state: GameState) -> None:
        """
        End the current turn and begin the next turn.

        Version 1 uses one active player, but active_player_index
        is still advanced for future multiplayer support.
        """
        self._validate_running_game(state)

        if state.phase is not Phase.END:
            raise ValueError(
                "A turn can only end during the END phase."
            )

        for player in state.players:
            player.mana_pool.clear()

        state.turn_number += 1

        if state.players:
            state.active_player_index = (
                state.active_player_index + 1
            ) % len(state.players)

        self.start_turn(state)


    @staticmethod
    def _validate_running_game(state: GameState) -> None:
        if not state.started:
            raise ValueError("Game has not started.")

        if state.game_over:
            raise ValueError("Game has already finished.")

        if not state.players:
            raise ValueError("Game has no players.")