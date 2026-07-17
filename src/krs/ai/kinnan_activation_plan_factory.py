from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from krs.actions.tap_permanent import TapPermanentAction
from krs.cards.card import Card
from krs.commanders.kinnan import is_kinnan
from krs.commanders.kinnan_activation_cost import (
    kinnan_activation_cost,
)
from krs.game.game_state import GameState
from krs.game.permanent import Permanent
from krs.game.player import Player
from krs.mana.mana import Mana
from krs.mana.mana_cost import ManaCost


@dataclass(frozen=True, slots=True)
class KinnanActivationPlan:
    """
    Immutable mana-payment plan for one Kinnan activation.

    mana_actions must be executed in tuple order before creating and
    executing ActivateKinnanAction.
    """

    source_permanent_id: int
    mana_actions: tuple[TapPermanentAction, ...]

    def __post_init__(self) -> None:
        if self.source_permanent_id < 0:
            raise ValueError(
                "source_permanent_id must not be negative."
            )


@dataclass(frozen=True, slots=True)
class _ManaSourceOption:
    """One possible mana selection from one permanent."""

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
class KinnanActivationPlanFactory:
    """
    Creates a deterministic minimum-tap plan for activating Kinnan.

    The factory considers:
    - mana already floating in the player's mana pool;
    - basic land types;
    - configured ManaAbility definitions;
    - tapped permanents;
    - summoning sickness;
    - Kinnan's additional nonland mana.

    It creates Actions only and does not mutate GameState.
    """

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
    ) -> KinnanActivationPlan | None:
        """
        Create one complete Kinnan activation payment plan.

        None is returned when the player does not control Kinnan or cannot
        produce enough mana to pay the activation cost.
        """
        player = self._find_player(
            state=state,
            player_id=player_id,
        )
        kinnan = self._find_controlled_kinnan(
            player
        )

        if kinnan is None:
            return None

        current_mana = self._mana_pool_counts(
            player
        )

        selected_options = self._find_minimum_plan(
            player=player,
            current_mana=current_mana,
            cost=kinnan_activation_cost(player),
            kinnan=kinnan,
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

        return KinnanActivationPlan(
            source_permanent_id=kinnan.permanent_id,
            mana_actions=mana_actions,
        )

    def _find_minimum_plan(
        self,
        *,
        player: Player,
        current_mana: Counter[Mana],
        cost: ManaCost,
        kinnan: Permanent,
    ) -> tuple[_ManaSourceOption, ...] | None:
        if self._can_pay(
            available=current_mana,
            cost=cost,
        ):
            return ()

        source_groups = self._available_source_groups(
            player=player,
            kinnan=kinnan,
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

    def _available_source_groups(
        self,
        *,
        player: Player,
        kinnan: Permanent,
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
            if permanent.permanent_id == kinnan.permanent_id:
                continue

            options = self._permanent_options(
                permanent=permanent,
                kinnan_is_active=True,
            )

            if options:
                groups.append(options)

        return tuple(groups)

    def _permanent_options(
        self,
        *,
        permanent: Permanent,
        kinnan_is_active: bool,
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

                for mana, base_amount in sorted(
                    ability.produced_mana.items(),
                    key=lambda item: item[0].value,
                ):
                    amount = base_amount

                    if (
                        kinnan_is_active
                        and not permanent.is_land
                    ):
                        amount += 1

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
        subtypes = set(
            subtype_part.split()
        )

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

            payment_amount = min(
                remaining[mana],
                generic_remaining,
            )
            remaining[mana] -= payment_amount
            generic_remaining -= payment_amount

        return generic_remaining == 0

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

        candidate_total = sum(
            option.amount
            for option in candidate
        )
        current_total = sum(
            option.amount
            for option in current_best
        )

        if candidate_total != current_total:
            return candidate_total < current_total

        candidate_key = tuple(
            option.sort_key
            for option in candidate
        )
        current_key = tuple(
            option.sort_key
            for option in current_best
        )

        return candidate_key < current_key

    @staticmethod
    def _mana_pool_counts(
        player: Player,
    ) -> Counter[Mana]:
        """
        Return concrete mana counts from the player's mana pool.

        Some existing unit tests replace ManaPool with a Mock that only
        defines can_pay(). Non-integer count results are treated as zero so
        the planner remains compatible with those isolated GameEngine tests.
        """
        counts: Counter[Mana] = Counter()

        for mana in Mana:
            amount = player.mana_pool.count(mana)

            if isinstance(amount, int) and not isinstance(
                amount,
                bool,
            ):
                counts[mana] = amount
            else:
                counts[mana] = 0

        return counts

    @staticmethod
    def _find_controlled_kinnan(
        player: Player,
    ) -> Permanent | None:
        kinnans = sorted(
            (
                permanent
                for permanent in player.battlefield
                if (
                    permanent.controller_id
                    == player.player_id
                    and is_kinnan(permanent)
                )
            ),
            key=lambda permanent: permanent.permanent_id,
        )

        if not kinnans:
            return None

        return kinnans[0]

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