from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass

from krs.actions.cast_spell import CastSpellAction
from krs.actions.tap_permanent import TapPermanentAction
from krs.cards.card import Card
from krs.game.game_state import GameState
from krs.game.permanent import Permanent
from krs.game.player import Player
from krs.mana.mana import Mana
from krs.mana.mana_cost import ManaCost
from types import MappingProxyType
from collections.abc import Mapping
from krs.mana.mana_production import (
    mana_production_multiplier,
)


_MANA_SYMBOL_PATTERN = re.compile(r"\{([^{}]+)\}")


@dataclass(frozen=True, slots=True)
class ManaPermanentCastPlan:
    """
    Immutable plan for casting one mana-producing permanent.

    mana_actions must be executed before cast_action.
    """

    mana_actions: tuple[TapPermanentAction, ...]
    cast_action: CastSpellAction


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
class _CastCandidate:
    """One castable mana-producing permanent candidate."""

    card: Card
    cost: ManaCost
    mana_actions: tuple[TapPermanentAction, ...]

    @property
    def produced_amount(self) -> int:
        """
        Return the maximum total mana this permanent can produce.

        Values within one ManaAbility are alternative mana selections,
        not simultaneous outputs. For example, Birds of Paradise can
        produce one mana of any one color, so its output is 1 rather
        than the sum of all five color entries.

        Separate ManaAbility instances are treated as independent
        abilities and their maximum selectable outputs are summed for
        candidate-ranking purposes.
        """
        return sum(
            max(
                ability.produced_mana.values(),
                default=0,
            )
            for ability in self.card.mana_abilities
        )

    @property
    def mana_option_count(self) -> int:
        return len(
            {
                mana
                for ability in self.card.mana_abilities
                for mana in ability.produced_mana
            }
        )

    @property
    def selection_key(
        self,
    ) -> tuple[int, int, int, str, str]:
        return (
            -self.produced_amount,
            self.cost.total,
            -self.mana_option_count,
            self.card.name.casefold(),
            self.card.id,
        )


@dataclass(frozen=True, slots=True)
class ManaPermanentCastPlanFactory:
    """
    Creates a deterministic plan for casting a mana permanent.

    The factory creates Actions only and does not mutate GameState.
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
    ) -> ManaPermanentCastPlan | None:
        """
        Create a plan for the best castable mana permanent.

        None is returned when the hand contains no supported mana permanent
        that can currently be paid for.
        """
        player = self._find_player(
            state=state,
            player_id=player_id,
        )

        candidates: list[_CastCandidate] = []

        for card in player.hand:
            if not self._is_supported_mana_permanent(card):
                continue

            cost = self._parse_mana_cost(
                card.mana_cost
            )

            if cost is None:
                continue

            selected_options = self._find_minimum_plan(
                player=player,
                cost=cost,
            )

            if selected_options is None:
                continue

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

            candidates.append(
                _CastCandidate(
                    card=card,
                    cost=cost,
                    mana_actions=mana_actions,
                )
            )

        if not candidates:
            return None

        selected = min(
            candidates,
            key=lambda candidate: candidate.selection_key,
        )

        return ManaPermanentCastPlan(
            mana_actions=selected.mana_actions,
            cast_action=CastSpellAction(
                player_id=player.player_id,
                turn_number=state.turn_number,
                card=selected.card,
                cost=selected.cost,
                chosen_values=self._chosen_values(
                    selected.card,
                ),
            ),
        )

    def _find_minimum_plan(
        self,
        *,
        player: Player,
        cost: ManaCost,
    ) -> tuple[_ManaSourceOption, ...] | None:
        current_mana = self._mana_pool_counts(
            player
        )

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

        kinnan_is_active = any(
            self._is_kinnan(permanent)
            for permanent in permanents
        )

        for permanent in permanents:
            options = self._permanent_options(
                permanent=permanent,
                kinnan_is_active=kinnan_is_active,
                battlefield=tuple(permanents),
            )

            if options:
                groups.append(options)

        return tuple(groups)

    def _permanent_options(
        self,
        *,
        permanent: Permanent,
        kinnan_is_active: bool,
        battlefield: tuple[Permanent, ...],
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

        multiplier = mana_production_multiplier(
            source=permanent,
            battlefield=battlefield,
        )

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
                    amount = base_amount * multiplier

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
                    amount=multiplier,
                    ability_index=0,
                )
            )

        return tuple(options)

    @staticmethod
    def _is_supported_mana_permanent(
        card: Card,
    ) -> bool:
        if not card.mana_abilities:
            return False

        card_types = set(
            card.type_line.split(
                " — ",
                maxsplit=1,
            )[0].split()
        )

        if "Land" in card_types:
            return False

        return bool(
            card_types.intersection(
                {
                    "Artifact",
                    "Creature",
                    "Enchantment",
                }
            )
        )

    @staticmethod
    def _is_kinnan(
        permanent: Permanent,
    ) -> bool:
        return (
            permanent.effective_card.name
            == "Kinnan, Bonder Prodigy"
        )

    @staticmethod
    def _basic_land_mana(
        card: Card,
    ) -> tuple[Mana, ...]:
        if " — " not in card.type_line:
            return ()

        subtypes = set(
            card.type_line.split(
                " — ",
                maxsplit=1,
            )[1].split()
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

    @staticmethod
    def _chosen_values(
        card: Card,
    ) -> Mapping[str, str]:
        """
        Return deterministic choices required when casting a card.

        Roaming Throne chooses Druid so it can interact with Kinnan,
        Bonder Prodigy's Druid creature type.

        Cards without required choices receive an empty mapping.
        """
        if card.name == "Roaming Throne":
            return {
                "creature_type": "Druid",
            }

        return {}

    @staticmethod
    def _parse_mana_cost(
        mana_cost: str,
    ) -> ManaCost | None:
        symbols = _MANA_SYMBOL_PATTERN.findall(
            mana_cost
        )

        if not symbols and mana_cost:
            return None

        values = {
            "generic": 0,
            "white": 0,
            "blue": 0,
            "black": 0,
            "red": 0,
            "green": 0,
            "colorless": 0,
        }

        field_by_symbol = {
            "W": "white",
            "U": "blue",
            "B": "black",
            "R": "red",
            "G": "green",
            "C": "colorless",
        }

        for raw_symbol in symbols:
            symbol = raw_symbol.strip().upper()

            if symbol.isdigit():
                values["generic"] += int(symbol)
                continue

            field_name = field_by_symbol.get(symbol)

            if field_name is None:
                return None

            values[field_name] += 1

        return ManaCost(**values)

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
    
    @staticmethod
    def _chosen_values(
        card: Card,
    ) -> Mapping[str, str]:
        if card.name == "Roaming Throne":
            return MappingProxyType(
                {
                    "creature_type": "Druid",
                }
            )

        return MappingProxyType({})