"""Tests for RPN mode in the root calculator window."""

from __future__ import annotations

import os
from datetime import UTC, datetime

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton

from plain_text_fin_calc.adapters.history_store import load_history
from plain_text_fin_calc.adapters.settings_store import load_settings
from plain_text_fin_calc.config.settings import Settings
from plain_text_fin_calc.domains.calc.history import History, HistoryEntry
from plain_text_fin_calc.domains.calc.rpn_stack import RpnStack
from plain_text_fin_calc.ui.gui.dialogs import help_dialogs
from plain_text_fin_calc.ui.gui.views import root_window

THIRD = "0.3333333333333333333333333333"


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def files(monkeypatch, tmp_path):
    """Point the window's history and settings files at a temporary folder."""
    _app()
    monkeypatch.setattr(root_window, "HISTORY_FILE", tmp_path / "history.json")
    monkeypatch.setattr(root_window, "SETTINGS_FILE", tmp_path / "settings.json")
    return tmp_path


def _window(**settings) -> root_window.RootWindow:
    return root_window.RootWindow(
        History(), settings=Settings(input_mode="rpn", **settings)
    )


def _press(window, *tokens: str) -> None:
    for token in tokens:
        window._on_token(token)


def _key(window, key: Qt.Key, text: str = "") -> None:
    window.keyPressEvent(
        QKeyEvent(
            QKeyEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier, text
        )
    )


def _click(window, label: str) -> None:
    (button,) = [
        b for b in window._keypad.findChildren(QPushButton) if b.text() == label
    ]
    button.click()


def _x(window) -> str:
    return window._display._expression_label.text()


def _y(window) -> str:
    return window._display._y_label.text()


def _status(window) -> str:
    return window._display._status_label.text()


def _tape(window) -> list[str]:
    tape = window._tape._list
    return [tape.item(row).text() for row in range(tape.count())]


def _keypad_labels(window) -> set[str]:
    return {b.text() for b in window._keypad.findChildren(QPushButton)}


def test_rpn_calculation_shows_registers_and_saves_keys(files):
    window = _window(decimal_places=2)
    assert (_x(window), _y(window)) == ("", "Y:")
    _press(window, "1")
    assert (_x(window), _y(window)) == ("1", "Y:")
    _key(window, Qt.Key.Key_Return)
    assert (_x(window), _y(window)) == ("1.00", "Y: 1.00")
    _press(window, "3")
    assert (_x(window), _y(window)) == ("3", "Y: 1.00")
    _press(window, "/")

    assert (_x(window), _y(window)) == ("0.33", "Y:")
    assert window._rpn == RpnStack((THIRD,))
    (entry,) = window._history.entries
    assert (entry.expression, entry.result, entry.rpn_input) == (
        "1 / 3", THIRD, "1 ENTER 3 /",
    )
    assert _tape(window) == ["1 / 3 = 0.33"]
    window.close()
    (saved,) = load_history(files / "history.json").entries
    assert saved == entry


def test_rpn_keypad_buttons_drive_the_stack(files):
    window = _window()
    assert {"x↔y", "DROP", "ENTER"} <= _keypad_labels(window)
    assert not {"(", ")", "="} & _keypad_labels(window)
    _click(window, "8")
    _click(window, "ENTER")
    _click(window, "2")
    _click(window, "x↔y")
    assert window._rpn.levels == ("8", "2")
    _click(window, "/")
    assert _tape(window) == ["2 / 8 = 0.25"]
    _click(window, "7")
    _click(window, "DROP")
    assert window._rpn.levels == ("0.25",)
    _click(window, "±")
    assert _x(window) == "-0.25"
    _click(window, "log")
    assert _status(window) == "Log undefined for non-positive values"
    _click(window, "C")
    assert (window._rpn, _status(window)) == (RpnStack(), "")
    assert [e.rpn_input for e in window._history.entries] == ["8 ENTER 2 SWAP /"]
    window.close()


def test_rpn_keyboard_shortcuts(files):
    window = _window()
    _key(window, Qt.Key.Key_8, "8")
    _key(window, Qt.Key.Key_Enter)
    _key(window, Qt.Key.Key_2, "2")
    _key(window, Qt.Key.Key_S, "s")
    assert window._rpn.levels == ("8", "2")
    _key(window, Qt.Key.Key_D, "D")
    assert window._rpn.levels == ("2",)
    _key(window, Qt.Key.Key_1, "1")
    _key(window, Qt.Key.Key_0, "0")
    _key(window, Qt.Key.Key_0, "0")
    _key(window, Qt.Key.Key_L, "l")
    assert _tape(window) == ["log ( 100 ) = 2"]
    _key(window, Qt.Key.Key_ParenLeft, "(")
    assert _status(window) == "Invalid input: ("
    _key(window, Qt.Key.Key_ParenRight, ")")
    assert _status(window) == "Invalid input: )"
    window.close()


def test_swap_and_drop_keys_are_unbound_in_algebraic_mode(files):
    window = root_window.RootWindow(History())
    _press(window, "2", "+")
    _key(window, Qt.Key.Key_S, "s")
    _key(window, Qt.Key.Key_D, "d")
    assert (_x(window), _status(window)) == ("2 +", "")
    assert window._display._y_label.isHidden()
    window.close()


def test_rpn_error_changes_only_the_status_line(files):
    window = _window()
    _press(window, "+")
    assert _status(window) == "Too few operands"
    assert (window._rpn, _x(window), _y(window)) == (RpnStack(), "", "Y:")
    assert window._history.entries == []
    _press(window, "5")
    assert (_status(window), _x(window)) == ("", "5")
    _press(window, "+")
    assert _status(window) == "Too few operands"
    assert window._rpn == RpnStack((), "5")
    window._on_backspace()
    assert (_status(window), window._rpn) == ("", RpnStack())
    window.close()


def test_rpn_escape_backspace_and_sign(files):
    window = _window()
    _press(window, "3")
    _key(window, Qt.Key.Key_Return)
    _press(window, "4", "5")
    _key(window, Qt.Key.Key_Backspace)
    assert (_x(window), _y(window)) == ("4", "Y: 3")
    window._on_toggle_sign()
    assert _x(window) == "-4"
    _key(window, Qt.Key.Key_Escape)
    assert window._rpn == RpnStack(("3",), None, True, ("3", "ENTER"))
    assert (_x(window), _y(window)) == ("3", "Y:")
    window._on_toggle_sign()
    assert window._rpn.levels == ("-3",)
    assert _x(window) == "-3"
    _key(window, Qt.Key.Key_Escape)
    assert (window._rpn, _x(window)) == (RpnStack(), "")
    window.close()


def test_tape_click_puts_result_on_the_stack(files):
    window = _window(decimal_places=2)
    _press(window, "9", "7")
    window._on_result_clicked("42")
    assert window._rpn.levels == ("42",)
    assert window._rpn.entry is None
    assert _x(window) == "42.00"
    _press(window, "3")
    assert (_x(window), _y(window)) == ("3", "Y: 42.00")
    window.close()

    window = _window()
    _press(window, "2")
    window._on_evaluate()
    window._on_result_clicked("7")
    assert (window._rpn.levels, window._rpn.lift) == (("7", "2"), True)
    _press(window, "+")
    window._on_result_clicked("7")
    assert window._rpn.levels == ("7", "9")
    _press(window, "*")
    assert [
        (e.expression, e.result, e.rpn_input) for e in window._history.entries
    ] == [("2 + 7", "9", "2 ENTER 7 +"), ("9 * 7", "63", "7 *")]
    window._on_result_clicked("abc")
    assert _status(window) == "Invalid number: abc"
    assert window._rpn.levels == ("63",)
    window.close()


def test_clicking_a_tape_row_in_rpn_mode_reuses_its_full_result(files):
    window = _window(decimal_places=2)
    _press(window, "1")
    window._on_evaluate()
    _press(window, "3", "/")
    window._on_clear()
    window._tape._list.itemClicked.emit(window._tape._list.item(0))
    assert window._rpn.levels == (THIRD,)
    assert _x(window) == "0.33"
    window.close()


def test_mode_switch_clears_pending_input_and_keeps_history(files):
    window = _window()
    _press(window, "5")
    window._on_evaluate()
    _press(window, "3", "+", "7")
    assert (window._rpn.levels, window._rpn.entry) == (("8",), "7")
    assert len(window._history.entries) == 1
    _press(window, "(")
    assert _status(window) == "Invalid input: ("

    window._apply_settings(Settings(input_mode="algebraic"))
    assert (_x(window), _status(window)) == ("", "")
    assert window._display._y_label.isHidden()
    assert {"(", ")", "="} <= _keypad_labels(window)
    assert not {"x↔y", "DROP", "ENTER"} & _keypad_labels(window)
    assert _tape(window) == ["5 + 3 = 8"]
    assert len(window._history.entries) == 1
    assert load_settings(files / "settings.json").input_mode == "algebraic"

    _press(window, "2", "+")
    assert _x(window) == "2 +"
    window._apply_settings(Settings(input_mode="rpn"))
    assert (window._rpn, _x(window), _y(window)) == (RpnStack(), "", "Y:")
    assert not window._display._y_label.isHidden()
    assert load_settings(files / "settings.json").input_mode == "rpn"
    window._apply_settings(Settings(input_mode="algebraic"))
    assert _x(window) == ""
    assert _tape(window) == ["5 + 3 = 8"]
    window.close()


def test_applying_settings_without_mode_change_keeps_pending_input(files):
    window = _window()
    _press(window, "5")
    window._on_evaluate()
    _press(window, "1", "2")
    before = window._rpn
    window._apply_settings(Settings(input_mode="rpn", decimal_places=2))
    assert window._rpn == before
    assert (_x(window), _y(window)) == ("12", "Y: 5.00")
    window.close()

    window = root_window.RootWindow(History())
    _press(window, "2", "+")
    window._apply_settings(Settings(theme="light"))
    assert _x(window) == "2 +"
    window._apply_settings(Settings())
    window.close()


def test_mode_change_applies_even_when_settings_cannot_be_saved(
    files, monkeypatch
):
    def deny_write(*_args):
        message = "settings are read-only"
        raise PermissionError(message)

    monkeypatch.setattr(root_window, "write_settings", deny_write)
    window = root_window.RootWindow(History())
    _press(window, "2", "+")
    window._apply_settings(Settings(input_mode="rpn"))
    assert window.statusBar().currentMessage() == (
        "Saving settings failed: settings are read-only"
    )
    assert window._settings.input_mode == "rpn"
    assert "ENTER" in _keypad_labels(window)
    assert (_x(window), _y(window)) == ("", "Y:")
    _press(window, "3")
    window._on_evaluate()
    assert window._rpn.levels == ("3", "3")
    window.close()


def test_settings_dialog_switches_the_window_to_rpn(files, monkeypatch):
    window = root_window.RootWindow(History())
    _press(window, "2", "+")

    def choose_rpn(dialog):
        combo = dialog._input_mode_combo
        assert combo.currentData() == "algebraic"
        combo.setCurrentIndex(combo.findData("rpn"))
        return root_window.QDialog.DialogCode.Accepted

    monkeypatch.setattr(root_window.SettingsDialog, "exec", choose_rpn)
    window._menus.settings_action.trigger()
    assert window._settings.input_mode == "rpn"
    assert load_settings(files / "settings.json").input_mode == "rpn"
    assert (_x(window), _y(window)) == ("", "Y:")
    _press(window, "3")
    window._on_evaluate()
    _press(window, "4", "+")
    assert _tape(window) == ["3 + 4 = 7"]
    window.close()

    restarted = root_window.RootWindow(
        History(), load_settings(files / "settings.json")
    )
    assert "ENTER" in _keypad_labels(restarted)
    assert restarted._rpn == RpnStack()
    restarted.close()


def test_settings_preview_shows_rpn_input_line(files, monkeypatch):
    window = _window()
    _press(window, "3")
    window._on_evaluate()
    _press(window, "4", "+")
    previews = []

    def read_preview(dialog):
        previews.append(dialog._text_export._preview.toPlainText())
        return root_window.QDialog.DialogCode.Rejected

    monkeypatch.setattr(root_window.SettingsDialog, "exec", read_preview)
    window._menus.settings_action.trigger()
    assert "3 + 4 = 7\nRPN input: 3 ENTER 4 +\n" in previews[0]
    window.close()


def test_shortcuts_dialog_follows_the_input_mode(files, monkeypatch):
    shown = []
    monkeypatch.setattr(
        help_dialogs.QMessageBox,
        "information",
        lambda _parent, _title, text: shown.append(text),
    )
    window = _window()
    window._menus.shortcuts_action.trigger()
    window._apply_settings(Settings())
    window._menus.shortcuts_action.trigger()
    assert shown == [
        help_dialogs.RPN_SHORTCUTS_TEXT,
        help_dialogs.SHORTCUTS_TEXT,
    ]
    window.close()


def test_register_accessible_names(files):
    window = _window(decimal_places=2)
    display = window._display
    assert display._y_label.accessibleName() == "Y register, empty"
    assert display._expression_label.accessibleName() == "X register, empty"
    _press(window, "5")
    window._on_evaluate()
    _press(window, "7")
    assert display._y_label.accessibleName() == "Y register, 5.00"
    assert display._expression_label.accessibleName() == "X register, 7"

    window._apply_settings(Settings())
    assert display._y_label.isHidden()
    assert display._y_label.accessibleName() == ""
    assert display._expression_label.accessibleName() == ""
    _press(window, "2")
    assert display._expression_label.accessibleName() == ""
    window.close()


def test_display_restyle_colors_the_y_line(files):
    from plain_text_fin_calc.ui.gui.views.theme import get_theme

    window = _window()
    light = get_theme("light")
    window._display.restyle(light)
    style = window._display._y_label.styleSheet()
    assert light.display_bg in style
    assert light.placeholder_text in style
    window.close()


def test_algebraic_evaluation_is_unchanged(files):
    window = root_window.RootWindow(History(), Settings(decimal_places=2))
    _press(window, "1", "/", "3")
    window._on_evaluate()
    assert _x(window) == "0.33"
    (entry,) = window._history.entries
    assert (entry.expression, entry.result, entry.rpn_input) == (
        "1 / 3", THIRD, None,
    )
    window.close()


def _show(window) -> None:
    window.show()
    window.activateWindow()
    QApplication.processEvents()


def _type(window, keys: str) -> None:
    """Send real key events to wherever keyboard focus is."""
    target = QApplication.focusWidget() or window
    QTest.keyClicks(target, keys)


def _click_tape_row(window, row: int) -> None:
    tape = window._tape._list
    point = tape.visualItemRect(tape.item(row)).center()
    QTest.mouseClick(tape.viewport(), Qt.MouseButton.LeftButton, pos=point)


def _entry(expression: str, result: str) -> HistoryEntry:
    return HistoryEntry(expression, result, datetime.now(tz=UTC))


def test_tape_never_takes_keyboard_focus(files):
    window = _window()
    _show(window)
    tape = window._tape._list
    assert tape.focusPolicy() == Qt.FocusPolicy.NoFocus
    assert QApplication.focusWidget() is not tape
    window.close()


def test_rpn_typed_keys_reach_the_stack_after_a_tape_click(files):
    window = root_window.RootWindow(
        History(entries=[_entry("1 + 1", "2")]),
        settings=Settings(input_mode="rpn"),
    )
    _show(window)
    _click_tape_row(window, 0)
    assert window._rpn.levels == ("2",)
    assert QApplication.focusWidget() is not window._tape._list

    _type(window, "5")
    assert (window._rpn.entry, window._rpn.levels) == ("5", ("2",))
    _type(window, "s")
    assert window._rpn.levels == ("2", "5")
    _type(window, "d")
    assert window._rpn.levels == ("5",)
    _type(window, "3+")
    assert window._rpn.levels == ("8",)
    assert _tape(window) == ["1 + 1 = 2", "5 + 3 = 8"]
    window.close()


def test_algebraic_typed_keys_reach_the_expression_after_a_tape_click(files):
    window = root_window.RootWindow(
        History(entries=[_entry("1 + 1", "2")]), settings=Settings()
    )
    _show(window)
    _type(window, "3+")
    assert _x(window) == "3 +"
    _click_tape_row(window, 0)
    assert _x(window) == "3 + 2"
    _type(window, "*4")
    assert _x(window) == "3 + 2 * 4"
    window.close()
