from pathlib import Path

import pytest

from krs.simulation.simulation_config_loader import (
    SimulationConfigLoader,
)


def write_config(
    path: Path,
    content: str,
) -> Path:
    path.write_text(
        content,
        encoding="utf-8",
    )
    return path


def test_loads_complete_simulation_config(
    tmp_path: Path,
) -> None:
    path = write_config(
        tmp_path / "simulation.yaml",
        """
locale: en
strategy: combo
games: 5000
max_turns: 8
seed: 12345
workers: 4
mulligan:
  enabled: false
replay:
  enabled: true
""",
    )

    config = SimulationConfigLoader().load(path)

    assert config.locale == "en"
    assert config.strategy_name == "combo"
    assert config.games == 5000
    assert config.max_turns == 8
    assert config.seed == 12345
    assert config.workers == 4
    assert config.mulligan_enabled is False
    assert config.save_replays is True


def test_missing_optional_values_use_defaults(
    tmp_path: Path,
) -> None:
    path = write_config(
        tmp_path / "minimal.yaml",
        """
strategy: balanced
""",
    )

    config = SimulationConfigLoader().load(path)

    assert config.locale == "ja"
    assert config.strategy_name == "balanced"
    assert config.games == 1000
    assert config.max_turns == 6
    assert config.seed is None
    assert config.workers == 1
    assert config.mulligan_enabled is True
    assert config.save_replays is False


def test_missing_strategy_uses_balanced(
    tmp_path: Path,
) -> None:
    path = write_config(
        tmp_path / "default-strategy.yaml",
        """
games: 100
""",
    )

    config = SimulationConfigLoader().load(path)

    assert config.strategy_name == "balanced"


def test_missing_file_is_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "missing.yaml"

    with pytest.raises(
        FileNotFoundError,
        match="Simulation config file not found",
    ):
        SimulationConfigLoader().load(path)


def test_directory_path_is_rejected(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="Simulation config path is not a file",
    ):
        SimulationConfigLoader().load(tmp_path)


def test_empty_file_is_rejected(
    tmp_path: Path,
) -> None:
    path = write_config(
        tmp_path / "empty.yaml",
        "",
    )

    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        SimulationConfigLoader().load(path)


def test_non_mapping_config_is_rejected(
    tmp_path: Path,
) -> None:
    path = write_config(
        tmp_path / "list.yaml",
        """
- balanced
- combo
""",
    )

    with pytest.raises(
        ValueError,
        match="must be a mapping",
    ):
        SimulationConfigLoader().load(path)


def test_strategy_rejects_non_string_value(
    tmp_path: Path,
) -> None:
    path = write_config(
        tmp_path / "strategy.yaml",
        """
strategy: 123
""",
    )

    with pytest.raises(
        ValueError,
        match="strategy must be a string",
    ):
        SimulationConfigLoader().load(path)


@pytest.mark.parametrize(
    ("field_name", "content"),
    [
        (
            "games",
            """
strategy: balanced
games: one-thousand
""",
        ),
        (
            "max_turns",
            """
strategy: balanced
max_turns: six
""",
        ),
        (
            "seed",
            """
strategy: balanced
seed: random
""",
        ),
        (
            "workers",
            """
strategy: balanced
workers: four
""",
        ),
    ],
)
def test_integer_fields_reject_non_integer_values(
    tmp_path: Path,
    field_name: str,
    content: str,
) -> None:
    path = write_config(
        tmp_path / f"{field_name}.yaml",
        content,
    )

    with pytest.raises(
        ValueError,
        match=rf"{field_name} must be an integer",
    ):
        SimulationConfigLoader().load(path)


@pytest.mark.parametrize(
    ("field_name", "content"),
    [
        (
            "games",
            """
strategy: balanced
games: true
""",
        ),
        (
            "max_turns",
            """
strategy: balanced
max_turns: false
""",
        ),
        (
            "seed",
            """
strategy: balanced
seed: true
""",
        ),
        (
            "workers",
            """
strategy: balanced
workers: true
""",
        ),
    ],
)
def test_integer_fields_reject_boolean_values(
    tmp_path: Path,
    field_name: str,
    content: str,
) -> None:
    path = write_config(
        tmp_path / f"{field_name}.yaml",
        content,
    )

    with pytest.raises(
        ValueError,
        match=rf"{field_name} must be an integer",
    ):
        SimulationConfigLoader().load(path)


@pytest.mark.parametrize(
    "workers",
    [
        0,
        -1,
        -10,
    ],
)
def test_workers_must_be_positive(
    tmp_path: Path,
    workers: int,
) -> None:
    path = write_config(
        tmp_path / "workers.yaml",
        f"""
strategy: balanced
workers: {workers}
""",
    )

    with pytest.raises(
        ValueError,
        match="Number of workers must be greater than zero",
    ):
        SimulationConfigLoader().load(path)


def test_mulligan_must_be_mapping(
    tmp_path: Path,
) -> None:
    path = write_config(
        tmp_path / "mulligan.yaml",
        """
strategy: balanced
mulligan: true
""",
    )

    with pytest.raises(
        ValueError,
        match="mulligan must be a mapping",
    ):
        SimulationConfigLoader().load(path)


def test_replay_must_be_mapping(
    tmp_path: Path,
) -> None:
    path = write_config(
        tmp_path / "replay.yaml",
        """
strategy: balanced
replay: false
""",
    )

    with pytest.raises(
        ValueError,
        match="replay must be a mapping",
    ):
        SimulationConfigLoader().load(path)


def test_yaml_boolean_values_are_supported(
    tmp_path: Path,
) -> None:
    path = write_config(
        tmp_path / "boolean.yaml",
        """
strategy: balanced
mulligan:
  enabled: yes
replay:
  enabled: no
""",
    )

    config = SimulationConfigLoader().load(path)

    assert config.mulligan_enabled is True
    assert config.save_replays is False


def test_mulligan_enabled_rejects_string(
    tmp_path: Path,
) -> None:
    path = write_config(
        tmp_path / "mulligan-string.yaml",
        """
strategy: balanced
mulligan:
  enabled: "true"
""",
    )

    with pytest.raises(
        ValueError,
        match="mulligan.enabled must be a boolean",
    ):
        SimulationConfigLoader().load(path)


def test_replay_enabled_rejects_string(
    tmp_path: Path,
) -> None:
    path = write_config(
        tmp_path / "replay-string.yaml",
        """
strategy: balanced
replay:
  enabled: "false"
""",
    )

    with pytest.raises(
        ValueError,
        match="replay.enabled must be a boolean",
    ):
        SimulationConfigLoader().load(path)

def test_loader_reads_parallel_workers_alias(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "simulation.yaml"

    config_path.write_text(
        """
strategy: balanced
games: 100
max_turns: 6
parallel_workers: 4
""".strip(),
        encoding="utf-8",
    )

    config = SimulationConfigLoader().load(
        config_path
    )

    assert config.workers == 4


def test_workers_takes_priority_over_parallel_workers(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "simulation.yaml"

    config_path.write_text(
        """
strategy: balanced
games: 100
max_turns: 6
workers: 2
parallel_workers: 4
""".strip(),
        encoding="utf-8",
    )

    config = SimulationConfigLoader().load(
        config_path
    )

    assert config.workers == 2


def test_loader_reads_top_level_save_replays_alias(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "simulation.yaml"

    config_path.write_text(
        """
strategy: balanced
games: 100
max_turns: 6
save_replays: true
""".strip(),
        encoding="utf-8",
    )

    config = SimulationConfigLoader().load(
        config_path
    )

    assert config.save_replays is True


def test_replay_enabled_takes_priority_over_save_replays(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "simulation.yaml"

    config_path.write_text(
        """
strategy: balanced
games: 100
max_turns: 6
save_replays: true
replay:
  enabled: false
""".strip(),
        encoding="utf-8",
    )

    config = SimulationConfigLoader().load(
        config_path
    )

    assert config.save_replays is False


def test_default_project_config_uses_parallel_workers() -> None:
    config = SimulationConfigLoader().load(
        Path("config/simulation/default.yaml")
    )

    assert config.workers == 1


def test_parallel_workers_rejects_non_integer(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "simulation.yaml"

    config_path.write_text(
        """
parallel_workers: four
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="workers must be an integer",
    ):
        SimulationConfigLoader().load(
            config_path
        )


def test_top_level_save_replays_rejects_non_boolean(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "simulation.yaml"

    config_path.write_text(
        """
save_replays: enabled
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="save_replays must be a boolean",
    ):
        SimulationConfigLoader().load(
            config_path
        )

def test_locale_rejects_non_string_value(
    tmp_path: Path,
) -> None:
    path = write_config(
        tmp_path / "locale.yaml",
        "locale: 123\n",
    )

    with pytest.raises(
        ValueError,
        match="locale must be a string",
    ):
        SimulationConfigLoader().load(path)
