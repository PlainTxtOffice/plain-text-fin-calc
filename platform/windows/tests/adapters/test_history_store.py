"""Tests for the history store adapter."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from plain_text_fin_calc.adapters.history_store import load_history, write_history
from plain_text_fin_calc.domains.calc.history import History, HistoryEntry


class TestHistoryStoreRoundTrip:
    """Tests for JSON persistence round-trip."""

    def test_write_then_load(self, tmp_path: Path):
        file = tmp_path / "history.json"
        ts = datetime(2026, 3, 30, 12, 0, tzinfo=timezone.utc)
        history = History()
        history.append(HistoryEntry("1 + 1", "2", ts))
        history.append(HistoryEntry("3 * 4", "12", ts))

        write_history(history, file)
        loaded = load_history(file)

        assert len(loaded.entries) == 2
        assert loaded.entries[0].expression == "1 + 1"
        assert loaded.entries[0].result == "2"
        assert loaded.entries[1].expression == "3 * 4"

    def test_load_nonexistent_file(self, tmp_path: Path):
        file = tmp_path / "missing.json"
        loaded = load_history(file)
        assert loaded.entries == []

    def test_load_empty_file(self, tmp_path: Path):
        file = tmp_path / "empty.json"
        file.write_text("")
        loaded = load_history(file)
        assert loaded.entries == []

    def test_load_corrupt_file(self, tmp_path: Path):
        file = tmp_path / "bad.json"
        file.write_text("{not valid json!!!")
        loaded = load_history(file)
        assert loaded.entries == []

    def test_load_non_list_json(self, tmp_path: Path):
        file = tmp_path / "bad_shape.json"
        file.write_text('{"expression": "1 + 1"}')
        loaded = load_history(file)
        assert loaded.entries == []

    def test_load_entry_with_missing_field(self, tmp_path: Path):
        file = tmp_path / "bad_entry.json"
        file.write_text('[{"expression": "1 + 1", "result": "2"}]')
        loaded = load_history(file)
        assert loaded.entries == []

    def test_timestamp_preserved(self, tmp_path: Path):
        file = tmp_path / "history.json"
        ts = datetime(2026, 3, 30, 14, 30, 15, tzinfo=timezone.utc)
        history = History()
        history.append(HistoryEntry("5 + 5", "10", ts))

        write_history(history, file)
        loaded = load_history(file)

        assert loaded.entries[0].timestamp == ts


class TestRpnInput:
    """Tests for the optional rpn_input field of a history entry."""

    TS = datetime(2026, 11, 23, 12, 0, 5, tzinfo=timezone.utc)

    def test_rpn_input_survives_write_and_load(self, tmp_path: Path):
        file = tmp_path / "history.json"
        history = History()
        history.append(HistoryEntry("1 + 1", "2", self.TS))
        history.append(HistoryEntry("3 + 4", "7", self.TS, "3 ENTER 4 +"))

        write_history(history, file)
        loaded = load_history(file)

        assert loaded.entries == history.entries
        assert loaded.entries[0].rpn_input is None
        assert loaded.entries[1].rpn_input == "3 ENTER 4 +"

    def test_algebraic_entry_is_written_without_the_key(self, tmp_path: Path):
        file = tmp_path / "history.json"
        write_history(History([HistoryEntry("1 + 1", "2", self.TS)]), file)
        assert "rpn_input" not in file.read_text(encoding="utf-8")
        assert json.loads(file.read_text(encoding="utf-8")) == [
            {
                "expression": "1 + 1",
                "result": "2",
                "timestamp": "2026-11-23T12:00:05+00:00",
            }
        ]

    def test_rpn_entry_is_written_with_the_key_last(self, tmp_path: Path):
        file = tmp_path / "history.json"
        entry = HistoryEntry("3 + 4", "7", self.TS, "3 ENTER 4 +")
        write_history(History([entry]), file)
        (raw,) = json.loads(file.read_text(encoding="utf-8"))
        assert list(raw) == ["expression", "result", "timestamp", "rpn_input"]
        assert raw["rpn_input"] == "3 ENTER 4 +"

    def test_file_saved_before_rpn_existed_loads_unchanged(self, tmp_path: Path):
        file = tmp_path / "history.json"
        file.write_text(
            '[{"expression": "12 + 3", "result": "15",'
            ' "timestamp": "2026-03-30T12:00:00+00:00"}]',
            encoding="utf-8",
        )
        (entry,) = load_history(file).entries
        assert entry == HistoryEntry(
            "12 + 3", "15", datetime(2026, 3, 30, 12, 0, tzinfo=timezone.utc)
        )
        assert entry.rpn_input is None

    @pytest.mark.parametrize("bad", ["5", '""', "null", "[]", "true"])
    def test_invalid_rpn_input_keeps_the_entry_and_the_file(
        self, tmp_path: Path, bad: str
    ):
        file = tmp_path / "history.json"
        file.write_text(
            '[{"expression": "3 + 4", "result": "7",'
            ' "timestamp": "2026-11-23T12:00:05+00:00",'
            f' "rpn_input": {bad}}},'
            ' {"expression": "1 + 1", "result": "2",'
            ' "timestamp": "2026-11-23T12:00:05+00:00",'
            ' "rpn_input": "1 1 +"}]',
            encoding="utf-8",
        )
        first, second = load_history(file).entries
        assert (first.expression, first.rpn_input) == ("3 + 4", None)
        assert second.rpn_input == "1 1 +"
