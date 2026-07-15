from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from krs.ai.strategy_factory import StrategyFactory
from krs.engine.game_engine import GameEngine
from krs.simulation.experiment_manager import ExperimentManager
from krs.simulation.monte_carlo import MonteCarloSimulator
from krs.simulation.simulation_config import SimulationConfig
from krs.simulation.simulation_factory import SimulationFactory
from krs.simulation.simulator import GoldfishSimulator
from krs.simulation.simulator_factory import (
    GoldfishSimulatorFactory,
)


def write_strategy(
    directory: Path,
    *,
    name: str,
) -> None:
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        directory / f"{name}.yaml"
    ).write_text(
        f"""
name: {name}
weights:
  mana_value: 1
  mana_ability: 2
  untap: 5
  copy: 4
  combo: 3
custom_scores: {{}}
combo_card_ids: []
""",
        encoding="utf-8",
    )


def write_simulation_config(
    path: Path,
    *,
    strategy: str,
    workers: int = 1,
) -> None:
    path.write_text(
        f"""
strategy: {strategy}
games: 100
max_turns: 5
seed: 123
workers: {workers}
mulligan:
  enabled: true
replay:
  enabled: false
""",
        encoding="utf-8",
    )


def create_factory(
    tmp_path: Path,
    *,
    strategy_name: str = "balanced",
) -> SimulationFactory:
    strategy_directory = tmp_path / "strategies"

    write_strategy(
        strategy_directory,
        name=strategy_name,
    )

    return SimulationFactory(
        strategy_factory=StrategyFactory(
            strategy_directory=strategy_directory,
        ),
    )


def test_factory_loads_config(
    tmp_path: Path,
) -> None:
    factory = create_factory(tmp_path)

    simulation_path = tmp_path / "simulation.yaml"
    write_simulation_config(
        simulation_path,
        strategy="balanced",
        workers=4,
    )

    config = factory.load_config(
        simulation_path,
    )

    assert config.strategy_name == "balanced"
    assert config.games == 100
    assert config.max_turns == 5
    assert config.seed == 123
    assert config.workers == 4


def test_factory_creates_game_engine(
    tmp_path: Path,
) -> None:
    factory = create_factory(
        tmp_path,
        strategy_name="combo",
    )

    config = SimulationConfig(
        strategy_name="combo",
    )

    engine = factory.create_game_engine(
        config,
    )

    assert isinstance(
        engine,
        GameEngine,
    )


def test_factory_creates_simulator_factory(
    tmp_path: Path,
) -> None:
    factory = create_factory(tmp_path)
    config = SimulationConfig()

    simulator_factory = (
        factory.create_simulator_factory(
            config,
        )
    )

    assert isinstance(
        simulator_factory,
        GoldfishSimulatorFactory,
    )
    assert simulator_factory.config is config


def test_simulator_factory_creates_fresh_engines(
    tmp_path: Path,
) -> None:
    factory = create_factory(tmp_path)
    config = SimulationConfig()

    simulator_factory = (
        factory.create_simulator_factory(
            config,
        )
    )

    first_simulator = simulator_factory.create()
    second_simulator = simulator_factory.create()

    assert first_simulator is not second_simulator
    assert (
        first_simulator.game_engine
        is not second_simulator.game_engine
    )


def test_factory_creates_goldfish_simulator(
    tmp_path: Path,
) -> None:
    factory = create_factory(tmp_path)
    config = SimulationConfig()

    simulator = factory.create_goldfish_simulator(
        config,
    )

    assert isinstance(
        simulator,
        GoldfishSimulator,
    )
    assert simulator.config is config
    assert isinstance(
        simulator.game_engine,
        GameEngine,
    )


def test_factory_creates_experiment_manager(
    tmp_path: Path,
) -> None:
    factory = create_factory(tmp_path)
    config = SimulationConfig(
        workers=4,
    )

    manager = factory.create_experiment_manager(
        config,
    )

    assert isinstance(
        manager,
        ExperimentManager,
    )
    assert manager.simulator.config is config
    assert manager.simulator_factory is not None
    assert manager.simulator_factory.config is config


def test_factory_creates_monte_carlo_simulator(
    tmp_path: Path,
) -> None:
    factory = create_factory(tmp_path)
    config = SimulationConfig()

    simulator = (
        factory.create_monte_carlo_simulator(
            config,
        )
    )

    assert isinstance(
        simulator,
        MonteCarloSimulator,
    )
    assert isinstance(
        simulator.experiment_manager,
        ExperimentManager,
    )
    assert (
        simulator
        .experiment_manager
        .simulator
        .config
        is config
    )


def test_factory_creates_config_and_engine_from_file(
    tmp_path: Path,
) -> None:
    factory = create_factory(tmp_path)

    config_path = tmp_path / "simulation.yaml"
    write_simulation_config(
        config_path,
        strategy="balanced",
    )

    config, engine = factory.create_from_file(
        config_path,
    )

    assert config.strategy_name == "balanced"
    assert isinstance(
        engine,
        GameEngine,
    )


def test_factory_creates_monte_carlo_from_file(
    tmp_path: Path,
) -> None:
    factory = create_factory(tmp_path)

    config_path = tmp_path / "simulation.yaml"
    write_simulation_config(
        config_path,
        strategy="balanced",
        workers=3,
    )

    config, simulator = (
        factory.create_monte_carlo_from_file(
            config_path,
        )
    )

    assert config.workers == 3
    assert isinstance(
        simulator,
        MonteCarloSimulator,
    )
    assert (
        simulator
        .experiment_manager
        .simulator
        .config
        is config
    )


def test_create_experiment_manager_uses_same_factory(
    tmp_path: Path,
) -> None:
    factory = create_factory(tmp_path)
    config = SimulationConfig(
        workers=2,
    )

    with patch(
        "krs.simulation.simulation_factory."
        "GoldfishSimulatorFactory",
    ) as simulator_factory_class:
        simulator_factory = (
            simulator_factory_class.return_value
        )
        simulator = Mock(
            spec=GoldfishSimulator,
        )
        simulator.config = config
        simulator_factory.create.return_value = simulator

        manager = factory.create_experiment_manager(
            config,
        )

    simulator_factory_class.assert_called_once()
    simulator_factory.create.assert_called_once_with()
    assert manager.simulator is simulator
    assert manager.simulator_factory is simulator_factory


def test_factory_rejects_unknown_strategy(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "simulation.yaml"

    write_simulation_config(
        config_path,
        strategy="missing",
    )

    factory = SimulationFactory(
        strategy_factory=StrategyFactory(
            strategy_directory=(
                tmp_path / "strategies"
            ),
        ),
    )

    with pytest.raises(
        FileNotFoundError,
        match="Strategy file not found",
    ):
        factory.create_from_file(
            config_path,
        )


def test_monte_carlo_factory_rejects_unknown_strategy(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "simulation.yaml"

    write_simulation_config(
        config_path,
        strategy="missing",
    )

    factory = SimulationFactory(
        strategy_factory=StrategyFactory(
            strategy_directory=(
                tmp_path / "strategies"
            ),
        ),
    )

    with pytest.raises(
        FileNotFoundError,
        match="Strategy file not found",
    ):
        factory.create_monte_carlo_from_file(
            config_path,
        )