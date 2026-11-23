"""Build the calculator menu bar."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PySide6.QtGui import QAction

from plain_text_fin_calc.ui.gui.feedback import add_feedback_action

if TYPE_CHECKING:
    from collections.abc import Callable

    from PySide6.QtWidgets import QMainWindow, QMenu

APP_NAME = "Plain Text Fin Calc"
DISTRIBUTION = "fin-calc"


@dataclass(frozen=True)
class MenuBarCallbacks:
    """Handlers the root window supplies for menu actions.

    Parameters
    ----------
    export_history : Callable[[], None]
        Export the history to CSV or a plain text tape.
    clear_history : Callable[[], None]
        Clear all history entries.
    open_settings : Callable[[], None]
        Open the Settings dialog.
    show_about : Callable[[], None]
        Show the About dialog.
    show_shortcuts : Callable[[], None]
        Show the Keyboard Shortcuts dialog.

    """

    export_history: Callable[[], None]
    clear_history: Callable[[], None]
    open_settings: Callable[[], None]
    show_about: Callable[[], None]
    show_shortcuts: Callable[[], None]


@dataclass
class MenuBarParts:
    """Hold menu objects and actions owned by the root window."""

    file_menu: QMenu
    edit_menu: QMenu
    help_menu: QMenu
    export_history_action: QAction
    clear_history_action: QAction
    exit_action: QAction
    settings_action: QAction
    about_action: QAction
    shortcuts_action: QAction
    feedback_action: QAction


def build_menu_bar(
    window: QMainWindow,
    callbacks: MenuBarCallbacks,
) -> MenuBarParts:
    """Build File, Edit, and Help menus for the root window."""
    file_menu = window.menuBar().addMenu("&File")

    export_history_action = QAction("Export History...", window)
    export_history_action.triggered.connect(callbacks.export_history)
    file_menu.addAction(export_history_action)

    file_menu.addSeparator()

    clear_history_action = QAction("Clear History", window)
    clear_history_action.triggered.connect(callbacks.clear_history)
    file_menu.addAction(clear_history_action)

    file_menu.addSeparator()

    exit_action = QAction("Exit", window)
    exit_action.triggered.connect(window.close)
    file_menu.addAction(exit_action)

    edit_menu = window.menuBar().addMenu("&Edit")

    settings_action = QAction("Settings...", window)
    settings_action.triggered.connect(callbacks.open_settings)
    edit_menu.addAction(settings_action)

    help_menu = window.menuBar().addMenu("&Help")

    shortcuts_action = QAction("Keyboard Shortcuts", window)
    shortcuts_action.triggered.connect(callbacks.show_shortcuts)
    help_menu.addAction(shortcuts_action)

    feedback_action = add_feedback_action(
        help_menu, window, APP_NAME, DISTRIBUTION
    )

    help_menu.addSeparator()

    about_action = QAction("About", window)
    about_action.triggered.connect(callbacks.show_about)
    help_menu.addAction(about_action)

    return MenuBarParts(
        file_menu=file_menu,
        edit_menu=edit_menu,
        help_menu=help_menu,
        export_history_action=export_history_action,
        clear_history_action=clear_history_action,
        exit_action=exit_action,
        settings_action=settings_action,
        about_action=about_action,
        shortcuts_action=shortcuts_action,
        feedback_action=feedback_action,
    )
