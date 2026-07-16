from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import Mock
from urllib.error import HTTPError, URLError

import pytest

from krs.cards.scryfall_cache_builder import (
    ScryfallBulkDataClient,
    ScryfallCacheBuilder,
)


class FakeResponse:
    def __init__(
        self,
        payload: object,
    ) -> None:
        self._payload = json.dumps(
            payload
        ).encode("utf-8")

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        return None

    def read(self) -> bytes:
        return self._payload


def card_payload(
    *,
    card_id: str,
    name: str,
    type_line: str = "Artifact",
) -> dict[str, object]:
    return {
        "id": card_id,
        "oracle_id": f"{card_id}-oracle",
        "name": name,
        "mana_cost": "",
        "cmc": 0,
        "oracle_text": "",
        "type_line": type_line,
        "keywords": [],
    }


def write_deck(
    path: Path,
    *,
    with_header: bool = True,
) -> None:
    rows: list[str] = []

    if with_header:
        rows.append(
            "quantity,name,section"
        )

    rows.extend(
        (
            '1,"Kinnan, Bonder Prodigy",commander',
            "1,Sol Ring,main",
            "2,Forest,main",
        )
    )

    path.write_text(
        "\n".join(rows),
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    "with_header",
    (
        True,
        False,
    ),
)
def test_read_deck_card_names(
    tmp_path: Path,
    with_header: bool,
) -> None:
    deck_path = tmp_path / "deck.csv"

    write_deck(
        deck_path,
        with_header=with_header,
    )

    names = ScryfallCacheBuilder.read_deck_card_names(
        deck_path
    )

    assert names == (
        "Kinnan, Bonder Prodigy",
        "Sol Ring",
        "Forest",
    )


def test_bulk_client_downloads_metadata_and_cards() -> None:
    cards = [
        card_payload(
            card_id="sol-ring-id",
            name="Sol Ring",
        ),
    ]

    opener = Mock(
        side_effect=(
            FakeResponse(
                {
                    "object": "bulk_data",
                    "type": "default_cards",
                    "download_uri": (
                        "https://data.scryfall.io/default-cards.json"
                    ),
                }
            ),
            FakeResponse(cards),
        )
    )

    client = ScryfallBulkDataClient(
        opener=opener,
    )

    result = client.download_default_cards()

    assert result == cards
    assert opener.call_count == 2

    metadata_request = opener.call_args_list[0].args[0]
    data_request = opener.call_args_list[1].args[0]

    assert metadata_request.full_url == (
        "https://api.scryfall.com/bulk-data/default-cards"
    )
    assert data_request.full_url == (
        "https://data.scryfall.io/default-cards.json"
    )


def test_builder_filters_bulk_data_to_deck_cards(
    tmp_path: Path,
) -> None:
    deck_path = tmp_path / "deck.csv"
    output_path = tmp_path / "cards.json"

    write_deck(deck_path)

    client = Mock(
        spec=ScryfallBulkDataClient,
    )
    client.download_default_cards.return_value = [
        card_payload(
            card_id="forest-id",
            name="Forest",
            type_line="Basic Land — Forest",
        ),
        card_payload(
            card_id="unrelated-id",
            name="Unrelated Card",
        ),
        card_payload(
            card_id="kinnan-id",
            name="Kinnan, Bonder Prodigy",
            type_line=(
                "Legendary Creature — Human Druid"
            ),
        ),
        card_payload(
            card_id="sol-ring-id",
            name="Sol Ring",
        ),
    ]

    result = ScryfallCacheBuilder(
        client=client,
    ).build_from_deck(
        deck_path=deck_path,
        output_path=output_path,
    )

    assert result.requested_card_count == 3
    assert result.downloaded_card_count == 3
    assert result.reused_card_count == 0

    decoded = json.loads(
        output_path.read_text(
            encoding="utf-8",
        )
    )

    assert [
        card["name"]
        for card in decoded
    ] == [
        "Kinnan, Bonder Prodigy",
        "Sol Ring",
        "Forest",
    ]


def test_builder_reuses_complete_existing_cache(
    tmp_path: Path,
) -> None:
    deck_path = tmp_path / "deck.csv"
    output_path = tmp_path / "cards.json"

    write_deck(deck_path)

    existing_cards = [
        card_payload(
            card_id="kinnan-id",
            name="Kinnan, Bonder Prodigy",
        ),
        card_payload(
            card_id="sol-ring-id",
            name="Sol Ring",
        ),
        card_payload(
            card_id="forest-id",
            name="Forest",
        ),
    ]

    output_path.write_text(
        json.dumps(existing_cards),
        encoding="utf-8",
    )

    client = Mock(
        spec=ScryfallBulkDataClient,
    )

    result = ScryfallCacheBuilder(
        client=client,
    ).build_from_deck(
        deck_path=deck_path,
        output_path=output_path,
    )

    assert result.downloaded_card_count == 0
    assert result.reused_card_count == 3
    client.download_default_cards.assert_not_called()


def test_builder_downloads_bulk_data_for_missing_cards(
    tmp_path: Path,
) -> None:
    deck_path = tmp_path / "deck.csv"
    output_path = tmp_path / "cards.json"

    write_deck(deck_path)

    output_path.write_text(
        json.dumps(
            [
                card_payload(
                    card_id="sol-ring-id",
                    name="Sol Ring",
                ),
            ]
        ),
        encoding="utf-8",
    )

    client = Mock(
        spec=ScryfallBulkDataClient,
    )
    client.download_default_cards.return_value = [
        card_payload(
            card_id="kinnan-id",
            name="Kinnan, Bonder Prodigy",
        ),
        card_payload(
            card_id="forest-id",
            name="Forest",
        ),
    ]

    result = ScryfallCacheBuilder(
        client=client,
    ).build_from_deck(
        deck_path=deck_path,
        output_path=output_path,
    )

    assert result.downloaded_card_count == 2
    assert result.reused_card_count == 1


def test_builder_reports_missing_bulk_card(
    tmp_path: Path,
) -> None:
    deck_path = tmp_path / "deck.csv"
    output_path = tmp_path / "cards.json"

    write_deck(deck_path)

    client = Mock(
        spec=ScryfallBulkDataClient,
    )
    client.download_default_cards.return_value = [
        card_payload(
            card_id="kinnan-id",
            name="Kinnan, Bonder Prodigy",
        ),
    ]

    with pytest.raises(
        ValueError,
        match=(
            "Cards were not found in Scryfall "
            "default-card Bulk Data"
        ),
    ):
        ScryfallCacheBuilder(
            client=client,
        ).build_from_deck(
            deck_path=deck_path,
            output_path=output_path,
        )


def test_bulk_client_reports_http_error() -> None:
    error = HTTPError(
        url=(
            "https://api.scryfall.com/"
            "bulk-data/default-cards"
        ),
        code=429,
        msg="Too Many Requests",
        hdrs=None,
        fp=io.BytesIO(
            json.dumps(
                {
                    "details": "Rate limited.",
                }
            ).encode("utf-8")
        ),
    )

    opener = Mock(
        side_effect=error,
    )

    with pytest.raises(
        ValueError,
        match="HTTP 429 - Rate limited",
    ):
        ScryfallBulkDataClient(
            opener=opener,
        ).download_default_cards()


def test_bulk_client_reports_connection_error() -> None:
    opener = Mock(
        side_effect=URLError(
            "network unavailable"
        ),
    )

    with pytest.raises(
        ConnectionError,
        match="network unavailable",
    ):
        ScryfallBulkDataClient(
            opener=opener,
        ).download_default_cards()


def test_builder_rejects_invalid_quantity(
    tmp_path: Path,
) -> None:
    deck_path = tmp_path / "deck.csv"

    deck_path.write_text(
        "abc,Sol Ring,main",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="quantity must be an integer",
    ):
        ScryfallCacheBuilder.read_deck_card_names(
            deck_path
        )


def test_builder_rejects_directory_output(
    tmp_path: Path,
) -> None:
    deck_path = tmp_path / "deck.csv"
    output_path = tmp_path / "cards"

    write_deck(deck_path)
    output_path.mkdir()

    client = Mock(
        spec=ScryfallBulkDataClient,
    )
    client.download_default_cards.return_value = [
        card_payload(
            card_id="kinnan-id",
            name="Kinnan, Bonder Prodigy",
        ),
        card_payload(
            card_id="sol-ring-id",
            name="Sol Ring",
        ),
        card_payload(
            card_id="forest-id",
            name="Forest",
        ),
    ]

    with pytest.raises(
        ValueError,
        match="Card cache path is not a file",
    ):
        ScryfallCacheBuilder(
            client=client,
        ).build_from_deck(
            deck_path=deck_path,
            output_path=output_path,
        )

def test_builder_ignores_unrelated_card_without_type_line(
    tmp_path: Path,
) -> None:
    deck_path = tmp_path / "deck.csv"
    output_path = tmp_path / "cards.json"

    write_deck(deck_path)

    unrelated_card = {
        "id": "unrelated-id",
        "name": "Unrelated Special Record",
    }

    client = Mock(
        spec=ScryfallBulkDataClient,
    )
    client.download_default_cards.return_value = [
        unrelated_card,
        card_payload(
            card_id="kinnan-id",
            name="Kinnan, Bonder Prodigy",
            type_line=(
                "Legendary Creature — Human Druid"
            ),
        ),
        card_payload(
            card_id="sol-ring-id",
            name="Sol Ring",
            type_line="Artifact",
        ),
        card_payload(
            card_id="forest-id",
            name="Forest",
            type_line="Basic Land — Forest",
        ),
    ]

    result = ScryfallCacheBuilder(
        client=client,
    ).build_from_deck(
        deck_path=deck_path,
        output_path=output_path,
    )

    assert result.downloaded_card_count == 3

    decoded = json.loads(
        output_path.read_text(
            encoding="utf-8",
        )
    )

    assert [
        card["name"]
        for card in decoded
    ] == [
        "Kinnan, Bonder Prodigy",
        "Sol Ring",
        "Forest",
    ]

def test_builder_rejects_selected_card_without_type_line(
    tmp_path: Path,
) -> None:
    deck_path = tmp_path / "deck.csv"
    output_path = tmp_path / "cards.json"

    write_deck(deck_path)

    client = Mock(
        spec=ScryfallBulkDataClient,
    )
    client.download_default_cards.return_value = [
        {
            "id": "kinnan-id",
            "name": "Kinnan, Bonder Prodigy",
        },
        card_payload(
            card_id="sol-ring-id",
            name="Sol Ring",
            type_line="Artifact",
        ),
        card_payload(
            card_id="forest-id",
            name="Forest",
            type_line="Basic Land — Forest",
        ),
    ]

    with pytest.raises(
        ValueError,
        match=(
            "Selected Scryfall card requires non-empty "
            "type_line: Kinnan, Bonder Prodigy"
        ),
    ):
        ScryfallCacheBuilder(
            client=client,
        ).build_from_deck(
            deck_path=deck_path,
            output_path=output_path,
        )