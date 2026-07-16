from __future__ import annotations

import argparse

import pytest

from scripts.run_kinnan_simulation import (
    create_config_overrides,
)


def create_arguments(
    *,
    games: int | None = None,
    max_turns: int | None = None,
    seed: int | None = None,
    random_seed: bool = False,
    workers: int | None = None,
) -> argparse.Namespace:
    return argparse.Namespace(
        games=games,
        max_turns=max_turns,
        seed=seed,
        random_seed=random_seed,
        workers=workers,
    )


def test_create_config_overrides() -> None:
    overrides = create_config_overrides(
        create_arguments(
            games=100,
            max_turns=8,
            seed=12345,
            workers=2,
        )
    )

    assert overrides.games == 100
    assert overrides.max_turns == 8
    assert overrides.seed == 12345
    assert overrides.seed_is_overridden is True
    assert overrides.workers == 2


def test_create_config_overrides_without_values() -> None:
    overrides = create_config_overrides(
        create_arguments()
    )

    assert overrides.has_overrides is False


def test_random_seed_clears_yaml_seed() -> None:
    overrides = create_config_overrides(
        create_arguments(
            random_seed=True,
        )
    )

    assert overrides.seed is None
    assert overrides.seed_is_overridden is True


def test_seed_and_random_seed_are_mutually_exclusive() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "--seed and --random-seed "
            "cannot be used together"
        ),
    ):
        create_config_overrides(
            create_arguments(
                seed=12345,
                random_seed=True,
            )
        )