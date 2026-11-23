"""Tests for JSON settings persistence."""

from __future__ import annotations

import json

import pytest

from plain_text_fin_calc.adapters.settings_store import load_settings, write_settings
from plain_text_fin_calc.config.settings import Settings
from plain_text_fin_calc.domains.calc.text_tape import TextTapeFormat


class TestLoadSettings:
    """Tests for load_settings."""

    def test_missing_file_returns_defaults(self, tmp_path):
        settings = load_settings(tmp_path / "settings.json")
        assert settings == Settings()

    def test_corrupt_json_returns_defaults(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_text("{not json", encoding="utf-8")
        assert load_settings(path) == Settings()

    def test_empty_file_returns_defaults(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_text("", encoding="utf-8")
        assert load_settings(path) == Settings()

    def test_unknown_theme_falls_back_to_dark(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_text('{"theme": "neon"}', encoding="utf-8")
        assert load_settings(path).theme == "dark"

    def test_invalid_decimal_places_falls_back_to_none(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_text('{"decimal_places": "two"}', encoding="utf-8")
        assert load_settings(path).decimal_places is None

    def test_negative_decimal_places_falls_back_to_none(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_text('{"decimal_places": -1}', encoding="utf-8")
        assert load_settings(path).decimal_places is None

    def test_invalid_history_cap_falls_back_to_default(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_text('{"max_history_entries": 0}', encoding="utf-8")
        assert load_settings(path).max_history_entries == 1000

    def test_missing_history_cap_uses_default(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_text('{"theme": "dark"}', encoding="utf-8")
        assert load_settings(path).max_history_entries == 1000

    def test_explicit_null_history_cap_means_unlimited(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_text('{"max_history_entries": null}', encoding="utf-8")
        assert load_settings(path).max_history_entries is None

    def test_out_of_range_decimal_places_clamps_to_max(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_text('{"decimal_places": 9}', encoding="utf-8")
        assert load_settings(path).decimal_places == 6

    def test_out_of_range_history_cap_clamps_to_max(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_text('{"max_history_entries": 50000}', encoding="utf-8")
        assert load_settings(path).max_history_entries == 10000

    def test_invalid_utf8_returns_defaults(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_bytes(b"\xff\xfe\x00garbage")
        assert load_settings(path) == Settings()

    def test_unknown_fields_ignored(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_text('{"theme": "light", "mystery": true}', encoding="utf-8")
        assert load_settings(path).theme == "light"

    def test_legacy_settings_use_default_tape_layout(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_text('{"theme": "light"}', encoding="utf-8")
        assert load_settings(path) == Settings(theme="light")

    def test_invalid_tape_switch_preserves_valid_sibling(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_text(
            '{"text_tape": {"date_headings": false, "entry_times": "false"}}',
            encoding="utf-8",
        )
        assert load_settings(path).text_tape == TextTapeFormat(
            date_headings=False, entry_times=True,
        )

    def test_invalid_zone_and_formats_preserve_seconds(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_text(
            '{"text_tape":{"time_zone":"Missing/Zone","date_format":[],'
            '"twelve_hour":"false","seconds":true}}', encoding="utf-8",
        )
        assert load_settings(path).text_tape == TextTapeFormat(seconds=True)


class TestRoundTrip:
    """Tests for write_settings + load_settings."""

    def test_round_trip(self, tmp_path):
        path = tmp_path / "settings.json"
        original = Settings(
            decimal_places=4, theme="light", max_history_entries=250,
            text_tape=TextTapeFormat(date_headings=False, entry_times=False),
        )
        write_settings(original, path)
        assert load_settings(path) == original

    def test_write_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "nested" / "settings.json"
        write_settings(Settings(), path)
        assert path.exists()


def test_settings_file_constant_lives_in_data_dir():
    from plain_text_fin_calc.config.path_handler import DATA_DIR, SETTINGS_FILE

    assert SETTINGS_FILE == DATA_DIR / "settings.json"


class TestInputMode:
    """Tests for the saved input_mode setting."""

    @pytest.mark.parametrize(
        "text",
        [
            '{"theme": "light", "decimal_places": 2}',
            '{"theme": "light", "decimal_places": 2, "input_mode": 7}',
            '{"theme": "light", "decimal_places": 2, "input_mode": null}',
            '{"theme": "light", "decimal_places": 2, "input_mode": "other"}',
            '{"theme": "light", "decimal_places": 2, "input_mode": "RPN"}',
            '{"theme": "light", "decimal_places": 2, "input_mode": ["rpn"]}',
        ],
    )
    def test_missing_or_invalid_mode_loads_as_algebraic(self, tmp_path, text):
        path = tmp_path / "settings.json"
        path.write_text(text, encoding="utf-8")
        assert load_settings(path) == Settings(
            decimal_places=2, theme="light", input_mode="algebraic"
        )

    def test_rpn_mode_loads(self, tmp_path):
        path = tmp_path / "settings.json"
        path.write_text('{"input_mode": "rpn"}', encoding="utf-8")
        assert load_settings(path) == Settings(input_mode="rpn")

    def test_rpn_mode_round_trips_as_a_top_level_key(self, tmp_path):
        path = tmp_path / "settings.json"
        original = Settings(decimal_places=4, theme="light", input_mode="rpn")
        write_settings(original, path)
        raw = json.loads(path.read_text(encoding="utf-8"))
        assert raw["input_mode"] == "rpn"
        assert list(raw)[-1] == "input_mode"
        assert load_settings(path) == original

    def test_default_mode_is_always_written(self, tmp_path):
        path = tmp_path / "settings.json"
        write_settings(Settings(), path)
        raw = json.loads(path.read_text(encoding="utf-8"))
        assert raw["input_mode"] == "algebraic"
