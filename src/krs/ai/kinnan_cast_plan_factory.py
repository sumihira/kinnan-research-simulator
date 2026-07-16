from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from krs.actions.cast_commander import CastCommanderAction
from krs.actions.tap_permanent import TapPermanentAction
from krs.cards.card import Card
from krs.commanders.kinnan import KINNAN_CARD_NAME
from krs.game.game_state import GameState
from krs.game.permanent import Permanent
from krs.game.player import Player
from krs.mana.mana import Mana
from krs.mana.mana_cost import ManaCost


@dataclass(frozen=True, slots=True)
class KinnanCastPlan:
    """
    Immutable action plan for casting Kinnan.

    Mana sources must be tapped in tuple order before executing
    cast_action.
    """

    mana_actions: tuple[TapPermanentAction, ...]
    cast_action: CastCommanderAction


@dataclass(frozen=True, slots=True)
class _ManaSourceOption:
    """One selectable mana result from one permanent."""

    permanent: Permanent
    mana: Mana
    amount: int
    ability_index: int

    def __post_init__(self) -> None:
        if self.amount < 1:
            raise ValueError(
                "Mana source amount must be at least 1."
            )

        if self.ability_index < 0:
            raise ValueError(
                "Mana ability index must not be negative."
            )

    @property
    def sort_key(
        self,
    ) -> tuple[int, str, int, str]:
        return (
            self.permanent.permanent_id,
            self.permanent.effective_card.name.casefold(),
            self.ability_index,
            self.mana.value,
        )


@dataclass(frozen=True, slots=True)
class KinnanCastPlanFactory:
    """
    Creates a deterministic minimum-tap plan for casting Kinnan.

    The factory only creates Actions. It does not tap permanents,
    spend mana, move cards, or otherwise mutate GameState.
    """

    KINNAN_BASE_COST = ManaCost(
        green=1,
        blue=1,
    )

    _GENERIC_PAYMENT_ORDER = (
        Mana.COLORLESS,
        Mana.WHITE,
        Mana.BLUE,
        Mana.BLACK,
        Mana.RED,
        Mana.GREEN,
    )

    def create(
        self,
        *,
        state: GameState,
        player_id: int,
    ) -> KinnanCastPlan | None:
        """
        Create a plan for casting Kinnan from the command zone.

        None is returned when Kinnan is not in the command zone or
        available mana sources cannot pay the total commander cost.
        """
        player = self._find_player(
            state=state,
            player_id=player_id,
        )
        kinnan = self._find_kinnan_in_command_zone(
            player
        )

        if kinnan is None:
            return None

        total_cost = self._commander_cost(
            commander_cast_count=player.commander_cast_count,
        )
        current_mana = self._mana_pool_counts(player)

        selected_options = self._find_minimum_plan(
            player=player,
            current_mana=current_mana,
            cost=total_cost,
        )

        if selected_options is None:
            return None

        mana_actions = tuple(
            TapPermanentAction(
                player_id=player.player_id,
                turn_number=state.turn_number,
                permanent=option.permanent,
                mana=option.mana,
                ability_index=option.ability_index,
            )
            for option in selected_options
        )

        return KinnanCastPlan(
            mana_actions=mana_actions,
            cast_action=CastCommanderAction(
                player_id=player.player_id,
                turn_number=state.turn_number,
                card=kinnan,
                base_cost=self.KINNAN_BASE_COST,
            ),
        )

    def _find_minimum_plan(
        self,
        *,
        player: Player,
        current_mana: Counter[Mana],
        cost: ManaCost,
    ) -> tuple[_ManaSourceOption, ...] | None:
        if self._can_pay(
            available=current_mana,
            cost=cost,
        ):
            return ()

        source_groups = self._available_source_groups(
            player
        )

        best_plan: tuple[_ManaSourceOption, ...] | None = None

        def search(
            source_index: int,
            available: Counter[Mana],
            selected: tuple[_ManaSourceOption, ...],
        ) -> None:
            nonlocal best_plan

            if self._can_pay(
                available=available,
                cost=cost,
            ):
                if self._is_better_plan(
                    candidate=selected,
                    current_best=best_plan,
                ):
                    best_plan = selected
                return

            if source_index >= len(source_groups):
                return

            if (
                best_plan is not None
                and len(selected) >= len(best_plan)
            ):
                return

            search(
                source_index + 1,
                available,
                selected,
            )

            for option in source_groups[source_index]:
                next_available = available.copy()
                next_available[option.mana] += option.amount

                search(
                    source_index + 1,
                    next_available,
                    selected + (option,),
                )

        search(
            source_index=0,
            available=current_mana.copy(),
            selected=(),
        )

        return best_plan

    @classmethod
    def _is_better_plan(
        cls,
        *,
        candidate: tuple[_ManaSourceOption, ...],
        current_best: tuple[_ManaSourceOption, ...] | None,
    ) -> bool:
        if current_best is None:
            return True

        if len(candidate) != len(current_best):
            return len(candidate) < len(current_best)

        candidate_key = tuple(
            option.sort_key
            for option in candidate
        )
        current_key = tuple(
            option.sort_key
            for option in current_best
        )

        return candidate_key < current_key

    def _available_source_groups(
        self,
        player: Player,
    ) -> tuple[tuple[_ManaSourceOption, ...], ...]:
        groups: list[tuple[_ManaSourceOption, ...]] = []

        permanents = sorted(
            player.battlefield,
            key=lambda permanent: (
                permanent.permanent_id,
                permanent.effective_card.name.casefold(),
            ),
        )

        for permanent in permanents:
            options = self._permanent_options(
                permanent
            )

            if options:
                groups.append(options)

        return tuple(groups)

    def _permanent_options(
        self,
        permanent: Permanent,
    ) -> tuple[_ManaSourceOption, ...]:
        if permanent.tapped:
            return ()

        if (
            permanent.is_creature
            and not permanent.can_activate_tap_ability
        ):
            return ()

        card = permanent.effective_card
        options: list[_ManaSourceOption] = []

        if card.mana_abilities:
            for ability_index, ability in enumerate(
                card.mana_abilities
            ):
                if not ability.requires_tap:
                    continue

                for mana, amount in sorted(
                    ability.produced_mana.items(),
                    key=lambda item: item[0].value,
                ):
                    options.append(
                        _ManaSourceOption(
                            permanent=permanent,
                            mana=mana,
                            amount=amount,
                            ability_index=ability_index,
                        )
                    )

            return tuple(options)

        if not permanent.is_land:
            return ()

        for mana in self._basic_land_mana(card):
            options.append(
                _ManaSourceOption(
                    permanent=permanent,
                    mana=mana,
                    amount=1,
                    ability_index=0,
                )
            )

        return tuple(options)

    @staticmethod
    def _basic_land_mana(
        card: Card,
    ) -> tuple[Mana, ...]:
        if " — " not in card.type_line:
            return ()

        subtype_part = card.type_line.split(
            " — ",
            maxsplit=1,
        )[1]
        subtypes = set(subtype_part.split())

        subtype_to_mana = (
            ("Plains", Mana.WHITE),
            ("Island", Mana.BLUE),
            ("Swamp", Mana.BLACK),
            ("Mountain", Mana.RED),
            ("Forest", Mana.GREEN),
        )

        return tuple(
            mana
            for subtype, mana in subtype_to_mana
            if subtype in subtypes
        )

    @classmethod
    def _can_pay(
        cls,
        *,
        available: Counter[Mana],
        cost: ManaCost,
    ) -> bool:
        remaining = available.copy()

        fixed_requirements = (
            (Mana.WHITE, cost.white),
            (Mana.BLUE, cost.blue),
            (Mana.BLACK, cost.black),
            (Mana.RED, cost.red),
            (Mana.GREEN, cost.green),
            (Mana.COLORLESS, cost.colorless),
        )

        for mana, required_amount in fixed_requirements:
            if remaining[mana] < required_amount:
                return False

            remaining[mana] -= required_amount

        generic_remaining = cost.generic

        for mana in cls._GENERIC_PAYMENT_ORDER:
            if generic_remaining == 0:
                break

            amount = min(
                remaining[mana],
                generic_remaining,
            )
            remaining[mana] -= amount
            generic_remaining -= amount

        return generic_remaining == 0

    @classmethod
    def _commander_cost(
        cls,
        *,
        commander_cast_count: int,
    ) -> ManaCost:
        if commander_cast_count < 0:
            raise ValueError(
                "Commander cast count must not be negative."
            )

        return ManaCost(
            generic=commander_cast_count * 2,
            blue=cls.KINNAN_BASE_COST.blue,
            green=cls.KINNAN_BASE_COST.green,
        )

    @staticmethod
    def _mana_pool_counts(
        player: Player,
    ) -> Counter[Mana]:
        return Counter(
            {
                mana: player.mana_pool.count(mana)
                for mana in Mana
            }
        )

    @staticmethod
    def _find_kinnan_in_command_zone(
        player: Player,
    ) -> Card | None:
        for card in player.command:
            if card.name == KINNAN_CARD_NAME:
                return card

        return None

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