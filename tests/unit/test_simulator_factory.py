from __future__ import annotations

from unittest.mock import Mock, call, patch

from krs.engine.game_engine import GameEngine
from krs.simulation.game_state_factory import GameStateFactory
from krs.simulation.simulation_config import SimulationConfig
from krs.simulation.simulator import GoldfishSimulator
from krs.simulation.simulator_factory import (
    GoldfishSimulatorFactory,
)


def test_factory_creates_goldfish_simulator() -> None:
    config = SimulationConfig()
    game_engine = Mock(
        spec=GameEngine,
    )
    state_factory = Mock(
        spec=GameStateFactory,
    )

    game_engine_factory = Mock(
        return_value=game_engine,
    )
    state_factory_factory = Mock(
        return_value=state_factory,
    )

    factory = GoldfishSimulatorFactory(
        config=config,
        game_engine_factory=game_engine_factory,
        state_factory_factory=state_factory_factory,
    )

    simulator = factory.create()

    assert isinstance(
        simulator,
        GoldfishSimulator,
    )
    assert simulator.config is config
    assert simulator.game_engine is game_engine
    assert simulator.state_factory is state_factory


def test_factory_creates_new_components_each_time() -> None:
    config = SimulationConfig()

    first_engine = Mock(
        spec=GameEngine,
    )
    second_engine = Mock(
        spec=GameEngine,
    )
    first_state_factory = Mock(
        spec=GameStateFactory,
    )
    second_state_factory = Mock(
        spec=GameStateFactory,
    )

    game_engine_factory = Mock(
        side_effect=[
            first_engine,
            second_engine,
        ],
    )
    state_factory_factory = Mock(
        side_effect=[
            first_state_factory,
            second_state_factory,
        ],
    )

    factory = GoldfishSimulatorFactory(
        config=config,
        game_engine_factory=game_engine_factory,
        state_factory_factory=state_factory_factory,
    )

    first_simulator = factory.create()
    second_simulator = factory.create()

    assert first_simulator is not second_simulator
    assert first_simulator.game_engine is first_engine
    assert second_simulator.game_engine is second_engine
    assert first_simulator.state_factory is first_state_factory
    assert second_simulator.state_factory is second_state_factory
    assert game_engine_factory.call_count == 2
    assert state_factory_factory.call_count == 2


def test_factory_uses_configured_strategy_by_default() -> None:
    config = SimulationConfig(
        strategy_name="combo",
    )
    state_factory = Mock(
        spec=GameStateFactory,
    )

    factory = GoldfishSimulatorFactory(
        config=config,
        state_factory_factory=Mock(
            return_value=state_factory,
        ),
    )

    with patch.object(
        GameEngine,
        "from_strategy",
    ) as from_strategy:
        game_engine = Mock(
            spec=GameEngine,
        )
        from_strategy.return_value = game_engine

        simulator = factory.create()

    from_strategy.assert_called_once_with(
        "combo",
    )
    assert simulator.game_engine is game_engine


def test_factory_uses_injected_game_engine_factory() -> None:
    config = SimulationConfig()
    game_engine = Mock(
        spec=GameEngine,
    )
    game_engine_factory = Mock(
        return_value=game_engine,
    )

    factory = GoldfishSimulatorFactory(
        config=config,
        game_engine_factory=game_engine_factory,
    )

    with patch.object(
        GameEngine,
        "from_strategy",
    ) as from_strategy:
        simulator = factory.create()

    game_engine_factory.assert_called_once_with()
    from_strategy.assert_not_called()
    assert simulator.game_engine is game_engine


def test_factory_creates_state_factory_for_every_simulator() -> None:
    config = SimulationConfig()
    state_factory_factory = Mock(
        side_effect=[
            Mock(spec=GameStateFactory),
            Mock(spec=GameStateFactory),
            Mock(spec=GameStateFactory),
        ],
    )

    factory = GoldfishSimulatorFactory(
        config=config,
        game_engine_factory=Mock(
            side_effect=[
                Mock(spec=GameEngine),
                Mock(spec=GameEngine),
                Mock(spec=GameEngine),
            ],
        ),
        state_factory_factory=state_factory_factory,
    )

    factory.create()
    factory.create()
    factory.create()

    assert state_factory_factory.call_args_list == [
        call(),
        call(),
        call(),
    ]


def test_factory_retains_same_immutable_config() -> None:
    config = SimulationConfig(
        games=100,
        workers=4,
        seed=12345,
    )

    factory = GoldfishSimulatorFactory(
        config=config,
        game_engine_factory=Mock(
            return_value=Mock(
                spec=GameEngine,
            ),
        ),
    )

    first_simulator = factory.create()
    second_simulator = factory.create()

    assert first_simulator.config is config
    assert second_simulator.config is config