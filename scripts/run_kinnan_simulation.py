from __future__ import annotations

import argparse
import sys
from pathlib import Path

from krs.cards.card_config_loader import CardConfigLoader
from krs.decks.implementation_audit import (
    DeckImplementationAuditor,
)
from krs.simulation.file_run_service import (
    FileSimulationRunResult,
    FileSimulationRunService,
    SimulationConfigOverrides,
)
from krs.simulation.preflight import (
    SimulationPreflightResult,
    SimulationPreflightValidator,
)
from krs.simulation.simulation_factory import SimulationFactory


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a file-based Kinnan Monte Carlo simulation "
            "and write all supported reports."
        ),
    )

    parser.add_argument(
        "--simulation-config",
        type=Path,
        default=Path(
            "config/simulation/default.yaml"
        ),
        help=(
            "Simulation configuration YAML path. "
            "Default: config/simulation/default.yaml"
        ),
    )
    parser.add_argument(
        "--deck",
        type=Path,
        default=Path(
            "data/decks/kinnan.csv"
        ),
        help=(
            "Commander deck CSV path. "
            "Default: data/decks/kinnan.csv"
        ),
    )
    parser.add_argument(
        "--card-cache",
        type=Path,
        required=True,
        help="Local Scryfall JSON card-cache path.",
    )
    parser.add_argument(
        "--card-config-directory",
        type=Path,
        default=Path("config/cards"),
        help=(
            "Executable card configuration directory. "
            "Default: config/cards"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "reports/kinnan_latest"
        ),
        help=(
            "Report output directory. "
            "Default: reports/kinnan_latest"
        ),
    )
    parser.add_argument(
        "--deck-name",
        default=None,
        help="Optional deck-name override.",
    )
    parser.add_argument(
        "--player-name",
        default="Player",
        help="Goldfish player name.",
    )
    parser.add_argument(
        "--games",
        type=int,
        default=None,
        help="Override the number of games.",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=None,
        help="Override the maximum turn count.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Override the simulation seed.",
    )
    parser.add_argument(
        "--random-seed",
        action="store_true",
        help="Replace the YAML seed with a random seed.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Override the worker count.",
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help=(
            "Validate the deck without running "
            "the Monte Carlo simulation."
        ),
    )

    return parser


def create_config_overrides(
    arguments: argparse.Namespace,
) -> SimulationConfigOverrides:
    """Create runtime overrides from parsed CLI arguments."""
    if arguments.seed is not None and arguments.random_seed:
        raise ValueError(
            "--seed and --random-seed cannot be used together."
        )

    seed_is_overridden = (
        arguments.seed is not None
        or arguments.random_seed
    )

    return SimulationConfigOverrides(
        games=arguments.games,
        max_turns=arguments.max_turns,
        seed=arguments.seed,
        seed_is_overridden=seed_is_overridden,
        workers=arguments.workers,
    )


def print_preflight(
    result: SimulationPreflightResult,
) -> None:
    """Print one preflight result."""
    status = (
        "READY"
        if result.ready
        else "BLOCKED"
    )

    print()
    print("Kinnan Simulation Preflight")
    print("=" * 64)
    print(f"Status                       : {status}")
    print(f"Deck                         : {result.deck_name}")
    print(f"Total cards                  : {result.total_cards:,}")
    print(f"Main-deck cards              : {result.main_deck_cards:,}")
    print(f"Unique cards                 : {result.unique_cards:,}")
    print(
        "Configured unique cards      : "
        f"{result.configured_unique_cards:,}"
    )
    print(
        "Oracle-only unique cards     : "
        f"{result.oracle_only_unique_cards:,}"
    )
    print(f"Land cards                   : {result.land_cards:,}")
    print(f"Implemented mana sources     : {result.mana_source_cards:,}")
    print(f"Blue mana sources            : {result.blue_source_cards:,}")
    print(f"Green mana sources           : {result.green_source_cards:,}")

    if result.issues:
        print("-" * 64)

    for issue in result.issues:
        level = (
            "ERROR"
            if issue.blocking
            else "WARNING"
        )

        print(
            f"[{level}] {issue.code}: {issue.message}"
        )


def print_result(
    result: FileSimulationRunResult,
) -> None:
    summary = result.experiment.summary
    chain = summary.kinnan_chain
    audit = result.audit
    config = result.config

    print_preflight(
        result.preflight
    )

    print()
    print("Kinnan Research Simulator")
    print("=" * 64)
    print(f"Deck                         : {result.deck.name}")
    print(f"Games requested              : {summary.games_requested:,}")
    print(f"Games completed              : {summary.games_completed:,}")
    print(f"Maximum turns                : {config.max_turns:,}")
    print(
        "Seed                         : "
        f"{config.seed if config.seed is not None else 'random'}"
    )
    print(f"Workers                      : {config.workers:,}")
    print(f"Implementation rate          : {audit.implementation_rate:.2%}")
    print(f"Configured unique cards      : {audit.configured_unique_cards:,}")
    print(f"Oracle-only unique cards     : {audit.oracle_only_unique_cards:,}")
    print("-" * 64)
    print(f"Kinnan activation games      : {chain.games_with_activation:,}")
    print(f"Kinnan chain games           : {chain.games_with_chain:,}")
    print(f"Overall chain rate           : {chain.overall_chain_rate:.2%}")
    print(
        "Activation-game chain rate  : "
        f"{chain.activation_game_chain_rate:.2%}"
    )
    print(f"Total Kinnan activations     : {chain.total_activations:,}")
    print(f"Chain activations            : {chain.chain_activations:,}")
    print(
        "Activation-based chain rate : "
        f"{chain.activation_chain_rate:.2%}"
    )
    print(
        "Average maximum chain       : "
        f"{chain.average_longest_chain:.3f}"
    )
    print(f"Maximum chain                : {chain.max_chain:,}")
    print("-" * 64)
    print(
        "Summary Markdown            : "
        f"{result.report_paths.summary_markdown_path}"
    )
    print(
        "Experiment JSON             : "
        f"{result.report_paths.json_path}"
    )
    print(
        "Experiment HTML             : "
        f"{result.report_paths.html_path}"
    )
    print(
        "Experiment Excel            : "
        f"{result.report_paths.excel_path}"
    )
    print(
        "Implementation audit        : "
        f"{result.audit_markdown_path}"
    )


def run_preflight_only(
    arguments: argparse.Namespace,
) -> int:
    """Load and validate the deck without running Monte Carlo."""
    factory = SimulationFactory()

    _, deck = factory.load_config_and_deck(
        simulation_config_path=(
            arguments.simulation_config
        ),
        deck_path=arguments.deck,
        card_cache_path=arguments.card_cache,
        card_config_directory=(
            arguments.card_config_directory
        ),
        deck_name=arguments.deck_name,
    )

    audit = DeckImplementationAuditor(
        CardConfigLoader(
            arguments.card_config_directory
        )
    ).audit(deck)

    preflight = SimulationPreflightValidator().validate(
        deck=deck,
        audit=audit,
    )

    print_preflight(preflight)

    return 0 if preflight.ready else 1


def main() -> int:
    parser = create_parser()
    arguments = parser.parse_args()

    try:
        if arguments.preflight_only:
            return run_preflight_only(
                arguments
            )

        overrides = create_config_overrides(
            arguments
        )

        result = FileSimulationRunService().run(
            simulation_config_path=(
                arguments.simulation_config
            ),
            deck_path=arguments.deck,
            card_cache_path=arguments.card_cache,
            card_config_directory=(
                arguments.card_config_directory
            ),
            output_directory=arguments.output,
            deck_name=arguments.deck_name,
            player_name=arguments.player_name,
            config_overrides=overrides,
        )
    except (
        FileNotFoundError,
        ValueError,
        IndexError,
    ) as error:
        print(
            f"Simulation failed: {error}",
            file=sys.stderr,
        )
        return 1

    print_result(result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())