"""Tests for the calculator keypad view."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QPushButton

from plain_text_fin_calc.ui.gui.views.keypad import KeypadView


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_keypad_does_not_show_clear_entry_button() -> None:
    """Verify backspace is the only single-entry correction control."""
    _app()
    keypad = KeypadView()

    labels = {button.text() for button in keypad.findChildren(QPushButton)}

    assert "CE" not in labels
    assert "\u2190" in labels


def test_l_key_maps_to_log_token() -> None:
    """Typing 'l' or 'L' enters the log function from the keyboard."""
    _app()
    keypad = KeypadView()
    received: list[str] = []
    keypad.token_pressed.connect(received.append)

    keypad.map_key_press("l")
    keypad.map_key_press("L")

    assert received == ["log", "log"]


def test_buttons_do_not_take_focus() -> None:
    """Buttons must not grab focus, so Space never re-triggers them."""
    _app()
    keypad = KeypadView()

    policies = {
        button.focusPolicy() for button in keypad.findChildren(QPushButton)
    }

    assert policies == {Qt.FocusPolicy.NoFocus}


def test_keypad_buttons_follow_live_palette_change() -> None:
    """Buttons must pick up palette changes from live theme switches."""
    from PySide6.QtGui import QColor

    from plain_text_fin_calc.ui.gui.views.theme import apply_theme, get_theme

    app = _app()
    apply_theme(app, "dark")
    keypad = KeypadView()
    keypad.show()  # polish widgets; the bug only appears once polished
    app.processEvents()
    apply_theme(app, "light")
    app.processEvents()
    button = keypad.findChildren(QPushButton)[0]
    assert button.palette().button().color() == QColor(
        get_theme("light").button
    )
    apply_theme(app, "dark")  # restore for other tests


def _buttons(keypad: KeypadView) -> dict[str, QPushButton]:
    return {button.text(): button for button in keypad.findChildren(QPushButton)}


def test_rpn_mode_relabels_three_keys_in_place() -> None:
    """RPN mode shows swap, DROP and ENTER where ( ) and = are."""
    _app()
    keypad = KeypadView()
    before = keypad.findChildren(QPushButton)
    algebraic_labels = set(_buttons(keypad))
    assert {"(", ")", "="} <= algebraic_labels

    keypad.set_input_mode("rpn")

    buttons = _buttons(keypad)
    assert set(buttons) == (algebraic_labels - {"(", ")", "="}) | {
        "x\u2194y", "DROP", "ENTER",
    }
    assert buttons["x\u2194y"].accessibleName() == "Swap X and Y"
    assert buttons["DROP"].accessibleName() == "Drop"
    assert buttons["ENTER"].accessibleName() == "Enter"
    assert keypad.findChildren(QPushButton) == before
    assert {b.focusPolicy() for b in before} == {Qt.FocusPolicy.NoFocus}
    assert buttons["ENTER"].font().pixelSize() < buttons["7"].font().pixelSize()

    keypad.set_input_mode("algebraic")

    buttons = _buttons(keypad)
    assert set(buttons) == algebraic_labels
    assert [buttons[label].accessibleName() for label in "()="] == ["", "", ""]
    assert buttons["="].font().pixelSize() == buttons["7"].font().pixelSize()


def _record(keypad: KeypadView) -> list[str]:
    events: list[str] = []
    keypad.token_pressed.connect(events.append)
    keypad.evaluate_pressed.connect(lambda: events.append("<evaluate>"))
    keypad.swap_pressed.connect(lambda: events.append("<swap>"))
    keypad.drop_pressed.connect(lambda: events.append("<drop>"))
    return events


def test_rpn_buttons_emit_swap_drop_and_evaluate() -> None:
    """The relabelled keys emit their own signals; the tall key still evaluates."""
    _app()
    keypad = KeypadView()
    events = _record(keypad)

    for label in ("(", ")", "="):
        _buttons(keypad)[label].click()
    keypad.set_input_mode("rpn")
    for label in ("x\u2194y", "DROP", "ENTER", "log", "7"):
        _buttons(keypad)[label].click()

    assert events == [
        "(", ")", "<evaluate>", "<swap>", "<drop>", "<evaluate>", "log", "7",
    ]


def test_s_and_d_keys_swap_and_drop_only_in_rpn_mode() -> None:
    """S and D are RPN shortcuts and stay unbound in algebraic mode."""
    _app()
    keypad = KeypadView()
    events = _record(keypad)

    for key in ("s", "S", "d", "D", "l"):
        keypad.map_key_press(key)
    assert events == ["log"]

    keypad.set_input_mode("rpn")
    for key in ("s", "S", "d", "D", "l", "(", "x"):
        keypad.map_key_press(key)
    assert events == ["log", "<swap>", "<swap>", "<drop>", "<drop>", "log", "("]
