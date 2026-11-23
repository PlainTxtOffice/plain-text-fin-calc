"""About and Keyboard Shortcuts dialogs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMessageBox

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from plain_text_fin_calc.config.settings import InputMode

# Keep in sync with [project] version in platform/windows/pyproject.toml.
APP_VERSION = "0.1.0"

SHORTCUTS_TEXT = (
    "Enter / Return — evaluate the expression\n"
    "Esc — clear the current expression\n"
    "Backspace — delete the last character\n"
    "L — insert log (base-10 logarithm)\n"
    "Digits and operators (0-9 . + - * / ^ ( )) — press keypad buttons"
)

RPN_SHORTCUTS_TEXT = (
    "Enter / Return — ENTER: copy the number onto the stack\n"
    "Esc — clear the number being entered, or the stack\n"
    "Backspace — delete the last digit\n"
    "L — log (base-10 logarithm) of X\n"
    "S — swap X and Y\n"
    "D — drop X\n"
    "Digits and operators (0-9 . + - * / ^) — press keypad buttons"
)


def show_about(parent: QWidget) -> None:
    """Show the About dialog.

    Parameters
    ----------
    parent : QWidget
        Parent window for the modal dialog.

    """
    QMessageBox.about(
        parent,
        "About Plain Text Fin Calc",
        f"Plain Text Fin Calc {APP_VERSION}\n\n"
        "A Decimal-based desktop calculator with a persistent tape.",
    )


def show_shortcuts(
    parent: QWidget, input_mode: InputMode = "algebraic"
) -> None:
    """Show the Keyboard Shortcuts dialog for the given input mode.

    Parameters
    ----------
    parent : QWidget
        Parent window for the modal dialog.
    input_mode : InputMode
        The active input mode; RPN mode has its own key list.

    """
    text = RPN_SHORTCUTS_TEXT if input_mode == "rpn" else SHORTCUTS_TEXT
    QMessageBox.information(parent, "Keyboard Shortcuts", text)
