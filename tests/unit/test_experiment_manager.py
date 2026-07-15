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
from krs.simulation.simulator_factory import (
    GoldfishSimulatorFactory,
)
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
    turns_started: int = 1,
    kinnan_activations: int = 0,
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
    turns_started: int = 1,
    kinnan_activations: int = 0,
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


def create_simulator_factory_mock() -> Mock:
    return Mock(
        spec=GoldfishSimulatorFactory,
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


def test_manager_creates_default_simulator_factory() -> None:
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
        manager.simulator_factory,
        GoldfishSimulatorFactory,
    )
    assert manager.simulator_factory.config is config


def test_manager_uses_injected_dependencies() -> None:
    config = SimulationConfig(
        games=1,
    )
    simulator = create_simulator_mock(
        config=config,
    )
    worker = create_worker_mock()
    simulator_factory = create_simulator_factory_mock()

    manager = ExperimentManager(
        simulator=simulator,
        worker=worker,
        simulator_factory=simulator_factory,
    )

    assert manager.worker is worker
    assert manager.simulator_factory is simulator_factory


def test_sequential_execution_uses_shared_worker() -> None:
    deck = create_deck()
    config = SimulationConfig(
        games=3,
        workers=1,
    )
    simulator = create_simulator_mock(
        config=config,
    )
    worker = create_worker_mock()
    simulator_factory = create_simulator_factory_mock()

    worker.run_game.side_effect = [
        create_worker_result(game_id=0),
        create_worker_result(game_id=1),
        create_worker_result(game_id=2),
    ]

    manager = ExperimentManager(
        simulator=simulator,
        worker=worker,
        simulator_factory=simulator_factory,
    )

    result = manager.run(deck)

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
    simulator_factory.create.assert_not_called()
    assert len(result.game_results) == 3


def test_parallel_execution_submits_isolated_method() -> None:
    deck = create_deck()
    config = SimulationConfig(
        games=2,
        workers=2,
    )
    simulator = create_simulator_mock(
        config=config,
    )
    worker = create_worker_mock()
    simulator_factory = create_simulator_factory_mock()

    with patch(
        "krs.simulation.experiment_manager.ThreadPoolExecutor",
    ) as executor_class:
        executor = executor_class.return_value.__enter__.return_value

        first_future = Mock()
        first_future.result.return_value = create_worker_result(
            game_id=0,
        )
        second_future = Mock()
        second_future.result.return_value = create_worker_result(
            game_id=1,
        )

        executor.submit.side_effect = [
            first_future,
            second_future,
        ]

        manager = ExperimentManager(
            simulator=simulator,
            worker=worker,
            simulator_factory=simulator_factory,
        )

        manager.run(deck)

    assert executor.submit.call_args_list == [
        call(
            manager._run_game_with_isolated_worker,
            deck,
            game_id=0,
            player_id=0,
            player_name="Player",
        ),
        call(
            manager._run_game_with_isolated_worker,
            deck,
            game_id=1,
            player_id=0,
            player_name="Player",
        ),
    ]


def test_isolated_execution_creates_new_simulator_and_worker() -> None:
    deck = create_deck()
    config = SimulationConfig(
        games=1,
        workers=2,
    )
    simulator = create_simulator_mock(
        config=config,
    )
    isolated_simulator = create_simulator_mock(
        config=config,
    )
    simulator_factory = create_simulator_factory_mock()
    simulator_factory.create.return_value = isolated_simulator

    expected_result = create_worker_result(
        game_id=7,
    )

    manager = ExperimentManager(
        simulator=simulator,
        simulator_factory=simulator_factory,
    )

    with patch(
        "krs.simulation.experiment_manager.SimulationWorker",
    ) as worker_class:
        isolated_worker = worker_class.return_value
        isolated_worker.run_game.return_value = expected_result

        result = manager._run_game_with_isolated_worker(
            deck,
            game_id=7,
            player_id=3,
            player_name="Junpei",
        )

    simulator_factory.create.assert_called_once_with()
    worker_class.assert_called_once_with(
        simulator=isolated_simulator,
    )
    isolated_worker.run_game.assert_called_once_with(
        deck,
        game_id=7,
        player_id=3,
        player_name="Junpei",
    )
    assert result is expected_result


def test_parallel_games_receive_different_simulators() -> None:
    deck = create_deck()
    config = SimulationConfig(
        games=2,
        workers=2,
    )
    simulator = create_simulator_mock(
        config=config,
    )
    first_simulator = create_simulator_mock(
        config=config,
    )
    second_simulator = create_simulator_mock(
        config=config,
    )

    simulator_factory = create_simulator_factory_mock()
    simulator_factory.create.side_effect = [
        first_simulator,
        second_simulator,
    ]

    manager = ExperimentManager(
        simulator=simulator,
        simulator_factory=simulator_factory,
    )

    with patch(
        "krs.simulation.experiment_manager.SimulationWorker",
    ) as worker_class:
        first_worker = Mock(
            spec=SimulationWorker,
        )
        first_worker.run_game.return_value = create_worker_result(
            game_id=0,
        )

        second_worker = Mock(
            spec=SimulationWorker,
        )
        second_worker.run_game.return_value = create_worker_result(
            game_id=1,
        )

        worker_class.side_effect = [
            first_worker,
            second_worker,
        ]

        first_result = manager._run_game_with_isolated_worker(
            deck,
            game_id=0,
            player_id=0,
            player_name="Player",
        )
        second_result = manager._run_game_with_isolated_worker(
            deck,
            game_id=1,
            player_id=0,
            player_name="Player",
        )

    assert simulator_factory.create.call_count == 2
    assert worker_class.call_args_list == [
        call(
            simulator=first_simulator,
        ),
        call(
            simulator=second_simulator,
        ),
    ]
    assert first_result.game_id == 0
    assert second_result.game_id == 1


def test_parallel_execution_does_not_use_shared_worker() -> None:
    deck = create_deck()
    config = SimulationConfig(
        games=1,
        workers=2,
    )
    simulator = create_simulator_mock(
        config=config,
    )
    shared_worker = create_worker_mock()
    isolated_simulator = create_simulator_mock(
        config=config,
    )
    simulator_factory = create_simulator_factory_mock()
    simulator_factory.create.return_value = isolated_simulator

    manager = ExperimentManager(
        simulator=simulator,
        worker=shared_worker,
        simulator_factory=simulator_factory,
    )

    with patch(
        "krs.simulation.experiment_manager.SimulationWorker",
    ) as worker_class:
        isolated_worker = worker_class.return_value
        isolated_worker.run_game.return_value = (
            create_worker_result(
                game_id=0,
            )
        )

        manager._run_game_with_isolated_worker(
            deck,
            game_id=0,
            player_id=0,
            player_name="Player",
        )

    shared_worker.run_game.assert_not_called()


def test_manager_orders_results_by_game_id() -> None:
    game_zero = create_worker_result(
        game_id=0,
        turns_started=2,
    )
    game_one = create_worker_result(
        game_id=1,
        turns_started=4,
    )
    game_two = create_worker_result(
        game_id=2,
        turns_started=3,
    )

    results = ExperimentManager._order_game_results(
        (
            game_two,
            game_zero,
            game_one,
        ),
    )

    assert results == (
        game_zero.result,
        game_one.result,
        game_two.result,
    )


def test_manager_rejects_duplicate_game_ids() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Worker results contain duplicate "
            "game_id values."
        ),
    ):
        ExperimentManager._order_game_results(
            (
                create_worker_result(game_id=0),
                create_worker_result(game_id=0),
            ),
        )


def test_manager_aggregates_results() -> None:
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
            reached_turn_limit=True,
        ),
    ]

    manager = ExperimentManager(
        simulator=simulator,
        worker=worker,
    )

    result = manager.run(deck)

    assert isinstance(
        result,
        ExperimentResult,
    )
    assert result.summary.games_completed == 3
    assert result.summary.wins == 2
    assert result.summary.non_wins == 1
    assert result.summary.turn_limit_games == 1
    assert result.summary.total_turns_started == 12
    assert result.summary.total_kinnan_activations == 4
    assert result.summary.fastest_win_turn == 2


def test_parallel_worker_exception_is_propagated() -> None:
    deck = create_deck()
    config = SimulationConfig(
        games=1,
        workers=2,
    )
    simulator = create_simulator_mock(
        config=config,
    )

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
        )

        with pytest.raises(
            RuntimeError,
            match="Simulation failed.",
        ):
            manager.run(deck)