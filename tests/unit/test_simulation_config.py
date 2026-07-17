from __future__ import annotations

import pytest

from krs.simulation.simulation_config import SimulationConfig


def test_simulation_config_defaults() -> None:
    config = SimulationConfig()

    assert config.locale == "ja"
    assert config.strategy_name == "balanced"
    assert config.games == 1_000
    assert config.max_turns == 6
    assert config.seed is None
    assert config.mulligan_enabled is True
    assert config.save_replays is False
    assert config.workers == 1


def test_strategy_name_is_normalized() -> None:
    config = SimulationConfig(
        strategy_name=" COMBO ",
    )

    assert config.strategy_name == "combo"


@pytest.mark.parametrize(
    "games",
    [
        0,
        -1,
        -100,
    ],
)
def test_games_must_be_positive(
    games: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="Number of games must be greater than zero",
    ):
        SimulationConfig(
            games=games,
        )


@pytest.mark.parametrize(
    "max_turns",
    [
        0,
        -1,
        -10,
    ],
)
def test_max_turns_must_be_positive(
    max_turns: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="Maximum turns must be greater than zero",
    ):
        SimulationConfig(
            max_turns=max_turns,
        )


@pytest.mark.parametrize(
    "workers",
    [
        0,
        -1,
        -10,
    ],
)
def test_workers_must_be_positive(
    workers: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="Number of workers must be greater than zero",
    ):
        SimulationConfig(
            workers=workers,
        )


def test_strategy_name_must_not_be_empty() -> None:
    with pytest.raises(
        ValueError,
        match="Strategy name must not be empty",
    ):
        SimulationConfig(
            strategy_name="",
        )


def test_simulation_config_accepts_multiple_workers() -> None:
    config = SimulationConfig(
        workers=4,
    )

    assert config.workers == 4


def test_simulation_config_is_immutable() -> None:
    config = SimulationConfig()

    with pytest.raises(AttributeError):
        config.games = 2_000  # type: ignore[misc]

def test_locale_is_normalized() -> None:
    config = SimulationConfig(locale=" EN ")

    assert config.locale == "en"


def test_unsupported_locale_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="locale must be one of: en, ja",
    ):
        SimulationConfig(locale="fr")
