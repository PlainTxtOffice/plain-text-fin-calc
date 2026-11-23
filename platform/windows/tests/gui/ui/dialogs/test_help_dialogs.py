"""Tests for the About and Keyboard Shortcuts dialogs."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QWidget

from plain_text_fin_calc.ui.gui.dialogs import help_dialogs


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_version_matches_pyproject():
    import tomllib
    from pathlib import Path

    pyproject = Path(__file__).resolve().parents[4] / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    assert help_dialogs.APP_VERSION == data["project"]["version"]


def test_show_about_includes_name_and_version(monkeypatch):
    _app()
    captured: dict[str, str] = {}

    def fake_about(parent, title, text):
        captured["title"] = title
        captured["text"] = text

    monkeypatch.setattr(help_dialogs.QMessageBox, "about", fake_about)
    help_dialogs.show_about(QWidget())

    assert captured["title"] == "About Plain Text Fin Calc"
    assert captured["text"].startswith("Plain Text Fin Calc ")
    assert help_dialogs.APP_VERSION in captured["text"]


def test_show_shortcuts_lists_key_bindings(monkeypatch):
    _app()
    captured: dict[str, str] = {}

    def fake_information(parent, title, text):
        captured["title"] = title
        captured["text"] = text

    monkeypatch.setattr(
        help_dialogs.QMessageBox,
        "information",
        fake_information,
    )
    help_dialogs.show_shortcuts(QWidget())

    assert "Shortcuts" in captured["title"]
    for token in ("Enter", "Esc", "Backspace", "L — insert log"):
        assert token in captured["text"]


def _shown_shortcuts(monkeypatch, *args) -> str:
    _app()
    captured: list[str] = []
    monkeypatch.setattr(
        help_dialogs.QMessageBox,
        "information",
        lambda _parent, _title, text: captured.append(text),
    )
    help_dialogs.show_shortcuts(QWidget(), *args)
    return captured[0]


def test_rpn_shortcuts_list_swap_and_drop(monkeypatch):
    text = _shown_shortcuts(monkeypatch, "rpn")
    assert text.splitlines() == [
        "Enter / Return \u2014 ENTER: copy the number onto the stack",
        "Esc \u2014 clear the number being entered, or the stack",
        "Backspace \u2014 delete the last digit",
        "L \u2014 log (base-10 logarithm) of X",
        "S \u2014 swap X and Y",
        "D \u2014 drop X",
        "Digits and operators (0-9 . + - * / ^) \u2014 press keypad buttons",
    ]
    assert "( )" not in text


def test_default_shortcuts_text_is_the_algebraic_one(monkeypatch):
    assert _shown_shortcuts(monkeypatch) == help_dialogs.SHORTCUTS_TEXT
    assert _shown_shortcuts(monkeypatch, "algebraic") == (
        help_dialogs.SHORTCUTS_TEXT
    )
    assert "( )" in help_dialogs.SHORTCUTS_TEXT
    assert "S \u2014 swap" not in help_dialogs.SHORTCUTS_TEXT
