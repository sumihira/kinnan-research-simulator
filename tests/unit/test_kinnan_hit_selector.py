from krs.ai.kinnan_hit_selector import KinnanHitSelector
from krs.cards.card import Card
from krs.ai.evaluator import CardEvaluator


def create_card(
    *,
    card_id: str,
    name: str,
    mana_value: int,
    type_line: str,
    oracle_text: str = "",
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost="",
        mana_value=mana_value,
        oracle_text=oracle_text,
        type_line=type_line,
    )


def test_selects_highest_mana_value_valid_hit() -> None:
    selector = KinnanHitSelector()

    cards = [
        create_card(
            card_id="small-creature",
            name="Small Creature",
            mana_value=2,
            type_line="Creature — Beast",
        ),
        create_card(
            card_id="large-creature",
            name="Large Creature",
            mana_value=7,
            type_line="Creature — Whale",
        ),
        create_card(
            card_id="medium-creature",
            name="Medium Creature",
            mana_value=4,
            type_line="Creature — Elemental",
        ),
    ]

    selected = selector.select(cards)

    assert selected is cards[1]


def test_ignores_human_creatures() -> None:
    selector = KinnanHitSelector()

    human = create_card(
        card_id="human",
        name="Large Human",
        mana_value=10,
        type_line="Creature — Human Wizard",
    )
    beast = create_card(
        card_id="beast",
        name="Small Beast",
        mana_value=2,
        type_line="Creature — Beast",
    )

    selected = selector.select(
        [
            human,
            beast,
        ]
    )

    assert selected is beast


def test_ignores_noncreature_cards() -> None:
    selector = KinnanHitSelector()

    artifact = create_card(
        card_id="artifact",
        name="Large Artifact",
        mana_value=10,
        type_line="Artifact",
    )
    creature = create_card(
        card_id="creature",
        name="Creature",
        mana_value=3,
        type_line="Creature — Beast",
    )

    selected = selector.select(
        [
            artifact,
            creature,
        ]
    )

    assert selected is creature


def test_returns_none_when_no_valid_hit_exists() -> None:
    selector = KinnanHitSelector()

    cards = [
        create_card(
            card_id="artifact",
            name="Artifact",
            mana_value=4,
            type_line="Artifact",
        ),
        create_card(
            card_id="human",
            name="Human",
            mana_value=6,
            type_line="Creature — Human",
        ),
        create_card(
            card_id="land",
            name="Forest",
            mana_value=0,
            type_line="Basic Land — Forest",
        ),
    ]

    assert selector.select(cards) is None


def test_returns_none_for_empty_reveal() -> None:
    selector = KinnanHitSelector()

    assert selector.select([]) is None


def test_tied_mana_values_keep_reveal_order() -> None:
    selector = KinnanHitSelector()

    first = create_card(
        card_id="first",
        name="First Creature",
        mana_value=6,
        type_line="Creature — Beast",
    )
    second = create_card(
        card_id="second",
        name="Second Creature",
        mana_value=6,
        type_line="Creature — Whale",
    )

    selected = selector.select(
        [
            first,
            second,
        ]
    )

    assert selected is first


def test_does_not_modify_revealed_cards() -> None:
    selector = KinnanHitSelector()

    cards = [
        create_card(
            card_id="first",
            name="First",
            mana_value=2,
            type_line="Creature — Beast",
        ),
        create_card(
            card_id="second",
            name="Second",
            mana_value=5,
            type_line="Creature — Beast",
        ),
    ]
    original = list(cards)

    selector.select(cards)

    assert cards == original

def test_selector_can_prefer_lower_mana_value_with_custom_score() -> None:
    evaluator = CardEvaluator(
        custom_scores={
            "preferred-id": 10.0,
        }
    )
    selector = KinnanHitSelector(
        evaluator=evaluator,
    )

    high_mana = create_card(
        card_id="high-id",
        name="High Mana Creature",
        mana_value=8,
        type_line="Creature — Beast",
    )
    preferred = create_card(
        card_id="preferred-id",
        name="Preferred Creature",
        mana_value=2,
        type_line="Creature — Beast",
    )

    selected = selector.select(
        [
            high_mana,
            preferred,
        ]
    )

    assert selected is preferred

def test_selector_can_prefer_untap_creature() -> None:
    evaluator = CardEvaluator(
        untap_bonus=5.0,
    )
    selector = KinnanHitSelector(
        evaluator=evaluator,
    )

    normal_creature = create_card(
        card_id="normal-id",
        name="Normal Creature",
        mana_value=7,
        type_line="Creature — Beast",
    )
    untap_creature = create_card(
        card_id="untap-id",
        name="Untap Creature",
        mana_value=4,
        type_line="Creature — Whale",
        oracle_text=(
            "When this creature enters, "
            "untap up to seven lands."
        ),
    )

    selected = selector.select(
        [
            normal_creature,
            untap_creature,
        ]
    )

    # Normal: 7
    # Untap: 4 + 5
    assert selected is untap_creature