from __future__ import annotations

import random
from collections.abc import Mapping

from krs.actions.activate_kinnan import ActivateKinnanAction
from krs.cards.card import Card
from krs.commanders.kinnan import is_kinnan
from krs.commanders.kinnan_ability import (
    KINNAN_ACTIVATION_COST,
    KINNAN_LOOK_COUNT,
    find_selected_hit,
)
from krs.engine.battlefield_entry_engine import (
    BattlefieldEntryEngine,
)
from krs.game.game_state import GameState
from krs.game.permanent import Permanent
from krs.game.player import Player


class KinnanResolutionEngine:
    """Validates and resolves Kinnan's activated ability."""

    def __init__(
        self,
        battlefield_entry_engine: (
            BattlefieldEntryEngine | None
        ) = None,
    ) -> None:
        self._battlefield_entry_engine = (
            battlefield_entry_engine
            or BattlefieldEntryEngine()
        )

    def execute(
        self,
        *,
        state: GameState,
        action: ActivateKinnanAction,
    ) -> None:
        """Resolve Kinnan's activated ability."""
        player = self._get_player(
            state=state,
            player_id=action.player_id,
        )

        if not state.started:
            raise ValueError(
                "Cannot activate Kinnan before the game starts."
            )

        if state.game_over:
            raise ValueError(
                "Cannot activate Kinnan in a finished game."
            )

        source = self._find_permanent_on_battlefield(
            player=player,
            permanent_id=action.source_permanent_id,
        )

        if source.controller_id != player.player_id:
            raise ValueError(
                "Player does not control the Kinnan source."
            )

        if not is_kinnan(source):
            raise ValueError(
                "Source permanent is not Kinnan: "
                f"{source.effective_card.name}"
            )

        if not player.mana_pool.can_pay(
            KINNAN_ACTIVATION_COST
        ):
            raise ValueError(
                "Kinnan activation cost cannot be paid."
            )

        reveal_count = min(
            KINNAN_LOOK_COUNT,
            len(player.library),
        )
        revealed_cards = player.library.peek(
            reveal_count
        )

        selected_card = find_selected_hit(
            revealed_cards=revealed_cards,
            selected_card_id=action.selected_card_id,
        )

        selected_permanent = (
            self._create_selected_permanent(
                state=state,
                player=player,
                selected_card=selected_card,
            )
        )

        if selected_permanent is not None:
            self._battlefield_entry_engine.validate(
                permanent=selected_permanent,
                controller=player,
                chosen_values=self._chosen_values(
                    action=action,
                    selected_card=selected_card,
                ),
            )

        player.mana_pool.pay(
            KINNAN_ACTIVATION_COST
        )

        removed_cards = player.library.draw_many(
            reveal_count
        )
        remaining_cards = list(removed_cards)

        if selected_card is not None:
            remaining_cards.remove(selected_card)

        rng = self._create_resolution_rng(
            state=state,
            action=action,
        )
        rng.shuffle(remaining_cards)

        player.library.put_many_on_bottom(
            remaining_cards
        )

        if selected_permanent is not None:
            self._battlefield_entry_engine.enter(
                state=state,
                controller=player,
                permanent=selected_permanent,
            )

        if selected_card is not None:
            state.kinnan_chain.record_hit(
                selected_card.id,
                turn=state.turn_number,
            )
        else:
            state.kinnan_chain.record_miss()

        state.mana_spent += (
            KINNAN_ACTIVATION_COST.total
        )
        state.action_count += 1

    @classmethod
    def _create_selected_permanent(
        cls,
        *,
        state: GameState,
        player: Player,
        selected_card: Card | None,
    ) -> Permanent | None:
        if selected_card is None:
            return None

        return Permanent(
            permanent_id=state.next_permanent_id,
            card=selected_card,
            owner_id=player.player_id,
            controller_id=player.player_id,
            tapped=False,
            summoning_sick=cls._is_creature_card(
                selected_card
            ),
            entered_turn=state.turn_number,
        )

    @classmethod
    def _chosen_values(
        cls,
        *,
        action: ActivateKinnanAction,
        selected_card: Card | None,
    ) -> Mapping[str, str]:
        """
        Resolve choices required when a Kinnan hit enters the battlefield.

        Explicit choices carried by the Action take priority. When the
        Action provides no value, deterministic Goldfish choices are added
        for cards that require an enters-the-battlefield choice.

        Roaming Throne chooses Druid so its chosen creature type matches
        Kinnan, Bonder Prodigy.
        """
        raw_chosen_values = getattr(
            action,
            "chosen_values",
            {},
        )

        if not isinstance(raw_chosen_values, Mapping):
            raise ValueError(
                "Kinnan chosen_values must be a mapping."
            )

        chosen_values = cls._normalize_chosen_values(
            raw_chosen_values
        )

        if (
            selected_card is not None
            and selected_card.name == "Roaming Throne"
        ):
            chosen_values.setdefault(
                "creature_type",
                "Druid",
            )

        return chosen_values
    
    @staticmethod
    def _normalize_chosen_values(
        chosen_values: Mapping[object, object],
    ) -> dict[str, str]:
        """
        Validate and normalize choices before battlefield entry.

        Keys and values must be non-empty strings. Whitespace is stripped
        so the values match CastSpellAction's normalization behavior.
        """
        normalized_values: dict[str, str] = {}

        for raw_key, raw_value in chosen_values.items():
            if (
                not isinstance(raw_key, str)
                or not raw_key.strip()
            ):
                raise ValueError(
                    "Kinnan chosen value key must be "
                    "a non-empty string."
                )

            if (
                not isinstance(raw_value, str)
                or not raw_value.strip()
            ):
                raise ValueError(
                    "Kinnan chosen value must be "
                    "a non-empty string."
                )

            normalized_values[raw_key.strip()] = (
                raw_value.strip()
            )

        return normalized_values

    @staticmethod
    def _create_resolution_rng(
        *,
        state: GameState,
        action: ActivateKinnanAction,
    ) -> random.Random:
        if state.seed is None:
            return random.Random()

        derived_seed = (
            state.seed
            + action.player_id
            + action.turn_number
            + state.action_count
        )

        return random.Random(derived_seed)

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

    @staticmethod
    def _find_permanent_on_battlefield(
        *,
        player: Player,
        permanent_id: int,
    ) -> Permanent:
        for permanent in player.battlefield:
            if permanent.permanent_id == permanent_id:
                return permanent

        raise ValueError(
            "Permanent not found on battlefield: "
            f"{permanent_id}"
        )

    @staticmethod
    def _card_types(
        card: Card,
    ) -> set[str]:
        type_part = card.type_line.split(
            " — ",
            maxsplit=1,
        )[0]

        return set(type_part.split())

    @classmethod
    def _is_creature_card(
        cls,
        card: Card,
    ) -> bool:
        return "Creature" in cls._card_types(card)