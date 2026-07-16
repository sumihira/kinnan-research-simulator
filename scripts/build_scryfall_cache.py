from __future__ import annotations

import argparse
import sys
from pathlib import Path

from krs.cards.scryfall_cache_builder import (
    ScryfallCacheBuilder,
)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a local Scryfall card cache from Bulk Data."
        ),
    )

    parser.add_argument(
        "--deck",
        type=Path,
        default=Path("data/decks/kinnan.csv"),
        help=(
            "Deck CSV path. "
            "Default: data/decks/kinnan.csv"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "data/cards/kinnan_cards.json"
        ),
        help=(
            "Output JSON path. "
            "Default: data/cards/kinnan_cards.json"
        ),
    )
    parser.add_argument(
        "--no-reuse",
        action="store_true",
        help=(
            "Ignore an existing deck cache and rebuild it "
            "from Scryfall Bulk Data."
        ),
    )

    return parser


def main() -> int:
    arguments = create_parser().parse_args()

    print("Building Scryfall cache from Bulk Data...")
    print(
        "The first execution downloads the default-card dataset."
    )

    try:
        result = ScryfallCacheBuilder().build_from_deck(
            deck_path=arguments.deck,
            output_path=arguments.output,
            reuse_existing=not arguments.no_reuse,
        )
    except (
        ConnectionError,
        FileNotFoundError,
        ValueError,
    ) as error:
        print(
            f"Cache build failed: {error}",
            file=sys.stderr,
        )
        return 1

    print()
    print("Scryfall cache created")
    print("=" * 56)
    print(
        f"Output               : {result.output_path}"
    )
    print(
        "Unique deck cards    : "
        f"{result.requested_card_count:,}"
    )
    print(
        "Bulk-data additions  : "
        f"{result.downloaded_card_count:,}"
    )
    print(
        "Reused               : "
        f"{result.reused_card_count:,}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())