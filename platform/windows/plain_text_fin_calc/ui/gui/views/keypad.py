"""Calculator button grid with keyboard input forwarding."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QPushButton, QSizePolicy, QWidget

if TYPE_CHECKING:
    from collections.abc import Callable

    from plain_text_fin_calc.config.settings import InputMode

BUTTON_LAYOUT: list[list[str]] = [
    ["log", "(", ")", "C", ""],
    ["7", "8", "9", "/", "^"],
    ["4", "5", "6", "*", "←"],
    ["1", "2", "3", "-", "="],
    ["0", ".", "±", "+", ""],
]

# The three keys that differ in RPN mode, by their algebraic label:
# (RPN label, accessible name). All other keys are the same in both modes.
RPN_KEYS: dict[str, tuple[str, str]] = {
    "(": ("x↔y", "Swap X and Y"),
    ")": ("DROP", "Drop"),
    "=": ("ENTER", "Enter"),
}

KEY_FONT_PX = 18
# Word labels (DROP, ENTER) are smaller so they fit a key at minimum width.
WORD_KEY_FONT_PX = 15

KEY_MAP: dict[str, str] = {
    "0": "0",
    "1": "1",
    "2": "2",
    "3": "3",
    "4": "4",
    "5": "5",
    "6": "6",
    "7": "7",
    "8": "8",
    "9": "9",
    ".": ".",
    "+": "+",
    "-": "-",
    "*": "*",
    "/": "/",
    "^": "^",
    "(": "(",
    ")": ")",
    "l": "log",
    "L": "log",
}


class KeypadView(QWidget):
    """Grid of calculator buttons.

    Emits signals for each button type rather than handling
    logic directly. In RPN mode the two parenthesis keys become swap and
    drop, and the tall key is labelled ENTER; it emits ``evaluate_pressed``
    in both modes.

    Parameters
    ----------
    parent : QWidget | None
        Parent widget.

    """

    token_pressed = Signal(str)
    evaluate_pressed = Signal()
    clear_pressed = Signal()
    backspace_pressed = Signal()
    toggle_sign_pressed = Signal()
    swap_pressed = Signal()
    drop_pressed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the keypad view with calculator buttons."""
        super().__init__(parent)
        self._input_mode: InputMode = "algebraic"
        self._mode_buttons: dict[str, QPushButton] = {}
        layout = QGridLayout(self)
        layout.setSpacing(2)

        for row_idx, row in enumerate(BUTTON_LAYOUT):
            for col_idx, label in enumerate(row):
                if not label:
                    continue
                btn = QPushButton(label)
                btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                btn.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Expanding,
                )
                btn.setMinimumHeight(50)
                # Use QFont, not a stylesheet: any stylesheet pins the
                # button's palette so live theme switches stop applying.
                font = btn.font()
                font.setPixelSize(KEY_FONT_PX)
                btn.setFont(font)
                btn.clicked.connect(self._make_click_callback(label))
                if label in RPN_KEYS:
                    self._mode_buttons[label] = btn
                if label == "=":
                    layout.addWidget(btn, row_idx, col_idx, 2, 1)
                else:
                    layout.addWidget(btn, row_idx, col_idx)

    def set_input_mode(self, mode: InputMode) -> None:
        """Label the three mode-dependent keys for the given input mode.

        The buttons are relabelled in place, so focus policy and theme are
        kept. RPN labels get an accessible name, and the word labels a
        smaller font; algebraic labels speak for themselves and have no
        accessible name.
        """
        self._input_mode = mode
        is_rpn = mode == "rpn"
        for label, button in self._mode_buttons.items():
            rpn_label, accessible_name = RPN_KEYS[label]
            text = rpn_label if is_rpn else label
            font = button.font()
            font.setPixelSize(
                WORD_KEY_FONT_PX if text.isalpha() else KEY_FONT_PX,
            )
            button.setFont(font)
            button.setText(text)
            button.setAccessibleName(accessible_name if is_rpn else "")

    def _make_click_callback(self, label: str) -> Callable[[], None]:
        """Return a slot closure for the given button label."""

        def on_click() -> None:
            self._route_button(label)

        return on_click

    def _route_button(self, label: str) -> None:
        """Emit the signal for a button, named by its algebraic label."""
        is_rpn = self._input_mode == "rpn"
        if label == "=":
            self.evaluate_pressed.emit()
        elif label == "C":
            self.clear_pressed.emit()
        elif label == "←":
            self.backspace_pressed.emit()
        elif label == "±":
            self.toggle_sign_pressed.emit()
        elif is_rpn and label == "(":
            self.swap_pressed.emit()
        elif is_rpn and label == ")":
            self.drop_pressed.emit()
        else:
            self.token_pressed.emit(label)

    def map_key_press(self, key_text: str) -> None:
        """Translate a keyboard key string into the appropriate signal.

        In RPN mode S swaps and D drops; those letters are unbound in
        algebraic mode.
        """
        if key_text in KEY_MAP:
            self.token_pressed.emit(KEY_MAP[key_text])
        elif self._input_mode == "rpn" and key_text in {"s", "S"}:
            self.swap_pressed.emit()
        elif self._input_mode == "rpn" and key_text in {"d", "D"}:
            self.drop_pressed.emit()
