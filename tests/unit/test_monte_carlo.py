from __future__ import annotations

from unittest.mock import Mock, call

import pytest

from krs.cards.card import Card
from krs.decks.deck import Deck
from krs.simulation.experiment import (
    ExperimentResult,
    SimulationSummary,
)
from krs.simulation.experiment_manager import ExperimentManager
from krs.simulation.monte_carlo import (
    MonteCarloDeckResult,
    MonteCarloSimulator,
)
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
    name: str = "Kinnan Test",
    card_prefix: str = "forest",
) -> Deck:
    commander = create_card(
        card_id=f"{name}-commander",
        name="Kinnan, Bonder Prodigy",
        type_line="Legendary Creature — Human Druid",
    )

    cards = [
        create_card(
            card_id=f"{card_prefix}-{index}",
            name="Forest",
            type_line="Basic Land — Forest",
        )
        for index in range(10)
    ]

    return Deck(
        name=name,
        commander=commander,
        cards=cards,
    )


def create_experiment_result(
    *,
    games: int = 1,
    turns_started: int = 3,
    kinnan_activations: int = 2,
) -> ExperimentResult:
    config = SimulationConfig(
        games=games,
    )

    game_results = tuple(
        GoldfishRunResult(
            turns_started=turns_started,
            kinnan_activations=kinnan_activations,
            reached_turn_limit=True,
            game_over=False,
            winner=None,
        )
        for _ in range(games)
    )

    summary = SimulationSummary.from_results(
        games_requested=games,
        results=game_results,
    )

    return ExperimentResult(
        config=config,
        game_results=game_results,
        summary=summary,
    )


def test_run_delegates_to_experiment_manager() -> None:
    deck = create_deck()
    expected_result = create_experiment_result()

    experiment_manager = Mock(
        spec=ExperimentManager,
    )
    experiment_manager.run.return_value = expected_result

    simulator = MonteCarloSimulator(
        experiment_manager=experiment_manager,
    )

    result = simulator.run(deck)

    experiment_manager.run.assert_called_once_with(
        deck,
        player_id=0,
        player_name="Player",
    )
    assert result is expected_result


def test_run_passes_custom_player_values() -> None:
    deck = create_deck()

    experiment_manager = Mock(
        spec=ExperimentManager,
    )
    experiment_manager.run.return_value = (
        create_experiment_result()
    )

    simulator = MonteCarloSimulator(
        experiment_manager=experiment_manager,
    )

    simulator.run(
        deck,
        player_id=7,
        player_name="Junpei",
    )

    experiment_manager.run.assert_called_once_with(
        deck,
        player_id=7,
        player_name="Junpei",
    )


def test_run_does_not_modify_experiment_result() -> None:
    deck = create_deck()
    expected_result = create_experiment_result(
        games=2,
    )

    experiment_manager = Mock(
        spec=ExperimentManager,
    )
    experiment_manager.run.return_value = expected_result

    simulator = MonteCarloSimulator(
        experiment_manager=experiment_manager,
    )

    result = simulator.run(deck)

    assert result is expected_result
    assert result.summary.games_completed == 2


def test_run_many_executes_every_deck() -> None:
    first_deck = create_deck(
        name="First Deck",
        card_prefix="first",
    )
    second_deck = create_deck(
        name="Second Deck",
        card_prefix="second",
    )

    first_result = create_experiment_result(
        turns_started=2,
    )
    second_result = create_experiment_result(
        turns_started=4,
    )

    experiment_manager = Mock(
        spec=ExperimentManager,
    )
    experiment_manager.run.side_effect = [
        first_result,
        second_result,
    ]

    simulator = MonteCarloSimulator(
        experiment_manager=experiment_manager,
    )

    results = simulator.run_many(
        (
            first_deck,
            second_deck,
        ),
    )

    assert experiment_manager.run.call_args_list == [
        call(
            first_deck,
            player_id=0,
            player_name="Player",
        ),
        call(
            second_deck,
            player_id=0,
            player_name="Player",
        ),
    ]
    assert len(results) == 2


def test_run_many_preserves_deck_order() -> None:
    first_deck = create_deck(
        name="First Deck",
        card_prefix="first",
    )
    second_deck = create_deck(
        name="Second Deck",
        card_prefix="second",
    )
    third_deck = create_deck(
        name="Third Deck",
        card_prefix="third",
    )

    first_result = create_experiment_result(
        turns_started=2,
    )
    second_result = create_experiment_result(
        turns_started=3,
    )
    third_result = create_experiment_result(
        turns_started=4,
    )

    experiment_manager = Mock(
        spec=ExperimentManager,
    )
    experiment_manager.run.side_effect = [
        first_result,
        second_result,
        third_result,
    ]

    simulator = MonteCarloSimulator(
        experiment_manager=experiment_manager,
    )

    results = simulator.run_many(
        (
            first_deck,
            second_deck,
            third_deck,
        ),
    )

    assert results == (
        MonteCarloDeckResult(
            deck=first_deck,
            experiment=first_result,
        ),
        MonteCarloDeckResult(
            deck=second_deck,
            experiment=second_result,
        ),
        MonteCarloDeckResult(
            deck=third_deck,
            experiment=third_result,
        ),
    )


def test_run_many_passes_custom_player_values_to_every_deck() -> None:
    first_deck = create_deck(
        name="First Deck",
        card_prefix="first",
    )
    second_deck = create_deck(
        name="Second Deck",
        card_prefix="second",
    )

    experiment_manager = Mock(
        spec=ExperimentManager,
    )
    experiment_manager.run.side_effect = [
        create_experiment_result(),
        create_experiment_result(),
    ]

    simulator = MonteCarloSimulator(
        experiment_manager=experiment_manager,
    )

    simulator.run_many(
        (
            first_deck,
            second_deck,
        ),
        player_id=9,
        player_name="Research Player",
    )

    assert experiment_manager.run.call_args_list == [
        call(
            first_deck,
            player_id=9,
            player_name="Research Player",
        ),
        call(
            second_deck,
            player_id=9,
            player_name="Research Player",
        ),
    ]


def test_run_many_rejects_empty_deck_collection() -> None:
    experiment_manager = Mock(
        spec=ExperimentManager,
    )

    simulator = MonteCarloSimulator(
        experiment_manager=experiment_manager,
    )

    with pytest.raises(
        ValueError,
        match=(
            "At least one deck is required for "
            "Monte Carlo simulation."
        ),
    ):
        simulator.run_many(())

    experiment_manager.run.assert_not_called()


def test_monte_carlo_deck_result_retains_values() -> None:
    deck = create_deck()
    experiment = create_experiment_result()

    result = MonteCarloDeckResult(
        deck=deck,
        experiment=experiment,
    )

    assert result.deck is deck
    assert result.experiment is experiment


def test_monte_carlo_deck_result_is_immutable() -> None:
    result = MonteCarloDeckResult(
        deck=create_deck(),
        experiment=create_experiment_result(),
    )

    with pytest.raises(AttributeError):
        result.experiment = create_experiment_result()  # type: ignore[misc]


def test_run_many_returns_immutable_tuple() -> None:
    deck = create_deck()
    experiment = create_experiment_result()

    experiment_manager = Mock(
        spec=ExperimentManager,
    )
    experiment_manager.run.return_value = experiment

    simulator = MonteCarloSimulator(
        experiment_manager=experiment_manager,
    )

    results = simulator.run_many(
        (
            deck,
        ),
    )

    assert isinstance(results, tuple)