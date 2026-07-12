from pathlib import Path

import pytest

from krs.ai.strategy_loader import StrategyLoader


def write_strategy(
    path: Path,
    content: str,
) -> Path:
    path.write_text(
        content,
        encoding="utf-8",
    )

    return path


def test_loads_complete_strategy_configuration(
    tmp_path: Path,
) -> None:
    path = write_strategy(
        tmp_path / "combo.yaml",
        """
name: combo

weights:
  mana_value: 0.7
  mana_ability: 2
  untap: 6
  copy: 5
  combo: 10

combo_card_ids:
  - combo-card-id

custom_scores:
  preferred-card-id: 8
""",
    )

    config = StrategyLoader().load(path)

    assert config.name == "combo"
    assert config.mana_value_weight == 0.7
    assert config.mana_ability_bonus == 2.0
    assert config.untap_bonus == 6.0
    assert config.copy_bonus == 5.0
    assert config.combo_bonus == 10.0
    assert config.combo_card_ids == frozenset(
        {
            "combo-card-id",
        }
    )
    assert config.custom_scores[
        "preferred-card-id"
    ] == 8.0


def test_missing_optional_values_use_defaults(
    tmp_path: Path,
) -> None:
    path = write_strategy(
        tmp_path / "minimal.yaml",
        """
name: minimal
""",
    )

    config = StrategyLoader().load(path)

    assert config.mana_value_weight == 1.0
    assert config.mana_ability_bonus == 2.0
    assert config.untap_bonus == 5.0
    assert config.copy_bonus == 4.0
    assert config.combo_bonus == 3.0
    assert config.custom_scores == {}
    assert config.combo_card_ids == frozenset()


def test_loader_creates_evaluator(
    tmp_path: Path,
) -> None:
    path = write_strategy(
        tmp_path / "strategy.yaml",
        """
name: custom

weights:
  mana_value: 2
  untap: 9
""",
    )

    loader = StrategyLoader()
    config = loader.load(path)
    evaluator = loader.create_evaluator(config)

    assert evaluator.mana_value_weight == 2.0
    assert evaluator.untap_bonus == 9.0


def test_missing_file_is_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "missing.yaml"

    with pytest.raises(
        FileNotFoundError,
        match="Strategy file not found",
    ):
        StrategyLoader().load(path)


def test_empty_file_is_rejected(
    tmp_path: Path,
) -> None:
    path = write_strategy(
        tmp_path / "empty.yaml",
        "",
    )

    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        StrategyLoader().load(path)


def test_non_mapping_yaml_is_rejected(
    tmp_path: Path,
) -> None:
    path = write_strategy(
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
        StrategyLoader().load(path)


def test_missing_name_is_rejected(
    tmp_path: Path,
) -> None:
    path = write_strategy(
        tmp_path / "missing-name.yaml",
        """
weights:
  mana_value: 1
""",
    )

    with pytest.raises(
        ValueError,
        match="requires a string name",
    ):
        StrategyLoader().load(path)


def test_invalid_weights_type_is_rejected(
    tmp_path: Path,
) -> None:
    path = write_strategy(
        tmp_path / "invalid.yaml",
        """
name: invalid
weights:
  mana_value: high
""",
    )

    with pytest.raises(
        ValueError,
        match="weights.mana_value must be numeric",
    ):
        StrategyLoader().load(path)


def test_boolean_weight_is_rejected(
    tmp_path: Path,
) -> None:
    path = write_strategy(
        tmp_path / "boolean.yaml",
        """
name: invalid
weights:
  mana_value: true
""",
    )

    with pytest.raises(
        ValueError,
        match="weights.mana_value must be numeric",
    ):
        StrategyLoader().load(path)


def test_combo_card_ids_must_be_list(
    tmp_path: Path,
) -> None:
    path = write_strategy(
        tmp_path / "invalid-combos.yaml",
        """
name: invalid
combo_card_ids: combo-card-id
""",
    )

    with pytest.raises(
        ValueError,
        match="combo_card_ids must be a list",
    ):
        StrategyLoader().load(path)

def test_project_balanced_strategy_can_be_loaded() -> None:
    path = Path(
        "config/strategies/balanced.yaml"
    )

    config = StrategyLoader().load(path)

    assert config.name == "balanced"