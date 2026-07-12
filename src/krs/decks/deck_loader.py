from __future__ import annotations

import csv
from pathlib import Path

from krs.cards.card_loader import CardLoader
from krs.decks.deck import Deck


class DeckLoader:
    """
    Loads a Commander deck from CSV.

    Required columns:
    - quantity
    - name
    - section
    """

    REQUIRED_COLUMNS = {
        "quantity",
        "name",
        "section",
    }

    VALID_SECTIONS = {
        "commander",
        "main",
    }

    def __init__(
        self,
        card_loader: CardLoader,
    ) -> None:
        self._card_loader = card_loader

    def load_csv(
        self,
        path: str | Path,
        *,
        deck_name: str | None = None,
    ) -> Deck:
        csv_path = Path(path)

        if not csv_path.exists():
            raise FileNotFoundError(
                f"Deck file not found: {csv_path}"
            )

        if not csv_path.is_file():
            raise ValueError(
                f"Deck path is not a file: {csv_path}"
            )

        with csv_path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.DictReader(file)

            if reader.fieldnames is None:
                raise ValueError(
                    "Deck CSV must contain a header."
                )

            normalized_columns = {
                column.strip().casefold()
                for column in reader.fieldnames
            }

            missing_columns = (
                self.REQUIRED_COLUMNS
                - normalized_columns
            )

            if missing_columns:
                missing = ", ".join(
                    sorted(missing_columns)
                )

                raise ValueError(
                    "Deck CSV is missing required columns: "
                    f"{missing}"
                )

            commander = None
            main_cards = []

            for row_number, row in enumerate(
                reader,
                start=2,
            ):
                quantity = self._parse_quantity(
                    row.get("quantity"),
                    row_number=row_number,
                )

                card_name = self._parse_name(
                    row.get("name"),
                    row_number=row_number,
                )

                section = self._parse_section(
                    row.get("section"),
                    row_number=row_number,
                )

                card = self._card_loader.load_by_name(
                    card_name
                )

                if section == "commander":
                    if quantity != 1:
                        raise ValueError(
                            "Commander quantity must be 1 "
                            f"at row {row_number}."
                        )

                    if commander is not None:
                        raise ValueError(
                            "Deck CSV must contain exactly "
                            "one commander."
                        )

                    commander = card
                    continue

                main_cards.extend(
                    card
                    for _ in range(quantity)
                )

        if commander is None:
            raise ValueError(
                "Deck CSV must contain exactly one commander."
            )

        resolved_name = (
            deck_name.strip()
            if deck_name is not None
            else csv_path.stem
        )

        if not resolved_name:
            raise ValueError(
                "Deck name must not be empty."
            )

        return Deck(
            name=resolved_name,
            commander=commander,
            cards=main_cards,
        )

    @staticmethod
    def _parse_quantity(
        raw_value: str | None,
        *,
        row_number: int,
    ) -> int:
        if raw_value is None:
            raise ValueError(
                f"Missing quantity at row {row_number}."
            )

        try:
            quantity = int(raw_value.strip())
        except ValueError as error:
            raise ValueError(
                "Quantity must be an integer "
                f"at row {row_number}."
            ) from error

        if quantity <= 0:
            raise ValueError(
                "Quantity must be greater than zero "
                f"at row {row_number}."
            )

        return quantity

    @staticmethod
    def _parse_name(
        raw_value: str | None,
        *,
        row_number: int,
    ) -> str:
        if raw_value is None:
            raise ValueError(
                f"Missing card name at row {row_number}."
            )

        name = raw_value.strip()

        if not name:
            raise ValueError(
                f"Card name must not be empty at row {row_number}."
            )

        return name

    @classmethod
    def _parse_section(
        cls,
        raw_value: str | None,
        *,
        row_number: int,
    ) -> str:
        if raw_value is None:
            raise ValueError(
                f"Missing section at row {row_number}."
            )

        section = raw_value.strip().casefold()

        if section not in cls.VALID_SECTIONS:
            raise ValueError(
                f"Invalid deck section at row {row_number}: "
                f"{section}"
            )

        return section