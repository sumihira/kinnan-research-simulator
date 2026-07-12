from __future__ import annotations

from krs.decks.deck import Deck
from krs.game.game_state import GameState
from krs.game.player import Player


class GameStateFactory:
    """
    Builds initial GameState objects from deck definitions.
    """

    def create_goldfish_state(
        self,
        deck: Deck,
        *,
        game_id: int = 0,
        seed: int | None = None,
        player_id: int = 0,
        player_name: str = "Player",
    ) -> GameState:
        player = Player(
            player_id=player_id,
            name=player_name,
            commander_card_id=deck.commander.id,
        )

        player.command.add(
            deck.commander
        )

        player.library.cards.extend(
            deck.cards
        )

        return GameState(
            players=[player],
            game_id=game_id,
            seed=seed,
        )