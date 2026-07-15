from __future__ import annotations

from unittest.mock import Mock, call

from krs.cards.card import Card
from krs.decks.deck import Deck
from krs.simulation.experiment import ExperimentResult
from krs.simulation.experiment_manager import ExperimentManager
from krs.simulation.runner import GoldfishRunResult
from krs.simulation.simulation_config import SimulationConfig
from krs.simulation.simulator import GoldfishSimulator


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


def create_deck() -> Deck:
    commander = create_card(
        card_id="kinnan-id",
        name="Kinnan, Bonder Prodigy",
        type_line="Legendary Creature — Human Druid",
    )

    cards = [
        create_card(
            card_id=f"forest-{index}",
            name="Forest",
            type_line="Basic Land — Forest",
        )
        for index in range(10)
    ]

    return Deck(
        name="Kinnan Test",
        commander=commander,
        cards=cards,
    )


def create_result(
    *,
    turns_started: int,
    kinnan_activations: int,
    reached_turn_limit: bool = False,
    game_over: bool = False,
    winner: str | None = None,
) -> GoldfishRunResult:
    return GoldfishRunResult(
        turns_started=turns_started,
        kinnan_activations=kinnan_activations,
        reached_turn_limit=reached_turn_limit,
        game_over=game_over,
        winner=winner,
    )


def create_simulator_mock(
    *,
    config: SimulationConfig,
) -> Mock:
    simulator = Mock(
        spec=GoldfishSimulator,
    )
    simulator.config = config
    return simulator


def test_manager_executes_configured_number_of_games() -> None:
    deck = create_deck()
    config = SimulationConfig(
        games=3,
    )

    simulator = create_simulator_mock(
        config=config,
    )
    simulator.simulate_game.side_effect = [
        create_result(
            turns_started=2,
            kinnan_activations=1,
        ),
        create_result(
            turns_started=3,
            kinnan_activations=2,
        ),
        create_result(
            turns_started=4,
            kinnan_activations=3,
        ),
    ]

    manager = ExperimentManager(
        simulator=simulator,
    )

    result = manager.run(deck)

    assert simulator.simulate_game.call_count == 3
    assert len(result.game_results) == 3
    assert result.summary.games_completed == 3


def test_manager_uses_sequential_game_ids() -> None:
    deck = create_deck()
    config = SimulationConfig(
        games=3,
    )

    simulator = create_simulator_mock(
        config=config,
    )
    simulator.simulate_game.return_value = create_result(
        turns_started=1,
        kinnan_activations=0,
    )

    manager = ExperimentManager(
        simulator=simulator,
    )

    manager.run(deck)

    assert simulator.simulate_game.call_args_list == [
        call(
            deck,
            game_id=0,
            player_id=0,
            player_name="Player",
        ),
        call(
            deck,
            game_id=1,
            player_id=0,
            player_name="Player",
        ),
        call(
            deck,
            game_id=2,
            player_id=0,
            player_name="Player",
        ),
    ]


def test_manager_passes_custom_player_values() -> None:
    deck = create_deck()
    config = SimulationConfig(
        games=1,
    )

    simulator = create_simulator_mock(
        config=config,
    )
    simulator.simulate_game.return_value = create_result(
        turns_started=1,
        kinnan_activations=0,
    )

    manager = ExperimentManager(
        simulator=simulator,
    )

    manager.run(
        deck,
        player_id=7,
        player_name="Junpei",
    )

    simulator.simulate_game.assert_called_once_with(
        deck,
        game_id=0,
        player_id=7,
        player_name="Junpei",
    )


def test_manager_aggregates_results() -> None:
    deck = create_deck()
    config = SimulationConfig(
        games=3,
    )

    simulator = create_simulator_mock(
        config=config,
    )
    simulator.simulate_game.side_effect = [
        create_result(
            turns_started=2,
            kinnan_activations=1,
            game_over=True,
            winner="Player",
        ),
        create_result(
            turns_started=4,
            kinnan_activations=3,
            game_over=True,
            winner="Player",
        ),
        create_result(
            turns_started=6,
            kinnan_activations=0,
            reached_turn_limit=True,
        ),
    ]

    manager = ExperimentManager(
        simulator=simulator,
    )

    result = manager.run(deck)

    assert isinstance(result, ExperimentResult)
    assert result.config is config
    assert result.summary.games_requested == 3
    assert result.summary.games_completed == 3
    assert result.summary.wins == 2
    assert result.summary.non_wins == 1
    assert result.summary.turn_limit_games == 1
    assert result.summary.total_turns_started == 12
    assert result.summary.total_kinnan_activations == 4
    assert result.summary.fastest_win_turn == 2
    assert result.summary.win_rate == 2 / 3


def test_manager_preserves_game_result_order() -> None:
    deck = create_deck()
    config = SimulationConfig(
        games=2,
    )

    first_result = create_result(
        turns_started=2,
        kinnan_activations=1,
    )
    second_result = create_result(
        turns_started=5,
        kinnan_activations=4,
    )

    simulator = create_simulator_mock(
        config=config,
    )
    simulator.simulate_game.side_effect = [
        first_result,
        second_result,
    ]

    manager = ExperimentManager(
        simulator=simulator,
    )

    result = manager.run(deck)

    assert result.game_results == (
        first_result,
        second_result,
    )


def test_manager_returns_immutable_result_collections() -> None:
    deck = create_deck()
    config = SimulationConfig(
        games=1,
    )

    simulator = create_simulator_mock(
        config=config,
    )
    simulator.simulate_game.return_value = create_result(
        turns_started=1,
        kinnan_activations=0,
    )

    manager = ExperimentManager(
        simulator=simulator,
    )

    result = manager.run(deck)

    assert isinstance(result.game_results, tuple)