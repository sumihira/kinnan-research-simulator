from __future__ import annotations

from krs.actions.activate_kinnan import ActivateKinnanAction
from krs.ai.kinnan_hit_selector import KinnanHitSelector
from krs.commanders.kinnan_ability import KINNAN_LOOK_COUNT
from krs.game.game_state import GameState
from krs.game.player import Player


class KinnanActionFactory:
    """Creates Kinnan activation actions using AI hit selection."""

    def __init__(
        self,
        hit_selector: KinnanHitSelector | None = None,
    ) -> None:
        self._hit_selector = (
            hit_selector
            or KinnanHitSelector()
        )

    def create(
        self,
        *,
        state: GameState,
        player_id: int,
        source_permanent_id: int,
    ) -> ActivateKinnanAction:
        """
        Create a Kinnan activation action for the current game state.

        This method reads the current library but does not modify any
        game state or zone.
        """
        player = self._get_player(
            state=state,
            player_id=player_id,
        )

        reveal_count = min(
            KINNAN_LOOK_COUNT,
            len(player.library),
        )
        revealed_cards = player.library.peek(
            reveal_count
        )

        selected_card = self._hit_selector.select(
            revealed_cards
        )

        return ActivateKinnanAction(
            player_id=player_id,
            turn_number=state.turn_number,
            source_permanent_id=source_permanent_id,
            selected_card_id=(
                selected_card.id
                if selected_card is not None
                else None
            ),
        )

    @staticmethod
    def _get_player(
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