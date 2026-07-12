from __future__ import annotations

import random

from krs.actions.action import Action
from krs.actions.bottom_cards import BottomCardsAction
from krs.actions.draw import DrawAction
from krs.actions.mulligan import MulliganAction
from krs.game.game_state import GameState
from krs.game.player import Player
from krs.actions.play_land import PlayLandAction
from krs.game.permanent import Permanent
from krs.game.phase import Phase
from krs.actions.tap_permanent import TapPermanentAction
from krs.mana.mana import Mana
from krs.abilities.mana_ability import ManaAbility
from krs.engine.static_ability_engine import StaticAbilityEngine
from krs.actions.cast_spell import CastSpellAction
from krs.cards.card import Card
from krs.actions.cast_commander import CastCommanderAction
from krs.mana.mana_cost import ManaCost
from krs.actions.return_commander import ReturnCommanderAction
from krs.actions.activate_kinnan import ActivateKinnanAction
from krs.commanders.kinnan import is_kinnan
from krs.commanders.kinnan_ability import (
    KINNAN_ACTIVATION_COST,
    KINNAN_LOOK_COUNT,
    find_selected_hit,
)
from krs.actions.activate_ability import ActivateAbilityAction
from krs.abilities.activated import ActivatedAbility

class ActionExecutor:
    """
    Applies Action objects to GameState.

    Only ActionExecutor and GameEngine may mutate game state.
    """

    OPENING_HAND_SIZE = 7

    def __init__(
        self,
        static_ability_engine: StaticAbilityEngine | None = None,
    ) -> None:
        self._static_ability_engine = (
            static_ability_engine
            or StaticAbilityEngine()
        )

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

        if isinstance(action, PlayLandAction):
            self._execute_play_land(state, action)
            return

        if isinstance(action, TapPermanentAction):
            self._execute_tap_permanent(state, action)
            return

        if isinstance(action, CastSpellAction):
            self._execute_cast_spell(state, action)
            return

        if isinstance(action, CastCommanderAction):
            self._execute_cast_commander(state, action)
            return

        if isinstance(action, ReturnCommanderAction):
            self._execute_return_commander(state, action)
            return

        if isinstance(action, ActivateAbilityAction):
            self._execute_activate_ability(state, action)
            return

        if isinstance(action, ActivateKinnanAction):
            self._execute_activate_kinnan(state, action)
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
    
    def _execute_play_land(
        self,
        state: GameState,
        action: PlayLandAction,
    ) -> None:
        player = self._get_player(state, action.player_id)

        if not state.started:
            raise ValueError("Cannot play a land before the game starts.")

        if state.game_over:
            raise ValueError("Cannot play a land in a finished game.")

        if state.phase is not Phase.MAIN:
            raise ValueError("Lands can only be played during the main phase.")

        if player.land_played_this_turn >= 1:
            raise ValueError("A land has already been played this turn.")

        card = self._find_card_in_hand(
            player=player,
            card_id=action.card.id,
        )

        if not self._is_land(card):
            raise ValueError(f"Card is not a land: {card.name}")

        permanent = Permanent(
            permanent_id=state.next_permanent_id,
            card=card,
            owner_id=player.player_id,
            controller_id=player.player_id,
            summoning_sick=False,
            entered_turn=state.turn_number,
        )

        player.hand.remove(card)
        player.battlefield.add(permanent)

        player.land_played_this_turn += 1
        state.next_permanent_id += 1
        state.action_count += 1

    @staticmethod
    def _find_card_in_hand(
        player: Player,
        card_id: str,
    ) -> Card:
        for card in player.hand:
            if card.id == card_id:
                return card

        raise ValueError(
            f"Card not found in hand: {card_id}"
        )

    @staticmethod
    def _is_land(card) -> bool:
        card_types = card.type_line.split(" — ", maxsplit=1)[0].split()

        return "Land" in card_types

    def _execute_tap_permanent(
        self,
        state: GameState,
        action: TapPermanentAction,
    ) -> None:
        player = self._get_player(state, action.player_id)

        if not state.started:
            raise ValueError(
                "Cannot activate a mana ability before the game starts."
            )

        if state.game_over:
            raise ValueError(
                "Cannot activate a mana ability in a finished game."
            )

        permanent = self._find_permanent_on_battlefield(
            player=player,
            permanent_id=action.permanent.permanent_id,
        )

        if permanent.controller_id != player.player_id:
            raise ValueError(
                "Player does not control this permanent."
            )

        if permanent.tapped:
            raise ValueError(
                f"Permanent is already tapped: "
                f"{permanent.effective_card.name}"
            )

        if (
            permanent.is_creature
            and not permanent.can_activate_tap_ability
        ):
            raise ValueError(
                "Summoning-sick creature cannot activate "
                f"a tap ability: {permanent.effective_card.name}"
            )

        if permanent.is_land:
            produced_mana = {
                self._resolve_basic_land_mana(
                    permanent=permanent,
                    selected_mana=action.mana,
                ): 1
            }
        else:
            produced_mana = self._resolve_nonland_mana_ability(
                permanent=permanent,
                selected_mana=action.mana,
                ability_index=action.ability_index,
            )

        permanent.tapped = True

        for mana, amount in produced_mana.items():
            player.mana_pool.add(mana, amount)

        amount_generated = sum(produced_mana.values())

        additional_mana = (
            self._static_ability_engine
            .calculate_additional_nonland_mana(
                source=permanent,
                produced_mana=produced_mana,
                selected_mana=action.mana,
                battlefield=player.battlefield,
            )
        )

        for mana, amount in additional_mana.items():
            player.mana_pool.add(mana, amount)
            amount_generated += amount

        state.mana_generated += amount_generated
        state.action_count += 1

    @staticmethod
    def _find_permanent_on_battlefield(
        player: Player,
        permanent_id: int,
    ) -> Permanent:
        for permanent in player.battlefield:
            if permanent.permanent_id == permanent_id:
                return permanent

        raise ValueError(
            f"Permanent not found on battlefield: {permanent_id}"
        )

    @staticmethod
    def _resolve_basic_land_mana(
        permanent: Permanent,
        selected_mana: Mana,
    ) -> Mana:
        if not permanent.is_land:
            raise ValueError(
                f"Permanent is not a land: "
                f"{permanent.effective_card.name}"
            )

        subtype_part = (
            permanent.effective_card.type_line.split(
                " — ",
                maxsplit=1,
            )[1]
            if " — " in permanent.effective_card.type_line
            else ""
        )

        basic_land_mana = {
            "Plains": Mana.WHITE,
            "Island": Mana.BLUE,
            "Swamp": Mana.BLACK,
            "Mountain": Mana.RED,
            "Forest": Mana.GREEN,
        }

        available_mana = {
            mana
            for subtype, mana in basic_land_mana.items()
            if subtype in subtype_part.split()
        }

        if not available_mana:
            raise ValueError(
                "Land has no supported mana ability: "
                f"{permanent.effective_card.name}"
            )

        if selected_mana not in available_mana:
            raise ValueError(
                f"Land cannot produce selected mana: "
                f"{selected_mana}"
            )

        return selected_mana
    
    @staticmethod
    def _resolve_nonland_mana_ability(
        permanent: Permanent,
        selected_mana: Mana,
        ability_index: int,
    ) -> dict[Mana, int]:
        card = permanent.effective_card

        if not 0 <= ability_index < len(card.mana_abilities):
            raise ValueError(
                f"Mana ability not found at index "
                f"{ability_index}: {card.name}"
            )

        ability: ManaAbility = card.mana_abilities[
            ability_index
        ]

        if not ability.requires_tap:
            raise ValueError(
                "The selected mana ability does not require tapping."
            )

        if not ability.can_produce(selected_mana):
            raise ValueError(
                f"Mana ability cannot produce selected mana: "
                f"{selected_mana}"
            )

        # Version 1では、選択した種類の固定マナをすべて生成する。
        return {
            selected_mana: ability.produced_mana[selected_mana]
        }

    def _execute_cast_spell(
        self,
        state: GameState,
        action: CastSpellAction,
    ) -> None:
        player = self._get_player(
            state,
            action.player_id,
        )

        if not state.started:
            raise ValueError(
                "Cannot cast a spell before the game starts."
            )

        if state.game_over:
            raise ValueError(
                "Cannot cast a spell in a finished game."
            )

        if state.phase is not Phase.MAIN:
            raise ValueError(
                "Permanent spells can only be cast during the main phase."
            )

        card = self._find_card_in_hand(
            player=player,
            card_id=action.card.id,
        )

        if self._is_land_card(card):
            raise ValueError(
                f"Land cards cannot be cast as spells: {card.name}"
            )

        if not self._is_permanent_card(card):
            raise ValueError(
                "Only permanent spells are supported: "
                f"{card.name}"
            )

        # 支払い可能性を先に検証する。
        # pay() は失敗時にManaPoolを変更しない。
        if not player.mana_pool.can_pay(action.cost):
            raise ValueError(
                f"Mana cost cannot be paid for: {card.name}"
            )

        player.mana_pool.pay(action.cost)

        permanent = Permanent(
            permanent_id=state.next_permanent_id,
            card=card,
            owner_id=player.player_id,
            controller_id=player.player_id,
            tapped=False,
            summoning_sick=self._is_creature_card(card),
            entered_turn=state.turn_number,
        )

        player.hand.remove(card)
        player.battlefield.add(permanent)

        state.next_permanent_id += 1
        state.mana_spent += action.cost.total
        state.action_count += 1

    @staticmethod
    def _card_types(card: Card) -> set[str]:
        type_part = card.type_line.split(
            " — ",
            maxsplit=1,
        )[0]

        return set(type_part.split())


    @classmethod
    def _is_land_card(
        cls,
        card: Card,
    ) -> bool:
        return "Land" in cls._card_types(card)


    @classmethod
    def _is_creature_card(
        cls,
        card: Card,
    ) -> bool:
        return "Creature" in cls._card_types(card)


    @classmethod
    def _is_permanent_card(
        cls,
        card: Card,
    ) -> bool:
        permanent_types = {
            "Artifact",
            "Battle",
            "Creature",
            "Enchantment",
            "Planeswalker",
        }

        return bool(
            cls._card_types(card) & permanent_types
        )

    def _execute_cast_commander(
        self,
        state: GameState,
        action: CastCommanderAction,
    ) -> None:
        player = self._get_player(
            state,
            action.player_id,
        )

        if not state.started:
            raise ValueError(
                "Cannot cast a commander before the game starts."
            )

        if state.game_over:
            raise ValueError(
                "Cannot cast a commander in a finished game."
            )

        if state.phase is not Phase.MAIN:
            raise ValueError(
                "Commander can only be cast during the main phase."
            )

        commander = self._find_card_in_command_zone(
            player=player,
            card_id=action.card.id,
        )

        if not self._is_permanent_card(commander):
            raise ValueError(
                "Only permanent commanders are currently supported: "
                f"{commander.name}"
            )

        total_cost = self._apply_commander_tax(
            base_cost=action.base_cost,
            commander_cast_count=player.commander_cast_count,
        )

        if not player.mana_pool.can_pay(total_cost):
            raise ValueError(
                f"Commander mana cost cannot be paid for: "
                f"{commander.name}"
            )

        player.mana_pool.pay(total_cost)

        permanent = Permanent(
            permanent_id=state.next_permanent_id,
            card=commander,
            owner_id=player.player_id,
            controller_id=player.player_id,
            tapped=False,
            summoning_sick=self._is_creature_card(commander),
            entered_turn=state.turn_number,
        )

        player.command.remove(commander)
        player.battlefield.add(permanent)

        player.commander_cast_count += 1

        state.next_permanent_id += 1
        state.mana_spent += total_cost.total
        state.action_count += 1

    @staticmethod
    def _find_card_in_command_zone(
        player: Player,
        card_id: str,
    ) -> Card:
        for card in player.command:
            if card.id == card_id:
                return card

        raise ValueError(
            f"Commander not found in command zone: {card_id}"
        )


    @staticmethod
    def _apply_commander_tax(
        base_cost: ManaCost,
        commander_cast_count: int,
    ) -> ManaCost:
        if commander_cast_count < 0:
            raise ValueError(
                "Commander cast count must not be negative."
            )

        return ManaCost(
            generic=(
                base_cost.generic
                + commander_cast_count * 2
            ),
            white=base_cost.white,
            blue=base_cost.blue,
            black=base_cost.black,
            red=base_cost.red,
            green=base_cost.green,
            colorless=base_cost.colorless,
        )
    
    def _execute_activate_ability(
        self,
        state: GameState,
        action: ActivateAbilityAction,
    ) -> None:
        player = self._get_player(
            state,
            action.player_id,
        )

        if not state.started:
            raise ValueError(
                "Cannot activate an ability before the game starts."
            )

        if state.game_over:
            raise ValueError(
                "Cannot activate an ability in a finished game."
            )

        source = self._find_permanent_on_battlefield(
            player=player,
            permanent_id=action.source.permanent_id,
        )

        if source.controller_id != player.player_id:
            raise ValueError(
                "Player does not control the ability source."
            )

        ability = self._find_activated_ability(
            source=source,
            ability_index=action.ability_index,
        )
        cost = self._parse_activated_ability_cost(
            ability.mana_cost
        )

        if not player.mana_pool.can_pay(cost):
            raise ValueError(
                "Activated ability cost cannot be paid: "
                f"{source.effective_card.name}"
            )

        self._validate_activated_ability(
            source=source,
            ability=ability,
        )

        player.mana_pool.pay(cost)

        self._apply_activated_ability(
            source=source,
            ability=ability,
        )

        state.mana_spent += cost.total
        state.action_count += 1

    @staticmethod
    def _find_activated_ability(
        source: Permanent,
        ability_index: int,
    ) -> ActivatedAbility:
        abilities = source.effective_card.activated_abilities

        if not 0 <= ability_index < len(abilities):
            raise ValueError(
                "Activated ability not found at index "
                f"{ability_index}: {source.effective_card.name}"
            )

        return abilities[ability_index]

    @staticmethod
    def _parse_activated_ability_cost(
        mana_cost: str,
    ) -> ManaCost:
        normalized_cost = mana_cost.strip()

        if not normalized_cost:
            return ManaCost()

        generic = 0
        white = 0
        blue = 0
        black = 0
        red = 0
        green = 0
        colorless = 0

        symbols = normalized_cost.replace("}{", " ").strip("{}").split()

        for symbol in symbols:
            if symbol.isdecimal():
                generic += int(symbol)
                continue

            if symbol == "W":
                white += 1
                continue

            if symbol == "U":
                blue += 1
                continue

            if symbol == "B":
                black += 1
                continue

            if symbol == "R":
                red += 1
                continue

            if symbol == "G":
                green += 1
                continue

            if symbol == "C":
                colorless += 1
                continue

            raise ValueError(
                f"Unsupported activated ability mana symbol: {symbol}"
            )

        return ManaCost(
            generic=generic,
            white=white,
            blue=blue,
            black=black,
            red=red,
            green=green,
            colorless=colorless,
        )

    @staticmethod
    def _validate_activated_ability(
        source: Permanent,
        ability: ActivatedAbility,
    ) -> None:
        if ability.requires_tap and source.tapped:
            raise ValueError(
                "Tapped permanent cannot pay a tap activation cost: "
                f"{source.effective_card.name}"
            )

        if (
            ability.requires_tap
            and source.is_creature
            and not source.can_activate_tap_ability
        ):
            raise ValueError(
                "Summoning-sick creature cannot activate "
                f"a tap ability: {source.effective_card.name}"
            )

        if ability.ability_type == "untap_self":
            if not source.tapped:
                raise ValueError(
                    "Permanent is already untapped: "
                    f"{source.effective_card.name}"
                )
            return

        raise NotImplementedError(
            "Unsupported activated ability type: "
            f"{ability.ability_type}"
        )

    @staticmethod
    def _apply_activated_ability(
        source: Permanent,
        ability: ActivatedAbility,
    ) -> None:
        if ability.requires_tap:
            source.tapped = True

        if ability.ability_type == "untap_self":
            source.tapped = False
            return

        raise NotImplementedError(
            "Unsupported activated ability type: "
            f"{ability.ability_type}"
        )

    def _execute_return_commander(
        self,
        state: GameState,
        action: ReturnCommanderAction,
    ) -> None:
        requesting_player = self._get_player(
            state,
            action.player_id,
        )

        if not state.started:
            raise ValueError(
                "Cannot return a commander before the game starts."
            )

        if state.game_over:
            raise ValueError(
                "Cannot return a commander in a finished game."
            )

        permanent = self._find_permanent_by_id(
            state=state,
            permanent_id=action.permanent_id,
        )

        if permanent.owner_id != requesting_player.player_id:
            raise ValueError(
                "Only the commander owner may return it "
                "to the command zone."
            )

        if not self._is_commander_card(
            player=requesting_player,
            card_id=permanent.effective_card.id,
        ):
            raise ValueError(
                "Permanent is not the player's commander: "
                f"{permanent.effective_card.name}"
            )

        battlefield_owner = self._find_battlefield_containing(
            state=state,
            permanent_id=permanent.permanent_id,
        )

        battlefield_owner.battlefield.remove(permanent)

        requesting_player.command.add(
            permanent.effective_card
        )

        state.action_count += 1

    @staticmethod
    def _find_permanent_by_id(
        state: GameState,
        permanent_id: int,
    ) -> Permanent:
        for player in state.players:
            for permanent in player.battlefield:
                if permanent.permanent_id == permanent_id:
                    return permanent

        raise ValueError(
            f"Permanent not found on battlefield: {permanent_id}"
        )


    @staticmethod
    def _find_battlefield_containing(
        state: GameState,
        permanent_id: int,
    ) -> Player:
        for player in state.players:
            for permanent in player.battlefield:
                if permanent.permanent_id == permanent_id:
                    return player

        raise ValueError(
            f"Permanent not found on battlefield: {permanent_id}"
        )


    @staticmethod
    def _is_commander_card(
        player: Player,
        card_id: str,
    ) -> bool:
        return player.commander_card_id == card_id
    
    def _execute_activate_kinnan(
        self,
        state: GameState,
        action: ActivateKinnanAction,
    ) -> None:
        player = self._get_player(
            state,
            action.player_id,
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

        # すべての検証完了後に状態を変更する
        player.mana_pool.pay(
            KINNAN_ACTIVATION_COST
        )

        removed_cards = player.library.draw_many(
            reveal_count
        )

        remaining_cards = list(removed_cards)

        if selected_card is not None:
            remaining_cards.remove(selected_card)

            permanent = Permanent(
                permanent_id=state.next_permanent_id,
                card=selected_card,
                owner_id=player.player_id,
                controller_id=player.player_id,
                tapped=False,
                summoning_sick=self._is_creature_card(
                    selected_card
                ),
                entered_turn=state.turn_number,
            )

            player.battlefield.add(permanent)
            state.next_permanent_id += 1

        player.library.put_many_on_bottom(
            remaining_cards
        )
        if selected_card is not None:
            state.kinnan_chain.record_hit(
                selected_card.id
            )
        else:
            state.kinnan_chain.record_miss()

        state.mana_spent += (
            KINNAN_ACTIVATION_COST.total
        )
        state.action_count += 1