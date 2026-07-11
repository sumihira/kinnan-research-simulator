from __future__ import annotations

import random

from krs.actions.action import Action
from krs.actions.bottom_cards import BottomCardsAction
from krs.actions.draw import DrawAction
from krs.actions.mulligan import MulliganAction
from krs.game.game_state import GameState
from krs.game.player import Player


class ActionExecutor:
    """
    Applies Action objects to GameState.

    Only ActionExecutor and GameEngine may mutate game state.
    """

    OPENING_HAND_SIZE = 7

    def execute(
        self,
        state: GameState,
        action: Action,
    ) -> None:
        if isinstance(action, DrawAction):
            self._execute_draw(state, action)
            return

        if isinstance(action, MulliganAction):
            self._execute_mulligan(state, action)
            return

        if isinstance(action, BottomCardsAction):
            self._execute_bottom_cards(state, action)
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

    def _execute_mulligan(
        self,
        state: GameState,
        action: MulliganAction,
    ) -> None:
        player = self._get_player(state, action.player_id)

        total_available = len(player.hand) + len(player.library)

        if total_available < self.OPENING_HAND_SIZE:
            raise IndexError(
                "Not enough cards to draw a new opening hand."
            )

        original_hand = list(player.hand)

        player.library.cards.extend(original_hand)
        player.hand.clear()

        rng = self._create_action_rng(
            state=state,
            player=player,
            action=action,
        )
        player.library.shuffle(rng)

        new_hand = player.library.draw_many(
            self.OPENING_HAND_SIZE
        )

        for card in new_hand:
            player.hand.add(card)

        player.mulligan_count += 1
        state.action_count += 1

    def _execute_bottom_cards(
        self,
        state: GameState,
        action: BottomCardsAction,
    ) -> None:
        player = self._get_player(state, action.player_id)

        if len(action.card_ids) != player.mulligan_count:
            raise ValueError(
                "Number of bottomed cards must equal mulligan count."
            )

        hand_by_id = {
            card.id: card
            for card in player.hand
        }

        missing_ids = [
            card_id
            for card_id in action.card_ids
            if card_id not in hand_by_id
        ]

        if missing_ids:
            raise ValueError(
                f"Cards not found in hand: {missing_ids}"
            )

        selected_cards = [
            hand_by_id[card_id]
            for card_id in action.card_ids
        ]

        for card in selected_cards:
            player.hand.remove(card)

        player.library.put_many_on_bottom(selected_cards)
        state.action_count += 1

    @staticmethod
    def _create_action_rng(
        state: GameState,
        player: Player,
        action: Action,
    ) -> random.Random:
        if state.seed is None:
            return random.Random()

        derived_seed = (
            state.seed
            + player.player_id
            + player.mulligan_count
            + action.turn_number
        )

        return random.Random(derived_seed)

    @staticmethod
    def _get_player(
        state: GameState,
        player_id: int,
    ) -> Player:
        for player in state.players:
            if player.player_id == player_id:
                return player

        raise ValueError(f"Player not found: {player_id}")