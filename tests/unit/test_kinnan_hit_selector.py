from krs.ai.kinnan_hit_selector import KinnanHitSelector
from krs.cards.card import Card


def create_card(
    *,
    card_id: str,
    name: str,
    mana_value: int,
    type_line: str,
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost="",
        mana_value=mana_value,
        oracle_text="",
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