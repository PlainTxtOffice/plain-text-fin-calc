"""Main calculator window assembling tape, display, and keypad."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from plain_text_fin_calc.adapters.history_export import (
    write_history_csv,
    write_history_text,
)
from plain_text_fin_calc.adapters.history_store import write_history
from plain_text_fin_calc.adapters.settings_store import write_settings
from plain_text_fin_calc.config.path_handler import (
    EXPORTS_DIR,
    HISTORY_FILE,
    SETTINGS_FILE,
)
from plain_text_fin_calc.config.settings import Settings
from plain_text_fin_calc.domains.calc.errors import EvaluationError
from plain_text_fin_calc.domains.calc.evaluator import evaluate, result_text
from plain_text_fin_calc.domains.calc.expression import ExpressionBuilder
from plain_text_fin_calc.domains.calc.formatting import format_result
from plain_text_fin_calc.domains.calc.history import History, HistoryEntry
from plain_text_fin_calc.domains.calc.rpn_stack import RpnStack
from plain_text_fin_calc.ui.gui.dialogs.help_dialogs import (
    show_about,
    show_shortcuts,
)
from plain_text_fin_calc.ui.gui.dialogs.settings_dialog import SettingsDialog
from plain_text_fin_calc.ui.gui.menus.menu_bar import (
    MenuBarCallbacks,
    build_menu_bar,
)
from plain_text_fin_calc.ui.gui.views.display import DisplayView
from plain_text_fin_calc.ui.gui.views.keypad import KeypadView
from plain_text_fin_calc.ui.gui.views.tape import TapeView
from plain_text_fin_calc.ui.gui.views.theme import apply_theme, get_theme

if TYPE_CHECKING:
    from collections.abc import Callable
    from concurrent.futures import Future

    from PySide6.QtGui import QCloseEvent, QKeyEvent

    from plain_text_fin_calc.domains.calc.rpn_stack import RpnStep


class RootWindow(QMainWindow):
    """Main calculator window.

    Parameters
    ----------
    history : History
        Pre-loaded history model.
    settings : Settings | None
        Pre-loaded settings; None uses defaults.
    parent : QWidget | None
        Parent widget.

    """

    # Carries a background history-write error to the GUI thread.
    history_write_failed = Signal(str)

    def __init__(
        self,
        history: History,
        settings: Settings | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the main calculator window and wire up its views."""
        super().__init__(parent)
        self.setWindowTitle("Plain Text Fin Calc")
        self.history_write_failed.connect(self._show_history_write_error)
        self.setMinimumSize(360, 560)

        self._history = history
        self._settings = settings or Settings()
        self._history.trim_to(self._settings.max_history_entries)
        self._builder = ExpressionBuilder()
        # The RPN stack is kept in memory only, like unfinished algebraic
        # input; it starts empty at every launch.
        self._rpn = RpnStack()
        self._write_pool = ThreadPoolExecutor(max_workers=1)
        self._menus = build_menu_bar(
            self,
            MenuBarCallbacks(
                export_history=self._on_export_history,
                clear_history=self._on_clear_history,
                open_settings=self._on_open_settings,
                show_about=lambda: show_about(self),
                show_shortcuts=lambda: show_shortcuts(
                    self,
                    self._settings.input_mode,
                ),
            ),
        )

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self._tape = TapeView()
        self._tape.result_clicked.connect(self._on_result_clicked)
        self._tape.clear_history_requested.connect(self._on_clear_history)
        layout.addWidget(self._tape, stretch=6)

        self._display = DisplayView()
        layout.addWidget(self._display, stretch=1)

        self._keypad = KeypadView()
        self._keypad.token_pressed.connect(self._on_token)
        self._keypad.evaluate_pressed.connect(self._on_evaluate)
        self._keypad.clear_pressed.connect(self._on_clear)
        self._keypad.backspace_pressed.connect(self._on_backspace)
        self._keypad.toggle_sign_pressed.connect(self._on_toggle_sign)
        self._keypad.swap_pressed.connect(self._on_swap)
        self._keypad.drop_pressed.connect(self._on_drop)
        layout.addWidget(self._keypad, stretch=4)

        self._tape.set_decimal_places(self._settings.decimal_places)
        self._apply_theme_styles()
        self._tape.load_entries(self._history.entries)
        self._apply_input_mode()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        """Forward keyboard input to the keypad or actions."""
        key = event.key()
        text = event.text()

        if key in {Qt.Key.Key_Return, Qt.Key.Key_Enter}:
            self._on_evaluate()
            return

        if key == Qt.Key.Key_Escape:
            self._on_clear()
        elif key == Qt.Key.Key_Backspace:
            self._on_backspace()
        elif text:
            self._keypad.map_key_press(text)

        self._refresh_display()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Wait for queued history writes before closing."""
        self._write_pool.shutdown(wait=True)
        super().closeEvent(event)

    def _is_rpn(self) -> bool:
        """Return whether keys go to the RPN stack instead of the builder."""
        return self._settings.input_mode == "rpn"

    def _apply_input_mode(self) -> None:
        """Show the keypad and display of the current input mode."""
        self._keypad.set_input_mode(self._settings.input_mode)
        self._display.set_rpn_mode(self._is_rpn())
        self._refresh_display()

    def _run_rpn(self, action: Callable[[RpnStack], RpnStep]) -> None:
        """Apply one RPN key or tape reuse and show the outcome.

        - The status line is cleared first, for every key.
        - A refused key shows its message and changes nothing else.
        - A calculating key adds its tape line and saves history off the GUI
          thread; the stack keeps the result even if that write fails.
        """
        self._display.clear_status()
        try:
            step = action(self._rpn)
        except EvaluationError as err:
            self._display.set_status(str(err))
            return
        if step.record is not None:
            entry = HistoryEntry(
                expression=step.record.expression,
                result=step.record.result,
                timestamp=datetime.now(tz=UTC),
                rpn_input=step.record.rpn_input,
            )
            self._history.append(entry)
            self._tape.add_entry(entry)
            self._persist_history()
        self._rpn = step.stack
        self._refresh_display()

    def _press_rpn(self, key: str) -> None:
        """Press one keypad key on the RPN stack."""
        self._run_rpn(lambda stack: stack.press(key))

    def _on_token(self, symbol: str) -> None:
        if self._is_rpn():
            self._press_rpn(symbol)
            return
        self._display.clear_status()
        if not self._builder.add_symbol(symbol):
            self._display.set_status(f"Invalid input: {symbol}")
        self._refresh_display()

    def _on_evaluate(self) -> None:
        if self._is_rpn():
            self._press_rpn("enter")
            return
        symbols = self._builder.symbol_list()
        if not symbols:
            return
        try:
            result = evaluate(symbols)
        except EvaluationError as err:
            self._display.set_status(str(err))
            return

        result_str = result_text(result)
        expression_str = self._builder.to_display()
        entry = HistoryEntry(
            expression=expression_str,
            result=result_str,
            timestamp=datetime.now(tz=UTC),
        )
        self._history.append(entry)
        self._tape.add_entry(entry)
        self._persist_history()

        self._builder.clear()
        self._builder.insert_result(result_str)
        self._display.clear_status()
        self._display.set_expression(
            format_result(result_str, self._settings.decimal_places),
        )

    def _on_clear(self) -> None:
        if self._is_rpn():
            self._press_rpn("C")
            return
        self._builder.clear()
        self._display.clear_status()
        self._refresh_display()

    def _on_backspace(self) -> None:
        if self._is_rpn():
            self._press_rpn("backspace")
            return
        self._builder.backspace()
        self._refresh_display()

    def _on_toggle_sign(self) -> None:
        if self._is_rpn():
            self._press_rpn("sign")
            return
        self._builder.toggle_sign()
        self._refresh_display()

    def _on_swap(self) -> None:
        self._press_rpn("swap")

    def _on_drop(self) -> None:
        self._press_rpn("drop")

    def _on_result_clicked(self, result: str) -> None:
        if self._is_rpn():
            self._run_rpn(lambda stack: stack.reuse(result))
            return
        self._builder.insert_result(result)
        self._display.clear_status()
        self._refresh_display()

    def _on_clear_history(self) -> None:
        answer = QMessageBox.question(
            self,
            "Clear History",
            "Clear all history?\n\n"
            "This removes every saved calculation from the tape.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._history.clear_all()
        self._tape.clear_tape()
        self._persist_history()

    def _on_export_history(self) -> None:
        """Export history using the saved layout for plain text."""
        text_filter = "Plain Text Tape (*.txt)"
        selected_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export History",
            str(EXPORTS_DIR / "history"),
            f"CSV Files (*.csv);;{text_filter}",
        )
        if not selected_path:
            return

        export_path = Path(selected_path)
        is_text = selected_filter == text_filter
        suffix = ".txt" if is_text else ".csv"

        try:
            if export_path.suffix.lower() != suffix:
                export_path = export_path.with_suffix(suffix)
                if export_path.exists():
                    reply = QMessageBox.question(
                        self,
                        "Replace File",
                        f"Replace the existing file?\n{export_path}",
                        QMessageBox.StandardButton.Yes
                        | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No,
                    )
                    if reply != QMessageBox.StandardButton.Yes:
                        return
            if is_text:
                write_history_text(
                    self._history,
                    export_path,
                    self._settings.text_tape,
                )
            else:
                write_history_csv(self._history, export_path)
        except OSError as err:
            self.statusBar().showMessage(f"Export failed: {err}")
            return

        self._display.clear_status()
        self.statusBar().showMessage(f"Exported history to {export_path}")

    def _on_open_settings(self) -> None:
        """Open the Settings dialog and apply changes on OK."""
        dialog = SettingsDialog(
            self._settings, self, entries=self._history.entries
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self._apply_settings(dialog.selected_settings())

    def _apply_settings(self, new_settings: Settings) -> None:
        """Apply and persist new settings, restyling and trimming live.

        A changed input mode discards the unfinished input of both modes and
        clears the status line; history is kept. Settings apply in memory
        first, so this happens even when the settings file cannot be written.
        """
        mode_changed = new_settings.input_mode != self._settings.input_mode
        self._settings = new_settings

        self._apply_theme_styles()

        self._history.trim_to(new_settings.max_history_entries)
        self._tape.set_decimal_places(new_settings.decimal_places)
        self._tape.clear_tape()
        self._tape.load_entries(self._history.entries)
        self._persist_history()

        try:
            write_settings(new_settings, SETTINGS_FILE)
        except OSError as err:
            self.statusBar().showMessage(f"Saving settings failed: {err}")

        if mode_changed:
            self._builder.clear()
            self._rpn = RpnStack()
            self._display.clear_status()
        self._apply_input_mode()

    def _apply_theme_styles(self) -> None:
        """Re-apply the current theme to app palette and styled views."""
        app = QApplication.instance()
        if isinstance(app, QApplication):
            apply_theme(app, self._settings.theme)
        colors = get_theme(self._settings.theme)
        self.statusBar().setStyleSheet(
            f"font-size: 14px; color: {colors.statusbar_fg};"
            f" background: {colors.statusbar_bg}; padding: 3px 8px;",
        )
        self._display.restyle(colors)
        self._tape.restyle(colors)

    def _persist_history(self) -> None:
        """Snapshot entries and write to disk off the GUI thread."""
        snapshot = History(entries=list(self._history.entries))
        future = self._write_pool.submit(write_history, snapshot, HISTORY_FILE)
        future.add_done_callback(self._report_history_write)

    def _report_history_write(self, future: Future[None]) -> None:
        """Forward a failed write from the worker thread to the GUI."""
        error = future.exception()
        if error is not None:
            self.history_write_failed.emit(str(error))

    def _show_history_write_error(self, message: str) -> None:
        self.statusBar().showMessage(f"Saving history failed: {message}")

    def _refresh_display(self) -> None:
        """Show the pending input of the current input mode.

        In RPN mode the X line shows the number as typed, or X rounded for
        display, and the Y line shows the register above it.
        """
        if not self._is_rpn():
            self._display.set_expression(self._builder.to_display())
            return
        places = self._settings.decimal_places
        stack = self._rpn
        if stack.entry is not None:
            shown_x = stack.entry
        elif stack.levels:
            shown_x = format_result(stack.levels[0], places)
        else:
            shown_x = ""
        shown_y = stack.visible_y
        self._display.set_expression(shown_x)
        self._display.set_y(
            None if shown_y is None else format_result(shown_y, places),
        )
