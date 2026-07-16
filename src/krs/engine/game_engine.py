from __future__ import annotations

import random

from krs.actions.activate_kinnan import ActivateKinnanAction
from krs.actions.draw import DrawAction
from krs.actions.play_land import PlayLandAction
from krs.ai.kinnan_action_factory import KinnanActionFactory
from krs.ai.land_action_factory import LandActionFactory
from krs.ai.strategy_factory import StrategyFactory
from krs.commanders.kinnan import is_kinnan
from krs.commanders.kinnan_ability import KINNAN_ACTIVATION_COST
from krs.engine.action_executor import ActionExecutor
from krs.game.game_state import GameState
from krs.game.permanent import Permanent
from krs.game.phase import Phase
from krs.game.player import Player
from krs.game.turn import Turn


class GameEngine:
    """
    Coordinates game flow.

    GameEngine creates and executes Actions through ActionExecutor.
    It does not directly manipulate player zones except for game setup
    operations such as shuffling.
    """

    INITIAL_HAND_SIZE = 7

    def __init__(
        self,
        action_executor: ActionExecutor | None = None,
        kinnan_action_factory: KinnanActionFactory | None = None,
        land_action_factory: LandActionFactory | None = None,
    ) -> None:
        self._action_executor = (
            action_executor or ActionExecutor()
        )
        self._kinnan_action_factory = (
            kinnan_action_factory
            or KinnanActionFactory()
        )
        self._land_action_factory = (
            land_action_factory
            or LandActionFactory()
        )

    def start_game(
        self,
        state: GameState,
    ) -> None:
        """
        Shuffle each player's library and draw an opening hand.

        Version 1 does not perform mulligans yet.
        """
        if not state.players:
            raise ValueError(
                "Cannot start a game without players."
            )

        if state.started:
            raise ValueError(
                "Game has already started."
            )

        if state.game_over:
            raise ValueError(
                "Cannot start a finished game."
            )

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
                raise IndexError(
                    "Not enough cards in library."
                )

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

        derived_seed = (
            experiment_seed + player_id
        )

        return random.Random(
            derived_seed
        )

    def start_turn(
        self,
        state: GameState,
    ) -> None:
        """
        Start the active player's turn.

        Resets turn-specific player state, untaps permanents that can untap
        normally, and removes summoning sickness from permanents that entered
        before the current turn.
        """
        self._validate_running_game(state)

        player = state.active_player

        if player is None:
            raise ValueError(
                "Active player could not be resolved."
            )

        state.phase = Phase.UNTAP
        player.land_played_this_turn = 0
        player.mana_pool.clear()

        for permanent in player.battlefield:
            if self._can_untap_during_untap_step(
                permanent
            ):
                permanent.tapped = False

            if (
                permanent.entered_turn
                < state.turn_number
            ):
                permanent.summoning_sick = False

    def advance_phase(
        self,
        state: GameState,
    ) -> None:
        """
        Advance to the next phase in the current turn.

        Entering the draw phase automatically draws one card for the active
        player.
        """
        self._validate_running_game(state)

        if state.phase is Phase.END:
            raise ValueError(
                "Cannot advance beyond END phase. "
                "Start a new turn instead."
            )

        state.phase = Turn.next_phase(
            state.phase
        )
        self._handle_phase_entry(state)

    def _handle_phase_entry(
        self,
        state: GameState,
    ) -> None:
        """Execute automatic processing when entering a phase."""
        if state.phase is Phase.DRAW:
            self._execute_draw_step(state)

    def _execute_draw_step(
        self,
        state: GameState,
    ) -> None:
        """
        Draw one card for the active player during the draw step.

        Version 1 draws one card on every turn, including turn one.
        """
        player = state.active_player

        if player is None:
            raise ValueError(
                "Active player could not be resolved."
            )

        self._action_executor.execute(
            state,
            DrawAction(
                player_id=player.player_id,
                turn_number=state.turn_number,
                amount=1,
            ),
        )

    def end_turn(
        self,
        state: GameState,
    ) -> None:
        """
        End the current turn and begin the next turn.

        Version 1 uses one active player, but active_player_index is still
        advanced for future multiplayer support.
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
    def _can_untap_during_untap_step(
        permanent: Permanent,
    ) -> bool:
        for ability in (
            permanent
            .effective_card
            .static_abilities
        ):
            if (
                ability.ability_type
                != "skip_normal_untap"
            ):
                continue

            if (
                ability.parameters.get(
                    "applies_during"
                )
                == "untap_step"
            ):
                return False

        return True

    @staticmethod
    def _validate_running_game(
        state: GameState,
    ) -> None:
        if not state.started:
            raise ValueError(
                "Game has not started."
            )

        if state.game_over:
            raise ValueError(
                "Game has already finished."
            )

        if not state.players:
            raise ValueError(
                "Game has no players."
            )

    def create_land_play_action(
        self,
        state: GameState,
        *,
        player_id: int,
    ) -> PlayLandAction | None:
        """
        Create one land-play Action through LandActionFactory.

        None is returned when no land can currently be played.
        This method does not execute the Action.
        """
        self._validate_running_game(state)

        return self._land_action_factory.create(
            state=state,
            player_id=player_id,
        )

    def execute_land_play_if_available(
        self,
        state: GameState,
        *,
        player_id: int,
    ) -> bool:
        """
        Create and execute one land-play Action when available.

        Returns True when a land was played.
        Returns False when no legal land play is available.
        """
        action = self.create_land_play_action(
            state,
            player_id=player_id,
        )

        if action is None:
            return False

        self._action_executor.execute(
            state,
            action,
        )

        return True

    def create_kinnan_activation_action(
        self,
        state: GameState,
        *,
        player_id: int,
        source_permanent_id: int,
    ) -> ActivateKinnanAction:
        """
        Create a Kinnan activation Action through KinnanActionFactory.

        This method does not execute the Action.
        """
        return self._kinnan_action_factory.create(
            state=state,
            player_id=player_id,
            source_permanent_id=(
                source_permanent_id
            ),
        )

    def find_activatable_kinnan(
        self,
        state: GameState,
        *,
        player_id: int,
    ) -> Permanent | None:
        """
        Return the first Kinnan the player can currently activate.

        Kinnan's activated ability does not require tapping the source.
        Therefore, tapped state and summoning sickness do not prevent
        activation. The player must control Kinnan and be able to pay
        the activation cost.
        """
        self._validate_running_game(state)

        player = self._get_player_by_id(
            state=state,
            player_id=player_id,
        )

        if not player.mana_pool.can_pay(
            KINNAN_ACTIVATION_COST
        ):
            return None

        for permanent in player.battlefield:
            if (
                permanent.controller_id
                != player.player_id
            ):
                continue

            if is_kinnan(permanent):
                return permanent

        return None

    def execute_kinnan_activation_if_available(
        self,
        state: GameState,
        *,
        player_id: int,
    ) -> bool:
        """
        Create and execute one Kinnan activation when available.

        Returns True when an activation Action was executed.
        Returns False when the player has no activatable Kinnan.
        """
        source = self.find_activatable_kinnan(
            state,
            player_id=player_id,
        )

        if source is None:
            return False

        action = (
            self.create_kinnan_activation_action(
                state,
                player_id=player_id,
                source_permanent_id=(
                    source.permanent_id
                ),
            )
        )

        self._action_executor.execute(
            state,
            action,
        )

        return True

    @staticmethod
    def _get_player_by_id(
        *,
        state: GameState,
        player_id: int,
    ) -> Player:
        for player in state.players:
            if player.player_id == player_id:
                return player

        raise ValueError(
            f"Player not found: {player_id}"
        )

    @classmethod
    def from_strategy(
        cls,
        strategy_name: str,
        *,
        action_executor: ActionExecutor | None = None,
        strategy_factory: StrategyFactory | None = None,
        land_action_factory: LandActionFactory | None = None,
    ) -> GameEngine:
        """Create a GameEngine configured with an AI strategy."""
        factory = (
            strategy_factory
            or StrategyFactory()
        )
        selector = (
            factory.create_kinnan_hit_selector(
                strategy_name
            )
        )

        return cls(
            action_executor=action_executor,
            kinnan_action_factory=(
                KinnanActionFactory(
                    hit_selector=selector,
                )
            ),
            land_action_factory=land_action_factory,
        )