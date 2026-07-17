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
from krs.report.localization import ReportLocalizer
from krs.simulation.simulation_config_loader import (
    SimulationConfigLoader,
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
        "--locale",
        choices=("ja", "en"),
        default=None,
        help=(
            "Override report locale. "
            "Supported values: ja, en."
        ),
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
        locale=arguments.locale,
        games=arguments.games,
        max_turns=arguments.max_turns,
        seed=arguments.seed,
        seed_is_overridden=seed_is_overridden,
        workers=arguments.workers,
    )


def print_preflight(
    result: SimulationPreflightResult,
    *,
    locale: str = "ja",
) -> None:
    """Print one localized preflight result."""
    localizer = ReportLocalizer(locale)

    status = localizer.text(
        ja=(
            "実行可能"
            if result.ready
            else "実行不可"
        ),
        en=(
            "READY"
            if result.ready
            else "BLOCKED"
        ),
    )

    print()
    print(
        localizer.text(
            ja="キナン・シミュレーション事前検証",
            en="Kinnan Simulation Preflight",
        )
    )
    print("=" * 64)

    print(
        f"{localizer.text(ja='状態', en='Status'):<29}: "
        f"{status}"
    )
    print(
        f"{localizer.text(ja='デッキ', en='Deck'):<29}: "
        f"{result.deck_name}"
    )
    print(
        f"{localizer.text(ja='総カード枚数', en='Total cards'):<29}: "
        f"{result.total_cards:,}"
    )
    print(
        f"{localizer.text(ja='メインデッキ枚数', en='Main-deck cards'):<29}: "
        f"{result.main_deck_cards:,}"
    )
    print(
        f"{localizer.text(ja='ユニークカード数', en='Unique cards'):<29}: "
        f"{result.unique_cards:,}"
    )
    print(
        f"{localizer.text(ja='設定済みユニークカード数', en='Configured unique cards'):<29}: "
        f"{result.configured_unique_cards:,}"
    )
    print(
        f"{localizer.text(ja='Oracle情報のみのカード数', en='Oracle-only unique cards'):<29}: "
        f"{result.oracle_only_unique_cards:,}"
    )
    print(
        f"{localizer.text(ja='土地カード数', en='Land cards'):<29}: "
        f"{result.land_cards:,}"
    )
    print(
        f"{localizer.text(ja='実装済みマナ源', en='Implemented mana sources'):<29}: "
        f"{result.mana_source_cards:,}"
    )
    print(
        f"{localizer.text(ja='青マナ源', en='Blue mana sources'):<29}: "
        f"{result.blue_source_cards:,}"
    )
    print(
        f"{localizer.text(ja='緑マナ源', en='Green mana sources'):<29}: "
        f"{result.green_source_cards:,}"
    )

    if result.issues:
        print("-" * 64)

    for issue in result.issues:
        level = localizer.text(
            ja=(
                "エラー"
                if issue.blocking
                else "警告"
            ),
            en=(
                "ERROR"
                if issue.blocking
                else "WARNING"
            ),
        )

        print(
            f"[{level}] {issue.code}: {issue.message}"
        )


def print_result(
    result: FileSimulationRunResult,
) -> None:
    """Print one localized simulation result."""
    summary = result.experiment.summary
    chain = summary.kinnan_chain
    audit = result.audit
    config = result.config
    localizer = ReportLocalizer(config.locale)

    print_preflight(
        result.preflight,
        locale=config.locale,
    )

    def print_metric(
        *,
        ja: str,
        en: str,
        value: object,
    ) -> None:
        label = localizer.text(
            ja=ja,
            en=en,
        )
        print(f"{label:<29}: {value}")

    print()
    print(
        localizer.text(
            ja="キナン・リサーチ・シミュレーター",
            en="Kinnan Research Simulator",
        )
    )
    print("=" * 64)

    print_metric(
        ja="デッキ",
        en="Deck",
        value=result.deck.name,
    )
    print_metric(
        ja="要求ゲーム数",
        en="Games requested",
        value=f"{summary.games_requested:,}",
    )
    print_metric(
        ja="完了ゲーム数",
        en="Games completed",
        value=f"{summary.games_completed:,}",
    )
    print_metric(
        ja="最大ターン数",
        en="Maximum turns",
        value=f"{config.max_turns:,}",
    )
    print_metric(
        ja="乱数シード",
        en="Seed",
        value=localizer.random_seed(config.seed),
    )
    print_metric(
        ja="並列ワーカー数",
        en="Workers",
        value=f"{config.workers:,}",
    )
    print_metric(
        ja="カード実装率",
        en="Implementation rate",
        value=f"{audit.implementation_rate:.2%}",
    )
    print_metric(
        ja="設定済みユニークカード数",
        en="Configured unique cards",
        value=f"{audit.configured_unique_cards:,}",
    )
    print_metric(
        ja="Oracle情報のみのカード数",
        en="Oracle-only unique cards",
        value=f"{audit.oracle_only_unique_cards:,}",
    )

    print("-" * 64)

    print_metric(
        ja="キナン起動ゲーム数",
        en="Kinnan activation games",
        value=f"{chain.games_with_activation:,}",
    )
    print_metric(
        ja="連続起動成立ゲーム数",
        en="Kinnan chain games",
        value=f"{chain.games_with_chain:,}",
    )
    print_metric(
        ja="全ゲーム基準の連続起動率",
        en="Overall chain rate",
        value=f"{chain.overall_chain_rate:.2%}",
    )
    print_metric(
        ja="起動ゲーム基準の連続起動率",
        en="Activation-game chain rate",
        value=f"{chain.activation_game_chain_rate:.2%}",
    )
    print_metric(
        ja="キナン総起動回数",
        en="Total Kinnan activations",
        value=f"{chain.total_activations:,}",
    )
    print_metric(
        ja="連続起動回数",
        en="Chain activations",
        value=f"{chain.chain_activations:,}",
    )
    print_metric(
        ja="起動回数基準の連続起動率",
        en="Activation-based chain rate",
        value=f"{chain.activation_chain_rate:.2%}",
    )
    print_metric(
        ja="平均最大連続起動数",
        en="Average maximum chain",
        value=f"{chain.average_longest_chain:.3f}",
    )
    print_metric(
        ja="最大連続起動数",
        en="Maximum chain",
        value=f"{chain.max_chain:,}",
    )

    print("-" * 64)

    print_metric(
        ja="概要Markdown",
        en="Summary Markdown",
        value=result.report_paths.summary_markdown_path,
    )
    print_metric(
        ja="実験JSON",
        en="Experiment JSON",
        value=result.report_paths.json_path,
    )
    print_metric(
        ja="実験HTML",
        en="Experiment HTML",
        value=result.report_paths.html_path,
    )
    print_metric(
        ja="実験Excel",
        en="Experiment Excel",
        value=result.report_paths.excel_path,
    )
    print_metric(
        ja="実装状況監査",
        en="Implementation audit",
        value=result.audit_markdown_path,
    )


def run_preflight_only(
    arguments: argparse.Namespace,
) -> int:
    """Load and validate the deck without running Monte Carlo."""
    factory = SimulationFactory()

    config, deck = factory.load_config_and_deck(
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

    locale = (
       arguments.locale
        if arguments.locale is not None
        else config.locale
    )

    print_preflight(
        preflight,
        locale=locale,
    )

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