from pathlib import Path

import pytest

from krs.ai.strategy_factory import StrategyFactory
from krs.engine.game_engine import GameEngine
from krs.simulation.simulation_factory import (
    SimulationFactory,
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

    (directory / f"{name}.yaml").write_text(
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
) -> None:
    path.write_text(
        f"""
strategy: {strategy}
games: 100
max_turns: 5
seed: 123

mulligan:
  enabled: true

replay:
  enabled: false
""",
        encoding="utf-8",
    )


def test_factory_loads_config(
    tmp_path: Path,
) -> None:
    strategy_directory = tmp_path / "strategies"
    write_strategy(
        strategy_directory,
        name="balanced",
    )

    simulation_path = tmp_path / "simulation.yaml"
    write_simulation_config(
        simulation_path,
        strategy="balanced",
    )

    factory = SimulationFactory(
        strategy_factory=StrategyFactory(
            strategy_directory=strategy_directory
        )
    )

    config = factory.load_config(
        simulation_path
    )

    assert config.strategy_name == "balanced"
    assert config.games == 100
    assert config.max_turns == 5
    assert config.seed == 123


def test_factory_creates_game_engine(
    tmp_path: Path,
) -> None:
    strategy_directory = tmp_path / "strategies"
    write_strategy(
        strategy_directory,
        name="combo",
    )

    factory = SimulationFactory(
        strategy_factory=StrategyFactory(
            strategy_directory=strategy_directory
        )
    )

    config_path = tmp_path / "simulation.yaml"
    write_simulation_config(
        config_path,
        strategy="combo",
    )

    config = factory.load_config(config_path)
    engine = factory.create_game_engine(config)

    assert isinstance(engine, GameEngine)


def test_factory_creates_config_and_engine_from_file(
    tmp_path: Path,
) -> None:
    strategy_directory = tmp_path / "strategies"
    write_strategy(
        strategy_directory,
        name="balanced",
    )

    config_path = tmp_path / "simulation.yaml"
    write_simulation_config(
        config_path,
        strategy="balanced",
    )

    factory = SimulationFactory(
        strategy_factory=StrategyFactory(
            strategy_directory=strategy_directory
        )
    )

    config, engine = factory.create_from_file(
        config_path
    )

    assert config.strategy_name == "balanced"
    assert isinstance(engine, GameEngine)


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
            strategy_directory=tmp_path / "strategies"
        )
    )

    with pytest.raises(
        FileNotFoundError,
        match="Strategy file not found",
    ):
        factory.create_from_file(config_path)