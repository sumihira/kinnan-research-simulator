from __future__ import annotations

from pathlib import Path

from krs.report.summary_markdown import (
    ExperimentSummaryMarkdownReporter,
)
from krs.simulation.experiment import (
    ExperimentResult,
    SimulationSummary,
)
from krs.simulation.runner import GoldfishRunResult
from krs.simulation.simulation_config import SimulationConfig
from krs.statistics.kinnan_chain import (
    KinnanChainSnapshot,
    KinnanChainStatistics,
)


def create_chain_snapshot(
    *,
    hit_card_ids: tuple[str, ...] = (),
    turn: int | None = None,
    misses: int = 0,
) -> KinnanChainSnapshot:
    statistics = KinnanChainStatistics()

    for card_id in hit_card_ids:
        statistics.record_hit(
            card_id,
            turn=turn,
        )

    for _ in range(misses):
        statistics.record_miss()

    return statistics.snapshot()


def create_game_result(
    chain: KinnanChainSnapshot,
) -> GoldfishRunResult:
    return GoldfishRunResult(
        turns_started=5,
        kinnan_activations=chain.activation_count,
        reached_turn_limit=True,
        game_over=False,
        winner=None,
        kinnan_chain=chain,
    )


def create_experiment_result() -> ExperimentResult:
    config = SimulationConfig(
        strategy_name="kinnan-chain",
        games=4,
        max_turns=6,
        seed=12345,
    )

    game_results = (
        create_game_result(
            KinnanChainSnapshot.empty()
        ),
        create_game_result(
            create_chain_snapshot(
                hit_card_ids=("card-1",),
                turn=2,
            )
        ),
        create_game_result(
            create_chain_snapshot(
                hit_card_ids=(
                    "card-2",
                    "card-3",
                ),
                turn=3,
            )
        ),
        create_game_result(
            create_chain_snapshot(
                hit_card_ids=(
                    "card-4",
                    "card-5",
                    "card-6",
                ),
                turn=4,
                misses=1,
            )
        ),
    )

    return ExperimentResult(
        config=config,
        game_results=game_results,
        summary=SimulationSummary.from_results(
            games_requested=config.games,
            results=game_results,
        ),
    )


def create_empty_experiment_result() -> ExperimentResult:
    config = SimulationConfig(
        games=2,
    )

    return ExperimentResult(
        config=config,
        game_results=(),
        summary=SimulationSummary.from_results(
            games_requested=config.games,
            results=(),
        ),
    )


def test_markdown_contains_kinnan_chain_counts() -> None:
    markdown = (
        ExperimentSummaryMarkdownReporter()
        .to_markdown(create_experiment_result())
    )

    assert "| Kinnan chain games | 4 |" in markdown
    assert "| Kinnan activation games | 3 |" in markdown
    assert (
        "| Kinnan chain-established games | 2 |"
        in markdown
    )
    assert (
        "| Total tracked Kinnan activations | 7 |"
        in markdown
    )
    assert (
        "| Kinnan chain activations | 5 |"
        in markdown
    )


def test_markdown_contains_kinnan_chain_rates() -> None:
    markdown = (
        ExperimentSummaryMarkdownReporter()
        .to_markdown(create_experiment_result())
    )

    assert (
        "| Overall Kinnan chain rate | 50.000% |"
        in markdown
    )
    assert (
        "| Activation-game Kinnan chain rate "
        "| 66.667% |"
        in markdown
    )
    assert (
        "| Activation-based Kinnan chain rate "
        "| 71.429% |"
        in markdown
    )


def test_markdown_contains_kinnan_chain_lengths() -> None:
    markdown = (
        ExperimentSummaryMarkdownReporter()
        .to_markdown(create_experiment_result())
    )

    assert (
        "| Average maximum chain length | 1.500 |"
        in markdown
    )
    assert "| Maximum chain length | 3 |" in markdown


def test_empty_experiment_contains_zero_chain_values() -> None:
    markdown = (
        ExperimentSummaryMarkdownReporter()
        .to_markdown(create_empty_experiment_result())
    )

    assert "| Kinnan chain games | 0 |" in markdown
    assert "| Kinnan activation games | 0 |" in markdown
    assert (
        "| Kinnan chain-established games | 0 |"
        in markdown
    )
    assert (
        "| Overall Kinnan chain rate | 0.000% |"
        in markdown
    )
    assert (
        "| Activation-game Kinnan chain rate "
        "| 0.000% |"
        in markdown
    )
    assert (
        "| Total tracked Kinnan activations | 0 |"
        in markdown
    )
    assert (
        "| Kinnan chain activations | 0 |"
        in markdown
    )
    assert (
        "| Activation-based Kinnan chain rate "
        "| 0.000% |"
        in markdown
    )
    assert (
        "| Average maximum chain length | 0.000 |"
        in markdown
    )
    assert "| Maximum chain length | 0 |" in markdown


def test_existing_markdown_sections_are_unchanged() -> None:
    markdown = (
        ExperimentSummaryMarkdownReporter()
        .to_markdown(create_experiment_result())
    )

    assert "## Simulation Configuration" in markdown
    assert "## Summary" in markdown
    assert "## Individual Games" in markdown
    assert markdown.count("\n\n---\n\n") == 3
    assert markdown.count("| Metric | Value |") == 2


def test_existing_summary_metrics_remain_present() -> None:
    markdown = (
        ExperimentSummaryMarkdownReporter()
        .to_markdown(create_experiment_result())
    )

    assert "| Games requested | 4 |" in markdown
    assert "| Games completed | 4 |" in markdown
    assert "| Wins | 0 |" in markdown
    assert "| Non-wins | 4 |" in markdown
    assert "| Win rate | 0.000% |" in markdown
    assert "| Turn-limit games | 4 |" in markdown
    assert "| Total turns started | 20 |" in markdown
    assert "| Average turns started | 5.000 |" in markdown
    assert "| Total Kinnan activations | 7 |" in markdown
    assert "| Average Kinnan activations | 1.750 |" in markdown
    assert "| Fastest win turn | N/A |" in markdown


def test_written_markdown_contains_chain_statistics(
    tmp_path: Path,
) -> None:
    result = create_experiment_result()
    output_path = tmp_path / "summary.md"

    ExperimentSummaryMarkdownReporter().write(
        result,
        output_path,
    )

    markdown = output_path.read_text(
        encoding="utf-8",
    )

    assert (
        "| Kinnan chain-established games | 2 |"
        in markdown
    )
    assert (
        "| Overall Kinnan chain rate | 50.000% |"
        in markdown
    )
    assert "| Maximum chain length | 3 |" in markdown


def test_reporter_does_not_modify_chain_summary() -> None:
    result = create_experiment_result()
    original_chain = result.summary.kinnan_chain

    reporter = ExperimentSummaryMarkdownReporter()

    reporter.to_markdown(result)

    assert result.summary.kinnan_chain is original_chain