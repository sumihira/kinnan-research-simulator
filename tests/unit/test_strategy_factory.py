from pathlib import Path

import pytest

from krs.ai.strategy_factory import StrategyFactory


def write_strategy(
    directory: Path,
    *,
    filename: str,
    configured_name: str,
    custom_score: float = 0.0,
) -> Path:
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = directory / filename

    path.write_text(
        f"""
name: {configured_name}

weights:
  mana_value: 1.0
  mana_ability: 2.0
  untap: 5.0
  copy: 4.0
  combo: 3.0

custom_scores:
  preferred-id: {custom_score}

combo_card_ids: []
""",
        encoding="utf-8",
    )

    return path


def test_factory_loads_strategy_by_name(
    tmp_path: Path,
) -> None:
    strategy_directory = tmp_path / "strategies"

    write_strategy(
        strategy_directory,
        filename="balanced.yaml",
        configured_name="balanced",
    )

    factory = StrategyFactory(
        strategy_directory=strategy_directory
    )

    config = factory.load_config("balanced")

    assert config.name == "balanced"


def test_factory_normalizes_strategy_name(
    tmp_path: Path,
) -> None:
    strategy_directory = tmp_path / "strategies"

    write_strategy(
        strategy_directory,
        filename="balanced.yaml",
        configured_name="balanced",
    )

    factory = StrategyFactory(
        strategy_directory=strategy_directory
    )

    config = factory.load_config(
        "  BALANCED  "
    )

    assert config.name == "balanced"


def test_factory_creates_selector(
    tmp_path: Path,
) -> None:
    strategy_directory = tmp_path / "strategies"

    write_strategy(
        strategy_directory,
        filename="combo.yaml",
        configured_name="combo",
        custom_score=10.0,
    )

    factory = StrategyFactory(
        strategy_directory=strategy_directory
    )

    selector = factory.create_kinnan_hit_selector(
        "combo"
    )

    assert selector is not None


def test_factory_rejects_missing_strategy(
    tmp_path: Path,
) -> None:
    factory = StrategyFactory(
        strategy_directory=tmp_path
    )

    with pytest.raises(
        FileNotFoundError,
        match="Strategy file not found",
    ):
        factory.load_config("missing")


@pytest.mark.parametrize(
    "strategy_name",
    [
        "",
        "   ",
    ],
)
def test_factory_rejects_empty_name(
    strategy_name: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="Strategy name must not be empty",
    ):
        StrategyFactory().load_config(
            strategy_name
        )


@pytest.mark.parametrize(
    "strategy_name",
    [
        "../balanced",
        "balanced.yaml",
        "combo/other",
        "shang-chi",
    ],
)
def test_factory_rejects_unsafe_strategy_name(
    strategy_name: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="may only contain",
    ):
        StrategyFactory().load_config(
            strategy_name
        )


def test_factory_rejects_name_mismatch(
    tmp_path: Path,
) -> None:
    strategy_directory = tmp_path / "strategies"

    write_strategy(
        strategy_directory,
        filename="balanced.yaml",
        configured_name="combo",
    )

    factory = StrategyFactory(
        strategy_directory=strategy_directory
    )

    with pytest.raises(
        ValueError,
        match="do not match",
    ):
        factory.load_config("balanced")