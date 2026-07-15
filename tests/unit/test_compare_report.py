from __future__ import annotations

import pytest

from krs.cards.card import Card
from krs.decks.deck import Deck
from krs.report.compare import (
    DeckComparisonEntry,
    DeckComparisonReport,
    DeckComparisonReporter,
)
from krs.simulation.experiment import (
    ExperimentResult,
    SimulationSummary,
)
from krs.simulation.monte_carlo import MonteCarloDeckResult
from krs.simulation.runner import GoldfishRunResult
from krs.simulation.simulation_config import SimulationConfig


def create_card(
    *,
    card_id: str,
    name: str,
    type_line: str,
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost="",
        mana_value=0,
        oracle_text="",
        type_line=type_line,
    )


def create_deck(
    *,
    name: str,
) -> Deck:
    commander = create_card(
        card_id=f"{name}-commander",
        name="Kinnan, Bonder Prodigy",
        type_line="Legendary Creature — Human Druid",
    )

    return Deck(
        name=name,
        commander=commander,
        cards=[
            create_card(
                card_id=f"{name}-forest-{index}",
                name="Forest",
                type_line="Basic Land — Forest",
            )
            for index in range(10)
        ],
    )


def create_game_result(
    *,
    turns_started: int,
    kinnan_activations: int = 0,
    win: bool = False,
    reached_turn_limit: bool = False,
) -> GoldfishRunResult:
    return GoldfishRunResult(
        turns_started=turns_started,
        kinnan_activations=kinnan_activations,
        reached_turn_limit=reached_turn_limit,
        game_over=win,
        winner="Player" if win else None,
    )


def create_deck_result(
    *,
    deck_name: str,
    game_results: tuple[GoldfishRunResult, ...],
) -> MonteCarloDeckResult:
    config = SimulationConfig(
        games=len(game_results),
    )

    summary = SimulationSummary.from_results(
        games_requested=config.games,
        results=game_results,
    )

    experiment = ExperimentResult(
        config=config,
        game_results=game_results,
        summary=summary,
    )

    return MonteCarloDeckResult(
        deck=create_deck(
            name=deck_name,
        ),
        experiment=experiment,
    )


def test_compare_orders_by_win_rate() -> None:
    high_win_rate = create_deck_result(
        deck_name="High Win Rate",
        game_results=(
            create_game_result(
                turns_started=2,
                win=True,
            ),
            create_game_result(
                turns_started=3,
                win=True,
            ),
        ),
    )
    low_win_rate = create_deck_result(
        deck_name="Low Win Rate",
        game_results=(
            create_game_result(
                turns_started=2,
                win=True,
            ),
            create_game_result(
                turns_started=6,
                reached_turn_limit=True,
            ),
        ),
    )

    report = DeckComparisonReporter().compare(
        (
            low_win_rate,
            high_win_rate,
        ),
    )

    assert report.entries[0].deck_name == "High Win Rate"
    assert report.entries[0].win_rate == 1.0
    assert report.entries[1].deck_name == "Low Win Rate"
    assert report.entries[1].win_rate == 0.5


def test_compare_uses_fastest_win_turn_as_tiebreaker() -> None:
    faster = create_deck_result(
        deck_name="Faster",
        game_results=(
            create_game_result(
                turns_started=2,
                win=True,
            ),
            create_game_result(
                turns_started=6,
                reached_turn_limit=True,
            ),
        ),
    )
    slower = create_deck_result(
        deck_name="Slower",
        game_results=(
            create_game_result(
                turns_started=4,
                win=True,
            ),
            create_game_result(
                turns_started=4,
                reached_turn_limit=True,
            ),
        ),
    )

    report = DeckComparisonReporter().compare(
        (
            slower,
            faster,
        ),
    )

    assert report.entries[0].deck_name == "Faster"
    assert report.entries[0].fastest_win_turn == 2
    assert report.entries[1].fastest_win_turn == 4


def test_compare_uses_average_turns_as_next_tiebreaker() -> None:
    lower_average = create_deck_result(
        deck_name="Lower Average",
        game_results=(
            create_game_result(
                turns_started=3,
                win=True,
            ),
            create_game_result(
                turns_started=3,
                reached_turn_limit=True,
            ),
        ),
    )
    higher_average = create_deck_result(
        deck_name="Higher Average",
        game_results=(
            create_game_result(
                turns_started=3,
                win=True,
            ),
            create_game_result(
                turns_started=5,
                reached_turn_limit=True,
            ),
        ),
    )

    report = DeckComparisonReporter().compare(
        (
            higher_average,
            lower_average,
        ),
    )

    assert report.entries[0].deck_name == "Lower Average"
    assert report.entries[0].average_turns_started == 3.0
    assert report.entries[1].average_turns_started == 4.0


def test_compare_uses_kinnan_activations_as_next_tiebreaker() -> None:
    more_activations = create_deck_result(
        deck_name="More Activations",
        game_results=(
            create_game_result(
                turns_started=3,
                kinnan_activations=4,
                win=True,
            ),
            create_game_result(
                turns_started=3,
                kinnan_activations=2,
                reached_turn_limit=True,
            ),
        ),
    )
    fewer_activations = create_deck_result(
        deck_name="Fewer Activations",
        game_results=(
            create_game_result(
                turns_started=3,
                kinnan_activations=1,
                win=True,
            ),
            create_game_result(
                turns_started=3,
                kinnan_activations=1,
                reached_turn_limit=True,
            ),
        ),
    )

    report = DeckComparisonReporter().compare(
        (
            fewer_activations,
            more_activations,
        ),
    )

    assert report.entries[0].deck_name == "More Activations"
    assert (
        report.entries[0].average_kinnan_activations
        == 3.0
    )


def test_compare_uses_deck_name_as_final_tiebreaker() -> None:
    alpha = create_deck_result(
        deck_name="Alpha",
        game_results=(
            create_game_result(
                turns_started=3,
                win=True,
            ),
        ),
    )
    beta = create_deck_result(
        deck_name="Beta",
        game_results=(
            create_game_result(
                turns_started=3,
                win=True,
            ),
        ),
    )

    report = DeckComparisonReporter().compare(
        (
            beta,
            alpha,
        ),
    )

    assert tuple(
        entry.deck_name
        for entry in report.entries
    ) == (
        "Alpha",
        "Beta",
    )


def test_compare_assigns_sequential_ranks() -> None:
    results = (
        create_deck_result(
            deck_name="Deck C",
            game_results=(
                create_game_result(
                    turns_started=5,
                ),
            ),
        ),
        create_deck_result(
            deck_name="Deck A",
            game_results=(
                create_game_result(
                    turns_started=2,
                    win=True,
                ),
            ),
        ),
        create_deck_result(
            deck_name="Deck B",
            game_results=(
                create_game_result(
                    turns_started=4,
                ),
            ),
        ),
    )

    report = DeckComparisonReporter().compare(results)

    assert tuple(
        entry.rank
        for entry in report.entries
    ) == (
        1,
        2,
        3,
    )


def test_report_winner_returns_first_entry() -> None:
    first = create_deck_result(
        deck_name="Winner",
        game_results=(
            create_game_result(
                turns_started=2,
                win=True,
            ),
        ),
    )
    second = create_deck_result(
        deck_name="Runner Up",
        game_results=(
            create_game_result(
                turns_started=6,
            ),
        ),
    )

    report = DeckComparisonReporter().compare(
        (
            second,
            first,
        ),
    )

    assert report.winner is report.entries[0]
    assert report.winner.deck_name == "Winner"


def test_compare_rejects_fewer_than_two_results() -> None:
    result = create_deck_result(
        deck_name="Only Deck",
        game_results=(
            create_game_result(
                turns_started=3,
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "At least two deck results are required "
            "for comparison."
        ),
    ):
        DeckComparisonReporter().compare(
            (
                result,
            ),
        )


def test_compare_rejects_duplicate_deck_names() -> None:
    first = create_deck_result(
        deck_name="Same Deck",
        game_results=(
            create_game_result(
                turns_started=2,
            ),
        ),
    )
    second = create_deck_result(
        deck_name="same deck",
        game_results=(
            create_game_result(
                turns_started=3,
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match="Deck names must be unique for comparison.",
    ):
        DeckComparisonReporter().compare(
            (
                first,
                second,
            ),
        )


def test_compare_rejects_different_game_counts_by_default() -> None:
    one_game = create_deck_result(
        deck_name="One Game",
        game_results=(
            create_game_result(
                turns_started=2,
            ),
        ),
    )
    two_games = create_deck_result(
        deck_name="Two Games",
        game_results=(
            create_game_result(
                turns_started=2,
            ),
            create_game_result(
                turns_started=3,
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "Compared decks must have equal "
            "completed game counts."
        ),
    ):
        DeckComparisonReporter().compare(
            (
                one_game,
                two_games,
            ),
        )


def test_compare_can_allow_different_game_counts() -> None:
    one_game = create_deck_result(
        deck_name="One Game",
        game_results=(
            create_game_result(
                turns_started=2,
                win=True,
            ),
        ),
    )
    two_games = create_deck_result(
        deck_name="Two Games",
        game_results=(
            create_game_result(
                turns_started=2,
                win=True,
            ),
            create_game_result(
                turns_started=3,
            ),
        ),
    )

    report = DeckComparisonReporter(
        require_equal_game_counts=False,
    ).compare(
        (
            two_games,
            one_game,
        ),
    )

    assert report.entries[0].deck_name == "One Game"


def test_comparison_entry_contains_summary_values() -> None:
    first = create_deck_result(
        deck_name="First",
        game_results=(
            create_game_result(
                turns_started=2,
                kinnan_activations=3,
                win=True,
            ),
            create_game_result(
                turns_started=6,
                kinnan_activations=1,
                reached_turn_limit=True,
            ),
        ),
    )
    second = create_deck_result(
        deck_name="Second",
        game_results=(
            create_game_result(
                turns_started=5,
            ),
            create_game_result(
                turns_started=5,
            ),
        ),
    )

    report = DeckComparisonReporter().compare(
        (
            first,
            second,
        ),
    )

    entry = report.entries[0]

    assert entry == DeckComparisonEntry(
        rank=1,
        deck_name="First",
        games_completed=2,
        wins=1,
        non_wins=1,
        win_rate=0.5,
        fastest_win_turn=2,
        average_turns_started=4.0,
        average_kinnan_activations=2.0,
        turn_limit_games=1,
    )


def test_comparison_report_is_immutable() -> None:
    first = create_deck_result(
        deck_name="First",
        game_results=(
            create_game_result(
                turns_started=2,
                win=True,
            ),
        ),
    )
    second = create_deck_result(
        deck_name="Second",
        game_results=(
            create_game_result(
                turns_started=3,
            ),
        ),
    )

    report = DeckComparisonReporter().compare(
        (
            first,
            second,
        ),
    )

    with pytest.raises(AttributeError):
        report.entries = ()  # type: ignore[misc]