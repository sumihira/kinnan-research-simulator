from __future__ import annotations

from krs.ai.card_evaluator import CardEvaluator
from krs.cards.card import Card


def create_card(
    *,
    name: str,
    type_line: str,
) -> Card:
    return Card(
        id=name.casefold().replace(" ", "-"),
        name=name,
        mana_cost="",
        mana_value=0,
        oracle_text="",
        type_line=type_line,
    )


def test_non_human_creature_receives_high_score() -> None:
    card = create_card(
        name="Beast",
        type_line="Creature — Beast",
    )

    score = CardEvaluator().evaluate(card)

    assert score.custom_score == 100.0
    assert score.total == 100.0


def test_human_creature_receives_zero_score() -> None:
    card = create_card(
        name="Human",
        type_line="Creature — Human Wizard",
    )

    score = CardEvaluator().evaluate(card)

    assert score.custom_score == 0.0
    assert score.total == 0.0


def test_non_creature_receives_zero_score() -> None:
    card = create_card(
        name="Sol Ring",
        type_line="Artifact",
    )

    score = CardEvaluator().evaluate(card)

    assert score.custom_score == 0.0
    assert score.total == 0.0


def test_artifact_creature_is_evaluated_as_creature() -> None:
    card = create_card(
        name="Artifact Beast",
        type_line="Artifact Creature — Beast",
    )

    score = CardEvaluator().evaluate(card)

    assert score.custom_score == 100.0
    assert score.total == 100.0


def test_artifact_human_creature_is_not_kinnan_hit() -> None:
    card = create_card(
        name="Artifact Human",
        type_line="Artifact Creature — Human Artificer",
    )

    score = CardEvaluator().evaluate(card)

    assert score.custom_score == 0.0
    assert score.total == 0.0


def test_creature_without_subtype_is_non_human() -> None:
    card = create_card(
        name="Subtype-less Creature",
        type_line="Creature",
    )

    score = CardEvaluator().evaluate(card)

    assert score.custom_score == 100.0
    assert score.total == 100.0