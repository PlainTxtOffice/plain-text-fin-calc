"""Tests for the Settings model."""

from __future__ import annotations

from plain_text_fin_calc.config.settings import Settings


class TestSettings:
    """Tests for Settings defaults."""

    def test_defaults(self):
        settings = Settings()
        assert settings.decimal_places is None
        assert settings.theme == "dark"
        assert settings.max_history_entries == 1000

    def test_explicit_values(self):
        settings = Settings(
            decimal_places=2, theme="light", max_history_entries=100
        )
        assert settings.decimal_places == 2
        assert settings.theme == "light"
        assert settings.max_history_entries == 100

    def test_input_mode_defaults_to_algebraic(self):
        assert Settings().input_mode == "algebraic"
        assert Settings(input_mode="rpn").input_mode == "rpn"

    def test_positional_construction_still_works(self):
        settings = Settings(2, "light", None)
        assert settings.max_history_entries is None
        assert settings.input_mode == "algebraic"
