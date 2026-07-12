import json
from pathlib import Path

import pytest

from krs.cards.cache import CardCache


def write_cache(
    path: Path,
    cards: object,
) -> Path:
    path.write_text(
        json.dumps(
            cards,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return path


def create_raw_card(
    *,
    card_id: str,
    name: str,
) -> dict[str, object]:
    return {
        "id": card_id,
        "name": name,
        "mana_cost": "{1}",
        "cmc": 1,
        "type_line": "Artifact",
        "oracle_text": "",
        "keywords": [],
    }


def test_loads_cards_from_json(
    tmp_path: Path,
) -> None:
    path = write_cache(
        tmp_path / "cards.json",
        [
            create_raw_card(
                card_id="sol-ring-id",
                name="Sol Ring",
            ),
            create_raw_card(
                card_id="basalt-id",
                name="Basalt Monolith",
            ),
        ],
    )

    cache = CardCache.load_json(path)

    assert len(cache) == 2
    assert cache.get_by_name(
        "Sol Ring"
    ).id == "sol-ring-id"


def test_name_lookup_is_case_insensitive(
    tmp_path: Path,
) -> None:
    path = write_cache(
        tmp_path / "cards.json",
        [
            create_raw_card(
                card_id="sol-ring-id",
                name="Sol Ring",
            ),
        ],
    )

    cache = CardCache.load_json(path)

    assert cache.get_by_name(
        "  sol   ring "
    ).id == "sol-ring-id"


def test_gets_card_by_id(
    tmp_path: Path,
) -> None:
    path = write_cache(
        tmp_path / "cards.json",
        [
            create_raw_card(
                card_id="sol-ring-id",
                name="Sol Ring",
            ),
        ],
    )

    cache = CardCache.load_json(path)

    assert cache.get_by_id(
        "sol-ring-id"
    ).name == "Sol Ring"


def test_missing_cache_file_is_rejected(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        FileNotFoundError,
        match="Card cache file not found",
    ):
        CardCache.load_json(
            tmp_path / "missing.json"
        )


def test_invalid_json_is_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(
        "{invalid",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="contains invalid JSON",
    ):
        CardCache.load_json(path)


def test_non_list_root_is_rejected(
    tmp_path: Path,
) -> None:
    path = write_cache(
        tmp_path / "cards.json",
        {
            "cards": [],
        },
    )

    with pytest.raises(
        ValueError,
        match="root must be a list",
    ):
        CardCache.load_json(path)


def test_duplicate_card_id_is_rejected(
    tmp_path: Path,
) -> None:
    path = write_cache(
        tmp_path / "cards.json",
        [
            create_raw_card(
                card_id="duplicate-id",
                name="First",
            ),
            create_raw_card(
                card_id="duplicate-id",
                name="Second",
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match="Duplicate Scryfall card ID",
    ):
        CardCache.load_json(path)


def test_missing_card_is_rejected(
    tmp_path: Path,
) -> None:
    path = write_cache(
        tmp_path / "cards.json",
        [],
    )

    cache = CardCache.load_json(path)

    with pytest.raises(
        ValueError,
        match="Card not found in cache",
    ):
        cache.get_by_name("Unknown Card")