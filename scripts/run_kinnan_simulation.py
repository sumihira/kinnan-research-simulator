from __future__ import annotations

import argparse
import sys
from pathlib import Path

from krs.simulation.file_run_service import (
    FileSimulationRunResult,
    FileSimulationRunService,
    SimulationConfigOverrides,
)


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
        help=(
            "Override the number of games from the YAML configuration."
        ),
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=None,
        help=(
            "Override the maximum turn count from the YAML configuration."
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help=(
            "Override the simulation seed. "
            "Omit this option to retain the YAML value."
        ),
    )
    parser.add_argument(
        "--random-seed",
        action="store_true",
        help=(
            "Override the YAML seed with null for non-deterministic runs."
        ),
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help=(
            "Override the worker count from the YAML configuration."
        ),
    )

    return parser


def create_config_overrides(
    arguments: argparse.Namespace,
) -> SimulationConfigOverrides:
    """Create validated runtime overrides from parsed CLI arguments."""
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


def print_result(
    result: FileSimulationRunResult,
) -> None:
    summary = result.experiment.summary
    chain = summary.kinnan_chain
    audit = result.audit
    config = result.config

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


def main() -> int:
    parser = create_parser()
    arguments = parser.parse_args()

    try:
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