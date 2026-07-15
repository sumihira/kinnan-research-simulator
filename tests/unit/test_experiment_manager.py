from __future__ import annotations

from unittest.mock import Mock, call, patch

import pytest

from krs.cards.card import Card
from krs.decks.deck import Deck
from krs.simulation.experiment import ExperimentResult
from krs.simulation.experiment_manager import ExperimentManager
from krs.simulation.runner import GoldfishRunResult
from krs.simulation.simulation_config import SimulationConfig
from krs.simulation.simulator import GoldfishSimulator
from krs.simulation.worker import (
    SimulationGameResult,
    SimulationWorker,
)


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


def create_worker_result(
    *,
    game_id: int,
    turns_started: int,
    kinnan_activations: int,
    reached_turn_limit: bool = False,
    game_over: bool = False,
    winner: str | None = None,
) -> SimulationGameResult:
    return SimulationGameResult(
        game_id=game_id,
        result=create_result(
            turns_started=turns_started,
            kinnan_activations=kinnan_activations,
            reached_turn_limit=reached_turn_limit,
            game_over=game_over,
            winner=winner,
        ),
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


def create_worker_mock() -> Mock:
    return Mock(
        spec=SimulationWorker,
    )


def test_manager_creates_default_worker() -> None:
    config = SimulationConfig(
        games=1,
    )
    simulator = create_simulator_mock(
        config=config,
    )

    manager = ExperimentManager(
        simulator=simulator,
    )

    assert isinstance(
        manager.worker,
        SimulationWorker,
    )
    assert manager.worker.simulator is simulator


def test_manager_uses_injected_worker() -> None:
    config = SimulationConfig(
        games=1,
    )
    simulator = create_simulator_mock(
        config=config,
    )
    worker = create_worker_mock()

    manager = ExperimentManager(
        simulator=simulator,
        worker=worker,
    )

    assert manager.worker is worker


def test_manager_executes_configured_number_of_games() -> None:
    deck = create_deck()
    config = SimulationConfig(
        games=3,
    )

    simulator = create_simulator_mock(
        config=config,
    )
    worker = create_worker_mock()
    worker.run_game.side_effect = [
        create_worker_result(
            game_id=0,
            turns_started=2,
            kinnan_activations=1,
        ),
        create_worker_result(
            game_id=1,
            turns_started=3,
            kinnan_activations=2,
        ),
        create_worker_result(
            game_id=2,
            turns_started=4,
            kinnan_activations=3,
        ),
    ]

    manager = ExperimentManager(
        simulator=simulator,
        worker=worker,
    )

    result = manager.run(deck)

    assert worker.run_game.call_count == 3
    assert len(result.game_results) == 3
    assert result.summary.games_completed == 3


def test_manager_uses_sequential_game_ids() -> None:
    deck = create_deck()
    config = SimulationConfig(
        games=3,
        workers=1,
    )

    simulator = create_simulator_mock(
        config=config,
    )
    worker = create_worker_mock()
    worker.run_game.side_effect = [
        create_worker_result(
            game_id=0,
            turns_started=1,
            kinnan_activations=0,
        ),
        create_worker_result(
            game_id=1,
            turns_started=1,
            kinnan_activations=0,
        ),
        create_worker_result(
            game_id=2,
            turns_started=1,
            kinnan_activations=0,
        ),
    ]

    manager = ExperimentManager(
        simulator=simulator,
        worker=worker,
    )

    manager.run(deck)

    assert worker.run_game.call_args_list == [
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


def test_manager_uses_sequential_execution_with_one_worker() -> None:
    deck = create_deck()
    config = SimulationConfig(
        games=1,
        workers=1,
    )

    simulator = create_simulator_mock(
        config=config,
    )
    worker = create_worker_mock()
    worker.run_game.return_value = create_worker_result(
        game_id=0,
        turns_started=1,
        kinnan_activations=0,
    )

    manager = ExperimentManager(
        simulator=simulator,
        worker=worker,
    )

    with patch(
        "krs.simulation.experiment_manager.ThreadPoolExecutor",
    ) as executor_class:
        manager.run(deck)

    executor_class.assert_not_called()


def test_manager_uses_configured_thread_workers() -> None:
    deck = create_deck()
    config = SimulationConfig(
        games=3,
        workers=2,
    )

    simulator = create_simulator_mock(
        config=config,
    )
    worker = create_worker_mock()

    expected_results = [
        create_worker_result(
            game_id=0,
            turns_started=1,
            kinnan_activations=0,
        ),
        create_worker_result(
            game_id=1,
            turns_started=2,
            kinnan_activations=1,
        ),
        create_worker_result(
            game_id=2,
            turns_started=3,
            kinnan_activations=2,
        ),
    ]

    with patch(
        "krs.simulation.experiment_manager.ThreadPoolExecutor",
    ) as executor_class:
        executor = executor_class.return_value.__enter__.return_value

        futures = [
            Mock(),
            Mock(),
            Mock(),
        ]

        for future, worker_result in zip(
            futures,
            expected_results,
            strict=True,
        ):
            future.result.return_value = worker_result

        executor.submit.side_effect = futures

        manager = ExperimentManager(
            simulator=simulator,
            worker=worker,
        )

        result = manager.run(deck)

    executor_class.assert_called_once_with(
        max_workers=2,
    )
    assert executor.submit.call_count == 3
    assert result.game_results == tuple(
        worker_result.result
        for worker_result in expected_results
    )


def test_manager_submits_all_game_ids_to_executor() -> None:
    deck = create_deck()
    config = SimulationConfig(
        games=3,
        workers=2,
    )

    simulator = create_simulator_mock(
        config=config,
    )
    worker = create_worker_mock()

    worker_results = [
        create_worker_result(
            game_id=0,
            turns_started=1,
            kinnan_activations=0,
        ),
        create_worker_result(
            game_id=1,
            turns_started=1,
            kinnan_activations=0,
        ),
        create_worker_result(
            game_id=2,
            turns_started=1,
            kinnan_activations=0,
        ),
    ]

    with patch(
        "krs.simulation.experiment_manager.ThreadPoolExecutor",
    ) as executor_class:
        executor = executor_class.return_value.__enter__.return_value

        futures = [
            Mock(),
            Mock(),
            Mock(),
        ]

        for future, worker_result in zip(
            futures,
            worker_results,
            strict=True,
        ):
            future.result.return_value = worker_result

        executor.submit.side_effect = futures

        manager = ExperimentManager(
            simulator=simulator,
            worker=worker,
        )

        manager.run(deck)

    assert executor.submit.call_args_list == [
        call(
            manager._run_game,
            deck,
            game_id=0,
            player_id=0,
            player_name="Player",
        ),
        call(
            manager._run_game,
            deck,
            game_id=1,
            player_id=0,
            player_name="Player",
        ),
        call(
            manager._run_game,
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
    worker = create_worker_mock()
    worker.run_game.return_value = create_worker_result(
        game_id=0,
        turns_started=1,
        kinnan_activations=0,
    )

    manager = ExperimentManager(
        simulator=simulator,
        worker=worker,
    )

    manager.run(
        deck,
        player_id=7,
        player_name="Junpei",
    )

    worker.run_game.assert_called_once_with(
        deck,
        game_id=0,
        player_id=7,
        player_name="Junpei",
    )


def test_manager_aggregates_worker_results() -> None:
    deck = create_deck()
    config = SimulationConfig(
        games=3,
    )

    simulator = create_simulator_mock(
        config=config,
    )
    worker = create_worker_mock()
    worker.run_game.side_effect = [
        create_worker_result(
            game_id=0,
            turns_started=2,
            kinnan_activations=1,
            game_over=True,
            winner="Player",
        ),
        create_worker_result(
            game_id=1,
            turns_started=4,
            kinnan_activations=3,
            game_over=True,
            winner="Player",
        ),
        create_worker_result(
            game_id=2,
            turns_started=6,
            kinnan_activations=0,
            reached_turn_limit=True,
        ),
    ]

    manager = ExperimentManager(
        simulator=simulator,
        worker=worker,
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


def test_manager_orders_results_by_game_id() -> None:
    deck = create_deck()
    config = SimulationConfig(
        games=3,
    )

    game_zero = create_worker_result(
        game_id=0,
        turns_started=2,
        kinnan_activations=1,
    )
    game_one = create_worker_result(
        game_id=1,
        turns_started=5,
        kinnan_activations=4,
    )
    game_two = create_worker_result(
        game_id=2,
        turns_started=3,
        kinnan_activations=2,
    )

    simulator = create_simulator_mock(
        config=config,
    )
    worker = create_worker_mock()

    worker.run_game.side_effect = [
        game_two,
        game_zero,
        game_one,
    ]

    manager = ExperimentManager(
        simulator=simulator,
        worker=worker,
    )

    result = manager.run(deck)

    assert result.game_results == (
        game_zero.result,
        game_one.result,
        game_two.result,
    )


def test_manager_rejects_duplicate_game_ids() -> None:
    deck = create_deck()
    config = SimulationConfig(
        games=2,
    )

    simulator = create_simulator_mock(
        config=config,
    )
    worker = create_worker_mock()
    worker.run_game.side_effect = [
        create_worker_result(
            game_id=0,
            turns_started=2,
            kinnan_activations=1,
        ),
        create_worker_result(
            game_id=0,
            turns_started=3,
            kinnan_activations=2,
        ),
    ]

    manager = ExperimentManager(
        simulator=simulator,
        worker=worker,
    )

    with pytest.raises(
        ValueError,
        match=(
            "Worker results contain duplicate "
            "game_id values."
        ),
    ):
        manager.run(deck)


def test_manager_propagates_parallel_worker_exception() -> None:
    deck = create_deck()
    config = SimulationConfig(
        games=1,
        workers=2,
    )

    simulator = create_simulator_mock(
        config=config,
    )
    worker = create_worker_mock()

    with patch(
        "krs.simulation.experiment_manager.ThreadPoolExecutor",
    ) as executor_class:
        executor = executor_class.return_value.__enter__.return_value
        future = Mock()
        future.result.side_effect = RuntimeError(
            "Simulation failed."
        )
        executor.submit.return_value = future

        manager = ExperimentManager(
            simulator=simulator,
            worker=worker,
        )

        with pytest.raises(
            RuntimeError,
            match="Simulation failed.",
        ):
            manager.run(deck)


def test_manager_does_not_call_simulator_directly() -> None:
    deck = create_deck()
    config = SimulationConfig(
        games=1,
    )

    simulator = create_simulator_mock(
        config=config,
    )
    worker = create_worker_mock()
    worker.run_game.return_value = create_worker_result(
        game_id=0,
        turns_started=1,
        kinnan_activations=0,
    )

    manager = ExperimentManager(
        simulator=simulator,
        worker=worker,
    )

    manager.run(deck)

    simulator.simulate_game.assert_not_called()


def test_manager_returns_immutable_result_collection() -> None:
    deck = create_deck()
    config = SimulationConfig(
        games=1,
    )

    simulator = create_simulator_mock(
        config=config,
    )
    worker = create_worker_mock()
    worker.run_game.return_value = create_worker_result(
        game_id=0,
        turns_started=1,
        kinnan_activations=0,
    )

    manager = ExperimentManager(
        simulator=simulator,
        worker=worker,
    )

    result = manager.run(deck)

    assert isinstance(
        result.game_results,
        tuple,
    )