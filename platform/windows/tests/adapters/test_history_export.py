"""Tests for history export adapters."""

from datetime import UTC, datetime
from pathlib import Path

from plain_text_fin_calc.adapters.history_export import write_history_csv, write_history_text
from plain_text_fin_calc.domains.calc.history import History, HistoryEntry
from plain_text_fin_calc.domains.calc.text_tape import TextTapeFormat


def test_write_history_csv_exports_entries(tmp_path: Path) -> None:
    """Verify calculator history can be exported as CSV."""
    export_path = tmp_path / "exports" / "history.csv"
    timestamp = datetime(2026, 6, 2, 12, 30, tzinfo=UTC)
    history = History(
        entries=[
            HistoryEntry(
                expression="1 + 1",
                result="2",
                timestamp=timestamp,
            ),
        ],
    )

    write_history_csv(history, export_path)

    assert export_path.read_text(encoding="utf-8").splitlines() == [
        "timestamp,expression,result,rpn_input",
        "2026-06-02T12:30:00+00:00,1 + 1,2,",
    ]


def test_text_tape_groups_days_in_local_time_and_preserves_values(tmp_path):
    def stored_time(day, hour):
        return datetime(2026, 1, day, hour, 15).astimezone(UTC)

    history = History(entries=[
        HistoryEntry("1 / 3", "0.3333333333333333333333333333", stored_time(1, 9)),
        HistoryEntry("20 × 2", "40", stored_time(1, 23)),
        HistoryEntry("40 - 2", "38", stored_time(2, 0)),
    ])
    path = tmp_path / "exports" / "tape.txt"
    write_history_text(history, path, TextTapeFormat())
    assert path.read_bytes() == (
        "2026-01-01\n09:15  1 / 3 = 0.3333333333333333333333333333\n"
        "23:15  20 × 2 = 40\n\n2026-01-02\n00:15  40 - 2 = 38\n"
    ).encode("utf-8")

    write_history_text(History(), path, TextTapeFormat())
    assert path.read_bytes() == b""


def test_text_tape_distinguishes_repeated_hour_at_dst_boundary(tmp_path):
    entries = [
        HistoryEntry("2 + 2", "4", datetime(2026, 11, 1, h, 15, 7, tzinfo=UTC))
        for h in (3, 4, 5, 6, 17)
    ]
    path = tmp_path / "new-york.txt"
    options = TextTapeFormat(
        time_zone="America/New_York", date_format="DD/MM/YYYY",
        twelve_hour=True, seconds=True, utc_offset=True,
    )
    write_history_text(History(entries), path, options)
    assert path.read_text(encoding="utf-8").splitlines() == [
        "31/10/2026", "11:15:07 PM UTC-04:00  2 + 2 = 4", "",
        "01/11/2026", "12:15:07 AM UTC-04:00  2 + 2 = 4",
        "1:15:07 AM UTC-04:00  2 + 2 = 4",
        "1:15:07 AM UTC-05:00  2 + 2 = 4",
        "12:15:07 PM UTC-05:00  2 + 2 = 4",
    ]


def _algebraic_and_rpn_entries() -> list[HistoryEntry]:
    return [
        HistoryEntry(
            "1 / 3", "0.3333333333333333333333333333",
            datetime(2026, 11, 23, 12, 0, 0, tzinfo=UTC),
        ),
        HistoryEntry(
            "3 + 4", "7", datetime(2026, 11, 23, 12, 0, 5, tzinfo=UTC),
            "3 ENTER 4 +",
        ),
    ]


def test_csv_has_rpn_input_as_last_column(tmp_path):
    path = tmp_path / "history.csv"
    write_history_csv(History(_algebraic_and_rpn_entries()), path)
    assert path.read_bytes() == (
        b"timestamp,expression,result,rpn_input\r\n"
        b"2026-11-23T12:00:00+00:00,1 / 3,0.3333333333333333333333333333,\r\n"
        b"2026-11-23T12:00:05+00:00,3 + 4,7,3 ENTER 4 +\r\n"
    )


def test_text_tape_adds_rpn_input_line_under_rpn_entries(tmp_path):
    history = History(_algebraic_and_rpn_entries())
    path = tmp_path / "tape.txt"
    write_history_text(history, path, TextTapeFormat(time_zone="UTC"))
    assert path.read_bytes() == (
        b"2026-11-23\n"
        b"12:00  1 / 3 = 0.3333333333333333333333333333\n"
        b"12:00  3 + 4 = 7\n"
        b"RPN input: 3 ENTER 4 +\n"
    )
    write_history_text(
        history, path, TextTapeFormat(date_headings=False, entry_times=False)
    )
    assert path.read_bytes() == (
        b"1 / 3 = 0.3333333333333333333333333333\n"
        b"3 + 4 = 7\n"
        b"RPN input: 3 ENTER 4 +\n"
    )


def test_text_tape_rpn_entry_starting_a_new_day(tmp_path):
    entries = [
        HistoryEntry("1 + 1", "2", datetime(2026, 11, 22, 23, 59, tzinfo=UTC)),
        HistoryEntry(
            "3 + 4", "7", datetime(2026, 11, 23, 0, 1, tzinfo=UTC), "3 4 +"
        ),
        HistoryEntry("2 * 2", "4", datetime(2026, 11, 23, 0, 2, tzinfo=UTC)),
    ]
    path = tmp_path / "tape.txt"
    write_history_text(History(entries), path, TextTapeFormat(time_zone="UTC"))
    assert path.read_text(encoding="utf-8").splitlines() == [
        "2026-11-22", "23:59  1 + 1 = 2", "",
        "2026-11-23", "00:01  3 + 4 = 7", "RPN input: 3 4 +",
        "00:02  2 * 2 = 4",
    ]
