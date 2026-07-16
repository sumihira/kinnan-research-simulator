from __future__ import annotations

from dataclasses import dataclass

from krs.actions.play_land import PlayLandAction
from krs.cards.card import Card
from krs.game.game_state import GameState
from krs.game.player import Player
from krs.mana.mana import Mana


@dataclass(frozen=True, slots=True)
class LandActionFactory:
    """
    Creates a land-play action for the active player's main phase.

    Land selection prioritizes access to Kinnan's blue-green color
    requirements. The factory does not mutate GameState.
    """

    def create(
        self,
        *,
        state: GameState,
        player_id: int,
    ) -> PlayLandAction | None:
        """
        Create a PlayLandAction for the best available land.

        None is returned when:
        - the player cannot be found;
        - a land has already been played this turn;
        - the hand contains no land.
        """
        player = self._find_player(
            state=state,
            player_id=player_id,
        )

        if player.land_played_this_turn >= 1:
            return None

        lands = tuple(
            card
            for card in player.hand
            if self._is_land(card)
        )

        if not lands:
            return None

        selected_land = min(
            lands,
            key=self._selection_key,
        )

        return PlayLandAction(
            player_id=player.player_id,
            turn_number=state.turn_number,
            card=selected_land,
        )

    @classmethod
    def _selection_key(
        cls,
        card: Card,
    ) -> tuple[
        int,
        int,
        int,
        int,
        str,
        str,
    ]:
        """
        Return a deterministic sorting key.

        Lower tuple values have higher priority.
        """
        produced_mana = cls._produced_mana(card)

        produces_blue = Mana.BLUE in produced_mana
        produces_green = Mana.GREEN in produced_mana
        produces_both = produces_blue and produces_green

        total_amount = sum(
            produced_mana.values()
        )

        return (
            0 if produces_both else 1,
            0 if produces_green else 1,
            0 if produces_blue else 1,
            -len(produced_mana),
            -total_amount,
            card.name.casefold(),
            card.id,
        )

    @classmethod
    def _produced_mana(
        cls,
        card: Card,
    ) -> dict[Mana, int]:
        """
        Resolve the mana types a land can produce.

        Explicit config/cards ManaAbility definitions take priority.
        Otherwise, basic land types are used.
        """
        configured_mana: dict[Mana, int] = {}

        for ability in card.mana_abilities:
            for mana, amount in ability.produced_mana.items():
                configured_mana[mana] = max(
                    configured_mana.get(mana, 0),
                    amount,
                )

        if configured_mana:
            return configured_mana

        return cls._basic_land_type_mana(card)

    @staticmethod
    def _basic_land_type_mana(
        card: Card,
    ) -> dict[Mana, int]:
        if " — " not in card.type_line:
            return {}

        subtype_part = card.type_line.split(
            " — ",
            maxsplit=1,
        )[1]

        subtype_to_mana = {
            "Plains": Mana.WHITE,
            "Island": Mana.BLUE,
            "Swamp": Mana.BLACK,
            "Mountain": Mana.RED,
            "Forest": Mana.GREEN,
        }

        return {
            mana: 1
            for subtype, mana in subtype_to_mana.items()
            if subtype in subtype_part.split()
        }

    @staticmethod
    def _is_land(
        card: Card,
    ) -> bool:
        card_types = card.type_line.split(
            " — ",
            maxsplit=1,
        )[0].split()

        return "Land" in card_types

    @staticmethod
    def _find_player(
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