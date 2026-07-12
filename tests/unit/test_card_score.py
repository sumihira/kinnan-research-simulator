from krs.abilities.mana_ability import ManaAbility
from krs.ai.evaluator import CardEvaluator
from krs.cards.card import Card
from krs.mana.mana import Mana
from krs.ai.card_score import CardScore

def create_card(
    *,
    card_id: str = "card-id",
    name: str = "Test Card",
    mana_value: int = 1,
    oracle_text: str = "",
    mana_abilities: tuple[ManaAbility, ...] = (),
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost="",
        mana_value=mana_value,
        oracle_text=oracle_text,
        type_line="Creature — Beast",
        mana_abilities=mana_abilities,
    )


def test_evaluator_scores_mana_value() -> None:
    evaluator = CardEvaluator()
    card = create_card(
        mana_value=7,
    )

    score = evaluator.evaluate(card)

    assert score.mana_value_score == 7.0
    assert score.total == 7.0


def test_evaluator_applies_mana_value_weight() -> None:
    evaluator = CardEvaluator(
        mana_value_weight=2.0,
    )
    card = create_card(
        mana_value=4,
    )

    score = evaluator.evaluate(card)

    assert score.mana_value_score == 8.0


def test_new_card_score_defaults_to_zero() -> None:
    score = CardScore()

    assert score.mana_value_score == 0.0
    assert score.mana_ability_score == 0.0
    assert score.untap_score == 0.0
    assert score.copy_score == 0.0
    assert score.combo_score == 0.0
    assert score.custom_score == 0.0
    assert score.total == 0.0


def test_total_sums_all_components() -> None:
    score = CardScore(
        mana_value_score=7.0,
        mana_ability_score=2.0,
        untap_score=5.0,
        copy_score=4.0,
        combo_score=3.0,
        custom_score=1.5,
    )

    assert score.total == 22.5

def test_evaluator_adds_mana_ability_bonus() -> None:
    evaluator = CardEvaluator(
        mana_ability_bonus=3.0,
    )

    card = create_card(
        mana_abilities=(
            ManaAbility(
                produced_mana={
                    Mana.GREEN: 1,
                }
            ),
        ),
    )

    score = evaluator.evaluate(card)

    assert score.mana_ability_score == 3.0


def test_evaluator_adds_untap_bonus() -> None:
    evaluator = CardEvaluator(
        untap_bonus=5.0,
    )

    card = create_card(
        oracle_text=(
            "When this creature enters, "
            "untap up to seven lands."
        ),
    )

    score = evaluator.evaluate(card)

    assert score.untap_score == 5.0


def test_evaluator_adds_copy_bonus() -> None:
    evaluator = CardEvaluator(
        copy_bonus=4.0,
    )

    card = create_card(
        oracle_text=(
            "You may have this creature enter "
            "as a copy of another creature."
        ),
    )

    score = evaluator.evaluate(card)

    assert score.copy_score == 4.0


def test_evaluator_adds_combo_bonus() -> None:
    evaluator = CardEvaluator(
        combo_bonus=6.0,
        combo_card_ids=frozenset(
            {
                "combo-card-id",
            }
        ),
    )

    card = create_card(
        card_id="combo-card-id",
    )

    score = evaluator.evaluate(card)

    assert score.combo_score == 6.0


def test_evaluator_adds_custom_score() -> None:
    evaluator = CardEvaluator(
        custom_scores={
            "preferred-card-id": 10.0,
        }
    )

    card = create_card(
        card_id="preferred-card-id",
    )

    score = evaluator.evaluate(card)

    assert score.custom_score == 10.0


def test_evaluator_combines_multiple_score_sources() -> None:
    evaluator = CardEvaluator(
        mana_value_weight=1.0,
        mana_ability_bonus=2.0,
        untap_bonus=5.0,
        combo_bonus=3.0,
        custom_scores={
            "great-whale-id": 1.0,
        },
        combo_card_ids=frozenset(
            {
                "great-whale-id",
            }
        ),
    )

    card = create_card(
        card_id="great-whale-id",
        name="Great Whale",
        mana_value=7,
        oracle_text=(
            "When Great Whale enters, "
            "untap up to seven lands."
        ),
        mana_abilities=(
            ManaAbility(
                produced_mana={
                    Mana.BLUE: 1,
                }
            ),
        ),
    )

    score = evaluator.evaluate(card)

    assert score.mana_value_score == 7.0
    assert score.mana_ability_score == 2.0
    assert score.untap_score == 5.0
    assert score.combo_score == 3.0
    assert score.custom_score == 1.0
    assert score.total == 18.0