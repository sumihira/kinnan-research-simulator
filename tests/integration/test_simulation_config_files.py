from pathlib import Path

from krs.simulation.simulation_factory import (
    SimulationFactory,
)


def test_default_simulation_config_can_build_engine() -> None:
    config_path = Path(
        "config/simulation/default.yaml"
    )

    config, engine = (
        SimulationFactory()
        .create_from_file(config_path)
    )

    assert config.strategy_name == "balanced"
    assert config.games == 1000
    assert config.max_turns == 6
    assert engine is not None