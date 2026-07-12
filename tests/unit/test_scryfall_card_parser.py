import pytest

from krs.cards.parser import ScryfallCardParser


def create_raw_card() -> dict[str, object]:
    return {
        "id": "kinnan-scryfall-id",
        "name": "Kinnan, Bonder Prodigy",
        "mana_cost": "{G}{U}",
        "cmc": 2.0,
        "type_line": (
            "Legendary Creature — Human Druid"
        ),
        "oracle_text": (
            "Whenever you tap a nonland permanent "
            "for mana, add one mana."
        ),
        "power": "2",
        "toughness": "2",
        "keywords": [],
    }


def test_parses_scryfall_card() -> None:
    card = ScryfallCardParser().parse(
        create_raw_card()
    )

    assert card.id == "kinnan-scryfall-id"
    assert card.name == "Kinnan, Bonder Prodigy"
    assert card.mana_cost == "{G}{U}"
    assert card.mana_value == 2
    assert card.power == "2"
    assert card.toughness == "2"


def test_parses_keywords() -> None:
    raw = create_raw_card()
    raw["keywords"] = [
        "Flying",
        "Haste",
    ]

    card = ScryfallCardParser().parse(raw)

    assert card.keywords == (
        "Flying",
        "Haste",
    )


def test_missing_optional_fields_use_defaults() -> None:
    raw = create_raw_card()
    raw.pop("power")
    raw.pop("toughness")
    raw.pop("oracle_text")
    raw.pop("mana_cost")
    raw.pop("keywords")

    card = ScryfallCardParser().parse(raw)

    assert card.power is None
    assert card.toughness is None
    assert card.oracle_text == ""
    assert card.mana_cost == ""
    assert card.keywords == ()


def test_combines_double_faced_card_text() -> None:
    raw = {
        "id": "double-faced-id",
        "name": "Front // Back",
        "cmc": 3,
        "type_line": (
            "Creature — Beast // Land — Forest"
        ),
        "card_faces": [
            {
                "mana_cost": "{2}{G}",
                "oracle_text": "Front ability.",
            },
            {
                "mana_cost": "",
                "oracle_text": "Back ability.",
            },
        ],
        "keywords": [],
    }

    card = ScryfallCardParser().parse(raw)

    assert card.mana_cost == "{2}{G} // "
    assert card.oracle_text == (
        "Front ability.\n//\nBack ability."
    )


@pytest.mark.parametrize(
    "field_name",
    [
        "id",
        "name",
        "type_line",
    ],
)
def test_required_string_fields_are_validated(
    field_name: str,
) -> None:
    raw = create_raw_card()
    raw[field_name] = ""

    with pytest.raises(
        ValueError,
        match=rf"requires non-empty {field_name}",
    ):
        ScryfallCardParser().parse(raw)


def test_invalid_mana_value_is_rejected() -> None:
    raw = create_raw_card()
    raw["cmc"] = "two"

    with pytest.raises(
        ValueError,
        match="cmc must be numeric",
    ):
        ScryfallCardParser().parse(raw)