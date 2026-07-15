from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from krs.replay.replay import Replay
from krs.replay.replay_event import ReplayEvent
from krs.replay.replay_html import ReplayHtmlReporter
from krs.replay.replay_statistics import ReplayCount


def create_event(
    *,
    turn: int = 1,
    phase: str = "main",
    action: str = "draw",
    description: str = "Player 0 executed draw.",
) -> ReplayEvent:
    return ReplayEvent(
        turn=turn,
        phase=phase,
        action=action,
        description=description,
    )


def create_replay() -> Replay:
    replay = Replay()

    replay.add(
        create_event(
            turn=1,
            phase="untap",
            action="game_start",
            description=(
                "Started game 42 with 1 player(s)."
            ),
        )
    )
    replay.add(
        create_event(
            turn=1,
            phase="draw",
            action="draw",
        )
    )
    replay.add(
        create_event(
            turn=1,
            phase="main",
            action="cast_spell",
            description=(
                "Player 0 executed cast_spell."
            ),
        )
    )
    replay.add(
        create_event(
            turn=2,
            phase="main",
            action="activate_kinnan",
            description=(
                "Player 0 executed activate_kinnan."
            ),
        )
    )
    replay.add(
        create_event(
            turn=3,
            phase="main",
            action="game_end",
            description=(
                "Game ended. Winner: Player."
            ),
        )
    )

    return replay


def test_to_html_returns_complete_document() -> None:
    html = ReplayHtmlReporter().to_html(
        create_replay()
    )

    assert html.startswith("<!DOCTYPE html>")
    assert '<html lang="en">' in html
    assert '<meta charset="utf-8">' in html
    assert "</body>" in html
    assert html.endswith("</html>\n")


def test_to_html_contains_default_title() -> None:
    html = ReplayHtmlReporter().to_html(
        create_replay()
    )

    assert (
        "<title>Kinnan Research Simulator Replay</title>"
        in html
    )
    assert (
        "<h1>Kinnan Research Simulator Replay</h1>"
        in html
    )


def test_to_html_contains_custom_title() -> None:
    html = ReplayHtmlReporter(
        title="Goldfish Replay 001",
    ).to_html(create_replay())

    assert "<title>Goldfish Replay 001</title>" in html
    assert "<h1>Goldfish Replay 001</h1>" in html


def test_to_html_contains_all_sections() -> None:
    html = ReplayHtmlReporter().to_html(
        create_replay()
    )

    assert 'id="summary-heading"' in html
    assert 'id="action-counts"' in html
    assert 'id="phase-counts"' in html
    assert 'id="timeline-heading"' in html


def test_to_html_contains_summary_values() -> None:
    html = ReplayHtmlReporter().to_html(
        create_replay()
    )

    assert "5 events across 3 turns" in html
    assert "Events" in html
    assert "Turns represented" in html
    assert "Maximum turn" in html
    assert "Game starts" in html
    assert "Game ends" in html
    assert "Kinnan activations" in html


def test_to_html_contains_kinnan_activation_count() -> None:
    html = ReplayHtmlReporter().to_html(
        create_replay()
    )

    label_position = html.index(
        "Kinnan activations"
    )
    value_position = html.index(
        ">1</strong>",
        label_position,
    )

    assert label_position < value_position


def test_to_html_contains_action_counts() -> None:
    html = ReplayHtmlReporter().to_html(
        create_replay()
    )

    assert ">activate_kinnan<" in html
    assert ">cast_spell<" in html
    assert ">draw<" in html
    assert ">game_end<" in html
    assert ">game_start<" in html


def test_to_html_contains_phase_counts() -> None:
    html = ReplayHtmlReporter().to_html(
        create_replay()
    )

    assert ">untap<" in html
    assert ">draw<" in html
    assert ">main<" in html


def test_to_html_contains_timeline_headers() -> None:
    html = ReplayHtmlReporter().to_html(
        create_replay()
    )

    assert '<th scope="col">#</th>' in html
    assert '<th scope="col">Turn</th>' in html
    assert '<th scope="col">Phase</th>' in html
    assert '<th scope="col">Action</th>' in html
    assert '<th scope="col">Description</th>' in html


def test_to_html_contains_all_event_descriptions() -> None:
    html = ReplayHtmlReporter().to_html(
        create_replay()
    )

    assert (
        "Started game 42 with 1 player(s)."
        in html
    )
    assert "Player 0 executed draw." in html
    assert "Player 0 executed cast_spell." in html
    assert (
        "Player 0 executed activate_kinnan."
        in html
    )
    assert "Game ended. Winner: Player." in html


def test_timeline_preserves_event_order() -> None:
    html = ReplayHtmlReporter().to_html(
        create_replay()
    )

    game_start_position = html.index(
        "<code>game_start</code>"
    )
    draw_position = html.index(
        "<code>draw</code>"
    )
    cast_position = html.index(
        "<code>cast_spell</code>"
    )
    kinnan_position = html.index(
        "<code>activate_kinnan</code>"
    )
    game_end_position = html.index(
        "<code>game_end</code>"
    )

    assert game_start_position < draw_position
    assert draw_position < cast_position
    assert cast_position < kinnan_position
    assert kinnan_position < game_end_position


def test_timeline_contains_event_indexes() -> None:
    html = ReplayHtmlReporter().to_html(
        create_replay()
    )

    for index in range(1, 6):
        assert (
            f'<td class="numeric">{index}</td>'
            in html
        )


def test_timeline_contains_data_attributes() -> None:
    html = ReplayHtmlReporter().to_html(
        create_replay()
    )

    assert (
        '<tr data-turn="1" data-action="game_start">'
        in html
    )
    assert (
        '<tr data-turn="2" '
        'data-action="activate_kinnan">'
        in html
    )
    assert (
        '<tr data-turn="3" data-action="game_end">'
        in html
    )


def test_to_html_supports_empty_replay() -> None:
    html = ReplayHtmlReporter().to_html(
        Replay()
    )

    assert "0 events across 0 turns" in html
    assert "N/A" in html
    assert (
        "No Replay events were recorded."
        in html
    )
    assert html.count(
        "No count data is available."
    ) == 2


def test_to_html_uses_singular_words() -> None:
    replay = Replay()
    replay.add(
        create_event()
    )

    html = ReplayHtmlReporter().to_html(
        replay
    )

    assert "1 event across 1 turn" in html
    assert "1 events" not in html
    assert "1 turns" not in html


def test_to_html_preserves_unicode() -> None:
    replay = Replay()
    replay.add(
        create_event(
            action="キナン起動",
            description="キナンの能力を起動しました。",
        )
    )

    html = ReplayHtmlReporter().to_html(
        replay
    )

    assert "キナン起動" in html
    assert "キナンの能力を起動しました。" in html


def test_title_is_html_escaped() -> None:
    html = ReplayHtmlReporter(
        title="<script>alert('x')</script>",
    ).to_html(Replay())

    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_event_values_are_html_escaped() -> None:
    replay = Replay()
    replay.add(
        create_event(
            phase="<main>",
            action='cast_"spell"&',
            description=(
                "<script>alert('x')</script> & result"
            ),
        )
    )

    html = ReplayHtmlReporter().to_html(
        replay
    )

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "&amp; result" in html
    assert "&lt;main&gt;" in html
    assert "cast_&quot;spell&quot;&amp;" in html


def test_render_count_row_returns_expected_html() -> None:
    html = ReplayHtmlReporter._render_count_row(
        ReplayCount(
            name="draw",
            count=12,
        )
    )

    assert "<td>draw</td>" in html
    assert (
        '<td class="numeric">12</td>'
        in html
    )


def test_render_count_row_escapes_name() -> None:
    html = ReplayHtmlReporter._render_count_row(
        ReplayCount(
            name="<draw>",
            count=1,
        )
    )

    assert "<draw>" not in html
    assert "&lt;draw&gt;" in html


def test_write_creates_html_file(
    tmp_path: Path,
) -> None:
    replay = create_replay()
    reporter = ReplayHtmlReporter()
    output_path = tmp_path / "replay.html"

    returned_path = reporter.write(
        replay,
        output_path,
    )

    assert returned_path == output_path
    assert output_path.is_file()
    assert output_path.read_text(
        encoding="utf-8",
    ) == reporter.to_html(replay)


def test_write_creates_parent_directories(
    tmp_path: Path,
) -> None:
    output_path = (
        tmp_path
        / "replays"
        / "game-001"
        / "replay.html"
    )

    ReplayHtmlReporter().write(
        create_replay(),
        output_path,
    )

    assert output_path.is_file()


def test_write_uses_utf_8(
    tmp_path: Path,
) -> None:
    replay = Replay()
    replay.add(
        create_event(
            description="キナンを起動しました。",
        )
    )

    output_path = tmp_path / "replay.html"

    ReplayHtmlReporter().write(
        replay,
        output_path,
    )

    assert "キナンを起動しました。" in (
        output_path.read_text(
            encoding="utf-8",
        )
    )


def test_write_overwrites_existing_file(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "replay.html"
    output_path.write_text(
        "old content",
        encoding="utf-8",
    )

    ReplayHtmlReporter().write(
        create_replay(),
        output_path,
    )

    content = output_path.read_text(
        encoding="utf-8",
    )

    assert content != "old content"
    assert content.startswith("<!DOCTYPE html>")


@pytest.mark.parametrize(
    "filename",
    (
        "replay.html",
        "replay.htm",
        "REPLAY.HTML",
        "REPLAY.HTM",
    ),
)
def test_write_accepts_html_extensions(
    tmp_path: Path,
    filename: str,
) -> None:
    output_path = tmp_path / filename

    ReplayHtmlReporter().write(
        create_replay(),
        output_path,
    )

    assert output_path.is_file()


@pytest.mark.parametrize(
    "filename",
    (
        "replay.txt",
        "replay.json",
        "replay",
        "replay.html.txt",
    ),
)
def test_write_rejects_invalid_extension(
    tmp_path: Path,
    filename: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Replay HTML path must use "
            "the .html or .htm extension."
        ),
    ):
        ReplayHtmlReporter().write(
            create_replay(),
            tmp_path / filename,
        )


def test_write_rejects_directory_path(
    tmp_path: Path,
) -> None:
    output_directory = (
        tmp_path
        / "replay.html"
    )
    output_directory.mkdir()

    with pytest.raises(
        ValueError,
        match="Replay HTML path is a directory",
    ):
        ReplayHtmlReporter().write(
            create_replay(),
            output_directory,
        )


@pytest.mark.parametrize(
    "title",
    (
        "",
        " ",
        "\t",
        "\n",
    ),
)
def test_reporter_rejects_empty_title(
    title: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="title must not be empty.",
    ):
        ReplayHtmlReporter(
            title=title,
        )


def test_reporter_is_immutable() -> None:
    reporter = ReplayHtmlReporter()

    with pytest.raises(
        FrozenInstanceError,
    ):
        reporter.title = "Changed"  # type: ignore[misc]


def test_to_html_does_not_modify_replay() -> None:
    replay = create_replay()
    original_events = replay.events
    original_count = replay.event_count

    ReplayHtmlReporter().to_html(replay)

    assert replay.events == original_events
    assert replay.event_count == original_count


def test_write_does_not_modify_replay(
    tmp_path: Path,
) -> None:
    replay = create_replay()
    original_events = replay.events
    original_count = replay.event_count

    ReplayHtmlReporter().write(
        replay,
        tmp_path / "replay.html",
    )

    assert replay.events == original_events
    assert replay.event_count == original_count