import pytest

from krs.ai.evaluator import CardEvaluator
from krs.ai.strategy_config import StrategyConfig


def test_strategy_config_can_be_created() -> None:
    config = StrategyConfig(
        name="balanced",
        mana_value_weight=1.0,
        untap_bonus=5.0,
    )

    assert config.name == "balanced"
    assert config.mana_value_weight == 1.0
    assert config.untap_bonus == 5.0


def test_strategy_name_must_not_be_empty() -> None:
    with pytest.raises(
        ValueError,
        match="Strategy name must not be empty",
    ):
        StrategyConfig(name="")


def test_custom_scores_are_copied_and_immutable() -> None:
    source = {
        "card-id": 5.0,
    }

    config = StrategyConfig(
        name="test",
        custom_scores=source,
    )

    source["card-id"] = 99.0

    assert config.custom_scores["card-id"] == 5.0

    with pytest.raises(TypeError):
        config.custom_scores["new-id"] = 1.0  # type: ignore[index]


def test_combo_ids_are_stored_as_frozenset() -> None:
    config = StrategyConfig(
        name="combo",
        combo_card_ids=frozenset(
            {
                "card-1",
                "card-2",
            }
        ),
    )

    assert config.combo_card_ids == frozenset(
        {
            "card-1",
            "card-2",
        }
    )


def test_empty_combo_id_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Combo card IDs must not be empty",
    ):
        StrategyConfig(
            name="invalid",
            combo_card_ids=frozenset(
                {
                    "",
                }
            ),
        )


def test_card_evaluator_can_be_created_from_strategy() -> None:
    config = StrategyConfig(
        name="combo",
        mana_value_weight=0.5,
        mana_ability_bonus=3.0,
        untap_bonus=7.0,
        copy_bonus=6.0,
        combo_bonus=10.0,
        custom_scores={
            "preferred-id": 4.0,
        },
        combo_card_ids=frozenset(
            {
                "combo-id",
            }
        ),
    )

    evaluator = CardEvaluator.from_strategy(config)

    assert evaluator.mana_value_weight == 0.5
    assert evaluator.mana_ability_bonus == 3.0
    assert evaluator.untap_bonus == 7.0
    assert evaluator.copy_bonus == 6.0
    assert evaluator.combo_bonus == 10.0
    assert evaluator.custom_scores["preferred-id"] == 4.0
    assert "combo-id" in evaluator.combo_card_ids