from __future__ import annotations

from dataclasses import dataclass

from krs.cards.card import Card
from krs.decks.deck import Deck
from krs.decks.implementation_audit import (
    DeckImplementationAudit,
)
from krs.mana.mana import Mana


@dataclass(frozen=True, slots=True)
class SimulationPreflightIssue:
    """One issue detected before starting a simulation."""

    code: str
    message: str
    blocking: bool = True

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError(
                "Preflight issue code must not be empty."
            )

        if not self.message.strip():
            raise ValueError(
                "Preflight issue message must not be empty."
            )


@dataclass(frozen=True, slots=True)
class SimulationPreflightResult:
    """Immutable preflight result for one loaded deck."""

    deck_name: str
    total_cards: int
    main_deck_cards: int
    unique_cards: int
    configured_unique_cards: int
    oracle_only_unique_cards: int
    land_cards: int
    mana_source_cards: int
    blue_source_cards: int
    green_source_cards: int
    issues: tuple[SimulationPreflightIssue, ...]

    def __post_init__(self) -> None:
        if not self.deck_name.strip():
            raise ValueError(
                "deck_name must not be empty."
            )

        counts = (
            self.total_cards,
            self.main_deck_cards,
            self.unique_cards,
            self.configured_unique_cards,
            self.oracle_only_unique_cards,
            self.land_cards,
            self.mana_source_cards,
            self.blue_source_cards,
            self.green_source_cards,
        )

        if any(count < 0 for count in counts):
            raise ValueError(
                "Preflight counts must not be negative."
            )

    @property
    def blocking_issues(
        self,
    ) -> tuple[SimulationPreflightIssue, ...]:
        """Return issues that prevent simulation execution."""
        return tuple(
            issue
            for issue in self.issues
            if issue.blocking
        )

    @property
    def warnings(
        self,
    ) -> tuple[SimulationPreflightIssue, ...]:
        """Return non-blocking implementation warnings."""
        return tuple(
            issue
            for issue in self.issues
            if not issue.blocking
        )

    @property
    def ready(self) -> bool:
        """Return whether the simulation may start."""
        return not self.blocking_issues


@dataclass(frozen=True, slots=True)
class SimulationPreflightValidator:
    """Validates a loaded deck before Monte Carlo execution."""

    expected_total_cards: int = 100
    expected_main_deck_cards: int = 99

    def __post_init__(self) -> None:
        if self.expected_total_cards < 1:
            raise ValueError(
                "expected_total_cards must be at least 1."
            )

        if self.expected_main_deck_cards < 0:
            raise ValueError(
                "expected_main_deck_cards must not be negative."
            )

        if (
            self.expected_main_deck_cards
            >= self.expected_total_cards
        ):
            raise ValueError(
                "expected_main_deck_cards must be smaller than "
                "expected_total_cards."
            )

    def validate(
        self,
        *,
        deck: Deck,
        audit: DeckImplementationAudit,
    ) -> SimulationPreflightResult:
        """Validate one deck and its implementation audit."""
        issues: list[SimulationPreflightIssue] = []

        all_cards = tuple(deck.all_cards)
        main_deck_cards = tuple(deck.cards)

        if len(all_cards) != self.expected_total_cards:
            issues.append(
                SimulationPreflightIssue(
                    code="invalid_deck_size",
                    message=(
                        "Deck must contain "
                        f"{self.expected_total_cards} cards including "
                        f"the commander, but contains {len(all_cards)}."
                    ),
                )
            )

        if len(main_deck_cards) != self.expected_main_deck_cards:
            issues.append(
                SimulationPreflightIssue(
                    code="invalid_main_deck_size",
                    message=(
                        "Main deck must contain "
                        f"{self.expected_main_deck_cards} cards, "
                        f"but contains {len(main_deck_cards)}."
                    ),
                )
            )

        if deck.commander.name != "Kinnan, Bonder Prodigy":
            issues.append(
                SimulationPreflightIssue(
                    code="invalid_commander",
                    message=(
                        "Commander must be Kinnan, Bonder Prodigy, "
                        f"but is {deck.commander.name}."
                    ),
                )
            )

        missing_oracle_cards = tuple(
            card.name
            for card in all_cards
            if not card.oracle_text.strip()
            and not self._is_basic_land(card)
        )

        if missing_oracle_cards:
            issues.append(
                SimulationPreflightIssue(
                    code="missing_oracle_text",
                    message=(
                        "Cards without Oracle text: "
                        + ", ".join(
                            sorted(
                                set(missing_oracle_cards),
                                key=str.casefold,
                            )
                        )
                    ),
                    blocking=False,
                )
            )

        if audit.oracle_only_unique_cards > 0:
            issues.append(
                SimulationPreflightIssue(
                    code="partial_card_implementation",
                    message=(
                        f"{audit.oracle_only_unique_cards} unique cards "
                        "have Oracle data only and no executable "
                        "config/cards definition."
                    ),
                    blocking=False,
                )
            )

        mana_source_cards = tuple(
            card
            for card in all_cards
            if self._is_mana_source(card)
        )

        blue_source_cards = tuple(
            card
            for card in mana_source_cards
            if Mana.BLUE in self._produced_mana(card)
        )
        green_source_cards = tuple(
            card
            for card in mana_source_cards
            if Mana.GREEN in self._produced_mana(card)
        )

        if not blue_source_cards:
            issues.append(
                SimulationPreflightIssue(
                    code="missing_blue_source",
                    message=(
                        "No implemented blue mana source was found."
                    ),
                )
            )

        if not green_source_cards:
            issues.append(
                SimulationPreflightIssue(
                    code="missing_green_source",
                    message=(
                        "No implemented green mana source was found."
                    ),
                )
            )

        if not deck.commander.static_abilities:
            issues.append(
                SimulationPreflightIssue(
                    code="kinnan_static_ability_not_configured",
                    message=(
                        "Kinnan has no configured static ability. "
                        "Additional nonland mana may not be simulated."
                    ),
                    blocking=False,
                )
            )

        land_cards = tuple(
            card
            for card in all_cards
            if self._is_land(card)
        )

        return SimulationPreflightResult(
            deck_name=deck.name,
            total_cards=len(all_cards),
            main_deck_cards=len(main_deck_cards),
            unique_cards=audit.unique_cards,
            configured_unique_cards=(
                audit.configured_unique_cards
            ),
            oracle_only_unique_cards=(
                audit.oracle_only_unique_cards
            ),
            land_cards=len(land_cards),
            mana_source_cards=len(mana_source_cards),
            blue_source_cards=len(blue_source_cards),
            green_source_cards=len(green_source_cards),
            issues=tuple(issues),
        )

    @classmethod
    def _is_mana_source(
        cls,
        card: Card,
    ) -> bool:
        if card.mana_abilities:
            return True

        return bool(
            cls._basic_land_mana(card)
        )

    @classmethod
    def _produced_mana(
        cls,
        card: Card,
    ) -> set[Mana]:
        result: set[Mana] = set()

        for ability in card.mana_abilities:
            result.update(
                ability.produced_mana
            )

        result.update(
            cls._basic_land_mana(card)
        )

        return result

    @staticmethod
    def _basic_land_mana(
        card: Card,
    ) -> set[Mana]:
        if " — " not in card.type_line:
            return set()

        subtypes = set(
            card.type_line.split(
                " — ",
                maxsplit=1,
            )[1].split()
        )

        subtype_to_mana = {
            "Plains": Mana.WHITE,
            "Island": Mana.BLUE,
            "Swamp": Mana.BLACK,
            "Mountain": Mana.RED,
            "Forest": Mana.GREEN,
        }

        return {
            mana
            for subtype, mana in subtype_to_mana.items()
            if subtype in subtypes
        }

    @staticmethod
    def _is_land(
        card: Card,
    ) -> bool:
        card_types = set(
            card.type_line.split(
                " — ",
                maxsplit=1,
            )[0].split()
        )

        return "Land" in card_types

    @classmethod
    def _is_basic_land(
        cls,
        card: Card,
    ) -> bool:
        return (
            cls._is_land(card)
            and "Basic" in card.type_line.split(
                " — ",
                maxsplit=1,
            )[0].split()
        )