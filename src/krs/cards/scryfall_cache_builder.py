from __future__ import annotations

import csv
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from krs.cards.cache import CardCache


JsonObject = dict[str, Any]
UrlOpen = Callable[..., Any]


@dataclass(frozen=True, slots=True)
class ScryfallCacheBuildResult:
    """Result of building one local Scryfall card cache."""

    output_path: Path
    requested_card_count: int
    downloaded_card_count: int
    reused_card_count: int
    card_names: tuple[str, ...]

    def __post_init__(self) -> None:
        counts = (
            self.requested_card_count,
            self.downloaded_card_count,
            self.reused_card_count,
        )

        if any(count < 0 for count in counts):
            raise ValueError(
                "Cache build counts must not be negative."
            )

        if (
            self.downloaded_card_count
            + self.reused_card_count
            != self.requested_card_count
        ):
            raise ValueError(
                "Downloaded and reused card counts must equal "
                "requested_card_count."
            )

        if len(self.card_names) != self.requested_card_count:
            raise ValueError(
                "card_names count must equal requested_card_count."
            )


@dataclass(frozen=True, slots=True)
class ScryfallBulkDataClient:
    """
    Downloads Scryfall default-card Bulk Data.

    Only two HTTP requests are required:
    1. retrieve Bulk Data metadata;
    2. download the default-card dataset.
    """

    metadata_url: str = (
        "https://api.scryfall.com/bulk-data/default-cards"
    )
    user_agent: str = (
        "KinnanResearchSimulator/0.1 "
        "(https://github.com/sumihira/"
        "kinnan-research-simulator)"
    )
    timeout_seconds: float = 120.0
    opener: UrlOpen = field(
        default=urlopen,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        if not self.metadata_url.strip():
            raise ValueError(
                "metadata_url must not be empty."
            )

        if not self.user_agent.strip():
            raise ValueError(
                "user_agent must not be empty."
            )

        if self.timeout_seconds <= 0.0:
            raise ValueError(
                "timeout_seconds must be greater than zero."
            )

    def download_default_cards(
        self,
    ) -> list[JsonObject]:
        """Download and decode the default-card Bulk Data dataset."""
        metadata = self._get_json(
            self.metadata_url,
            description="Scryfall Bulk Data metadata",
        )

        if not isinstance(metadata, Mapping):
            raise ValueError(
                "Scryfall Bulk Data metadata must be a mapping."
            )

        download_uri = metadata.get("download_uri")

        if (
            not isinstance(download_uri, str)
            or not download_uri.strip()
        ):
            raise ValueError(
                "Scryfall Bulk Data metadata requires download_uri."
            )

        raw_cards = self._get_json(
            download_uri,
            description="Scryfall default-card Bulk Data",
        )

        if not isinstance(raw_cards, list):
            raise ValueError(
                "Scryfall default-card Bulk Data root must be a list."
            )

        cards: list[JsonObject] = []

        for index, raw_card in enumerate(raw_cards):
            if not isinstance(raw_card, Mapping):
                raise ValueError(
                    "Scryfall Bulk Data card must be a mapping: "
                    f"index {index}"
                )

            card = dict(raw_card)
            self._validate_card(
                card,
                index=index,
            )
            cards.append(card)

        return cards

    def _get_json(
        self,
        url: str,
        *,
        description: str,
    ) -> object:
        request = Request(
            url=url,
            headers={
                "Accept": "application/json",
                "User-Agent": self.user_agent,
            },
            method="GET",
        )

        try:
            with self.opener(
                request,
                timeout=self.timeout_seconds,
            ) as response:
                payload = response.read()
        except HTTPError as error:
            detail = self._read_http_error_detail(error)

            raise ValueError(
                f"{description} request failed: "
                f"HTTP {error.code}{detail}"
            ) from error
        except URLError as error:
            raise ConnectionError(
                f"Could not retrieve {description}: "
                f"{error.reason}"
            ) from error

        try:
            return json.loads(
                payload.decode("utf-8")
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as error:
            raise ValueError(
                f"{description} returned invalid JSON."
            ) from error

    @staticmethod
    def _validate_card(
        card: Mapping[str, Any],
        *,
        index: int,
    ) -> None:
        for field_name in (
            "id",
            "name",
            "type_line",
        ):
            value = card.get(field_name)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    "Scryfall Bulk Data card requires non-empty "
                    f"{field_name}: index {index}"
                )

    @staticmethod
    def _read_http_error_detail(
        error: HTTPError,
    ) -> str:
        try:
            payload = error.read()
            decoded = json.loads(
                payload.decode("utf-8")
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ):
            return ""

        if not isinstance(decoded, Mapping):
            return ""

        details = decoded.get("details")

        if not isinstance(details, str) or not details.strip():
            return ""

        return f" - {details.strip()}"


@dataclass(frozen=True, slots=True)
class ScryfallCacheBuilder:
    """Builds a deck-specific cache from Scryfall Bulk Data."""

    client: ScryfallBulkDataClient = field(
        default_factory=ScryfallBulkDataClient,
    )

    def build_from_deck(
        self,
        *,
        deck_path: str | Path,
        output_path: str | Path,
        reuse_existing: bool = True,
    ) -> ScryfallCacheBuildResult:
        """
        Build a JSON cache containing every unique card in one deck.

        Existing matching cache entries are reused. If any card is missing,
        the default-card Bulk Data dataset is downloaded once and filtered.
        """
        source_path = Path(deck_path)
        destination_path = Path(output_path)

        card_names = self.read_deck_card_names(
            source_path
        )

        existing_cards = (
            self._load_existing_cards(destination_path)
            if reuse_existing
            else {}
        )

        missing_names = tuple(
            card_name
            for card_name in card_names
            if CardCache.normalize_name(card_name)
            not in existing_cards
        )

        bulk_cards_by_name: dict[str, JsonObject] = {}

        if missing_names:
            bulk_cards_by_name = self._index_bulk_cards(
                self.client.download_default_cards()
            )

        resolved_cards: list[JsonObject] = []
        reused_count = 0
        downloaded_count = 0
        unresolved_names: list[str] = []

        for card_name in card_names:
            normalized_name = CardCache.normalize_name(
                card_name
            )

            existing_card = existing_cards.get(
                normalized_name
            )

            if existing_card is not None:
                resolved_cards.append(existing_card)
                reused_count += 1
                continue

            bulk_card = bulk_cards_by_name.get(
                normalized_name
            )

            if bulk_card is None:
                unresolved_names.append(card_name)
                continue

            resolved_cards.append(bulk_card)
            downloaded_count += 1

        if unresolved_names:
            formatted_names = ", ".join(
                unresolved_names
            )

            raise ValueError(
                "Cards were not found in Scryfall default-card "
                f"Bulk Data: {formatted_names}"
            )

        self._write_cache(
            resolved_cards,
            destination_path,
        )

        return ScryfallCacheBuildResult(
            output_path=destination_path,
            requested_card_count=len(card_names),
            downloaded_card_count=downloaded_count,
            reused_card_count=reused_count,
            card_names=card_names,
        )

    @staticmethod
    def read_deck_card_names(
        deck_path: str | Path,
    ) -> tuple[str, ...]:
        """Read unique card names from a deck CSV."""
        path = Path(deck_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Deck file not found: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Deck path is not a file: {path}"
            )

        with path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            rows = list(csv.reader(file))

        if not rows:
            raise ValueError(
                f"Deck file is empty: {path}"
            )

        start_index = (
            1
            if ScryfallCacheBuilder._is_header(rows[0])
            else 0
        )

        names_by_normalized_name: dict[str, str] = {}

        for row_number, row in enumerate(
            rows[start_index:],
            start=start_index + 1,
        ):
            if not row or all(
                not value.strip()
                for value in row
            ):
                continue

            if len(row) < 2:
                raise ValueError(
                    "Deck row must contain quantity and card name: "
                    f"line {row_number}"
                )

            quantity_text = row[0].strip()
            card_name = row[1].strip()

            try:
                quantity = int(quantity_text)
            except ValueError as error:
                raise ValueError(
                    "Deck quantity must be an integer: "
                    f"line {row_number}"
                ) from error

            if quantity < 1:
                raise ValueError(
                    "Deck quantity must be at least 1: "
                    f"line {row_number}"
                )

            if not card_name:
                raise ValueError(
                    "Deck card name must not be empty: "
                    f"line {row_number}"
                )

            normalized_name = CardCache.normalize_name(
                card_name
            )

            names_by_normalized_name.setdefault(
                normalized_name,
                card_name,
            )

        if not names_by_normalized_name:
            raise ValueError(
                f"Deck contains no cards: {path}"
            )

        return tuple(
            names_by_normalized_name.values()
        )

    @staticmethod
    def _is_header(
        row: list[str],
    ) -> bool:
        if len(row) < 2:
            return False

        first = row[0].strip().casefold()
        second = row[1].strip().casefold()

        return (
            first in {
                "quantity",
                "qty",
                "count",
            }
            and second in {
                "name",
                "card",
                "card_name",
            }
        )

    @staticmethod
    def _index_bulk_cards(
        cards: list[JsonObject],
    ) -> dict[str, JsonObject]:
        cards_by_name: dict[str, JsonObject] = {}

        for card in cards:
            name = card["name"]
            normalized_name = CardCache.normalize_name(
                name
            )

            cards_by_name.setdefault(
                normalized_name,
                card,
            )

        return cards_by_name

    @staticmethod
    def _load_existing_cards(
        path: Path,
    ) -> dict[str, JsonObject]:
        if not path.exists():
            return {}

        if not path.is_file():
            raise ValueError(
                f"Card cache path is not a file: {path}"
            )

        try:
            decoded = json.loads(
                path.read_text(
                    encoding="utf-8",
                )
            )
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Card cache contains invalid JSON: {path}"
            ) from error

        if not isinstance(decoded, list):
            raise ValueError(
                "Existing card cache root must be a list."
            )

        cards_by_name: dict[str, JsonObject] = {}

        for index, card in enumerate(decoded):
            if not isinstance(card, Mapping):
                raise ValueError(
                    "Existing card cache entry must be a mapping: "
                    f"index {index}"
                )

            name = card.get("name")

            if not isinstance(name, str) or not name.strip():
                raise ValueError(
                    "Existing card cache entry requires a name: "
                    f"index {index}"
                )

            cards_by_name.setdefault(
                CardCache.normalize_name(name),
                dict(card),
            )

        return cards_by_name

    @staticmethod
    def _write_cache(
        cards: list[JsonObject],
        output_path: Path,
    ) -> None:
        if output_path.exists() and output_path.is_dir():
            raise ValueError(
                "Card cache output path is a directory: "
                f"{output_path}"
            )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = output_path.with_suffix(
            output_path.suffix + ".tmp"
        )

        temporary_path.write_text(
            json.dumps(
                cards,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        temporary_path.replace(output_path)