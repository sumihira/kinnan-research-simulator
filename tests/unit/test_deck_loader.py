from pathlib import Path

import pytest

from krs.cards.card import Card
from krs.cards.card_loader import CardLoader
from krs.decks.deck_loader import DeckLoader


def create_card(
    card_id: str,
    name: str,
    type_line: str,
) -> Card:
    return Card(
        id=card_id,
        name=name,
        mana_cost="",
        mana_value=0,
        oracle_text="",
        type_line=type_line,
    )


def create_loader() -> DeckLoader:
    cards = {
        "Kinnan, Bonder Prodigy": create_card(
            "kinnan-id",
            "Kinnan, Bonder Prodigy",
            "Legendary Creature — Human Druid",
        ),
        "Sol Ring": create_card(
            "sol-ring-id",
            "Sol Ring",
            "Artifact",
        ),
        "Forest": create_card(
            "forest-id",
            "Forest",
            "Basic Land — Forest",
        ),
    }

    return DeckLoader(
        CardLoader(cards)
    )


def write_csv(
    path: Path,
    content: str,
) -> Path:
    path.write_text(
        content,
        encoding="utf-8",
    )

    return path


def test_loads_commander_and_main_deck(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path / "kinnan.csv",
        '''quantity,name,section
1,"Kinnan, Bonder Prodigy",commander
1,Sol Ring,main
2,Forest,main
''',
    )

    deck = create_loader().load_csv(path)

    assert deck.name == "kinnan"
    assert deck.commander.name == (
        "Kinnan, Bonder Prodigy"
    )
    assert [
        card.name
        for card in deck.cards
    ] == [
        "Sol Ring",
        "Forest",
        "Forest",
    ]


def test_custom_deck_name_is_used(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path / "deck.csv",
        '''quantity,name,section
1,"Kinnan, Bonder Prodigy",commander
1,Sol Ring,main
''',
    )

    deck = create_loader().load_csv(
        path,
        deck_name="Current List",
    )

    assert deck.name == "Current List"


def test_card_names_are_resolved_case_insensitively(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path / "deck.csv",
        '''quantity,name,section
1,"kinnan, bonder prodigy",commander
1,sol ring,main
''',
    )

    deck = create_loader().load_csv(path)

    assert deck.commander.id == "kinnan-id"
    assert deck.cards[0].id == "sol-ring-id"


def test_missing_file_is_rejected(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        FileNotFoundError,
        match="Deck file not found",
    ):
        create_loader().load_csv(
            tmp_path / "missing.csv"
        )


def test_missing_required_column_is_rejected(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path / "invalid.csv",
        '''quantity,name
1,"Kinnan, Bonder Prodigy"
''',
    )

    with pytest.raises(
        ValueError,
        match="missing required columns: section",
    ):
        create_loader().load_csv(path)


def test_missing_commander_is_rejected(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path / "invalid.csv",
        '''quantity,name,section
1,Sol Ring,main
''',
    )

    with pytest.raises(
        ValueError,
        match="exactly one commander",
    ):
        create_loader().load_csv(path)


def test_multiple_commanders_are_rejected(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path / "invalid.csv",
        '''quantity,name,section
1,"Kinnan, Bonder Prodigy",commander
1,"Kinnan, Bonder Prodigy",commander
''',
    )

    with pytest.raises(
        ValueError,
        match="exactly one commander",
    ):
        create_loader().load_csv(path)


def test_commander_quantity_must_be_one(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path / "invalid.csv",
        '''quantity,name,section
2,"Kinnan, Bonder Prodigy",commander
''',
    )

    with pytest.raises(
        ValueError,
        match="Commander quantity must be 1",
    ):
        create_loader().load_csv(path)


@pytest.mark.parametrize(
    "quantity",
    [
        "0",
        "-1",
        "abc",
    ],
)
def test_invalid_quantity_is_rejected(
    tmp_path: Path,
    quantity: str,
) -> None:
    path = write_csv(
        tmp_path / "invalid.csv",
        f'''quantity,name,section
1,"Kinnan, Bonder Prodigy",commander
{quantity},Sol Ring,main
''',
    )

    with pytest.raises(ValueError):
        create_loader().load_csv(path)


def test_unknown_card_is_rejected(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path / "invalid.csv",
        '''quantity,name,section
1,"Kinnan, Bonder Prodigy",commander
1,Unknown Card,main
''',
    )

    with pytest.raises(
        ValueError,
        match="Card not found: Unknown Card",
    ):
        create_loader().load_csv(path)


def test_invalid_section_is_rejected(
    tmp_path: Path,
) -> None:
    path = write_csv(
        tmp_path / "invalid.csv",
        '''quantity,name,section
1,"Kinnan, Bonder Prodigy",commander
1,Sol Ring,sideboard
''',
    )

    with pytest.raises(
        ValueError,
        match="Invalid deck section",
    ):
        create_loader().load_csv(path)