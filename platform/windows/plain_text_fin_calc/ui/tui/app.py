"""Compose and launch the Textual calculator."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.widgets import Footer, Header, Input, RichLog, Static

from plain_text_fin_calc.domains.calc.errors import EvaluationError
from plain_text_fin_calc.domains.calc.formatting import (
    format_history_line,
    format_stack_lines,
)

if TYPE_CHECKING:
    from plain_text_fin_calc.application.session import CalculatorSession

_IDLE_TEXT = "Enter an expression and press Enter."
_PLACEHOLDER = "Example: 0.1 + 0.2 or log(100)"
_RPN_IDLE_TEXT = (
    "Enter numbers and operators separated by spaces and press Enter."
)
_RPN_PLACEHOLDER = "Example: 3 4 + or 100 log"


class CalculatorApp(App[None]):
    """Present expression entry, results, and persisted calculation history.

    The input mode saved in the settings is read at start: algebraic mode
    takes expressions, RPN mode takes lines of space-separated tokens.
    """

    TITLE = "Plain Text Fin Calc"
    CSS = """
    #tape { height: 1fr; border: round $primary; }
    #result { height: auto; min-height: 3; padding: 1; }
    #expression { margin: 0 1 1 1; }
    """
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
        Binding("escape", "clear_input", "Clear input"),
    ]

    def __init__(self, session: CalculatorSession) -> None:
        """Use a loaded session without opening files during composition."""
        super().__init__()
        self.session = session
        self._rpn_mode = session.settings.input_mode == "rpn"
        self.theme = (
            "textual-light"
            if session.settings.theme == "light"
            else "textual-dark"
        )

    def compose(self) -> ComposeResult:
        """Create the history tape, result area, and expression field."""
        yield Header()
        yield RichLog(id="tape", wrap=True, markup=False, highlight=False)
        yield Static(self._idle_text(), id="result", markup=False)
        yield Input(
            placeholder=_RPN_PLACEHOLDER if self._rpn_mode else _PLACEHOLDER,
            id="expression",
        )
        yield Footer()

    def _idle_text(self) -> str:
        """Return the result-area text shown when nothing is pending.

        In RPN mode a non-empty stack is shown on one line, highest level
        first; otherwise the entry hint for the input mode is shown.
        """
        if not self._rpn_mode:
            return _IDLE_TEXT
        lines = format_stack_lines(
            self.session.rpn,
            self.session.settings.decimal_places,
        )
        return "  ".join(lines) if lines else _RPN_IDLE_TEXT

    def _refresh_tape(self) -> None:
        tape = self.query_one("#tape", RichLog)
        tape.clear()
        decimal_places = self.session.settings.decimal_places
        for entry in self.session.history.entries:
            tape.write(format_history_line(entry, decimal_places))

    def on_mount(self) -> None:
        """Display the saved tape and focus expression entry."""
        self._refresh_tape()
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Delegate calculation and persistence, keeping errors in the UI.

        RPN mode shows the stack after the line, or "Stack is empty.". A
        failed line or save shows the error and changes nothing else.
        """
        output = self.query_one("#result", Static)
        try:
            if self._rpn_mode:
                self.session.run_rpn_line(event.value)
                lines = format_stack_lines(
                    self.session.rpn,
                    self.session.settings.decimal_places,
                )
                shown = "  ".join(lines) if lines else "Stack is empty."
            else:
                shown = f"Result: {self.session.calculate(event.value)}"
        except (EvaluationError, OSError) as error:
            output.update(f"Error: {error}")
            return
        output.update(shown)
        self._refresh_tape()
        event.input.clear()

    def action_clear_input(self) -> None:
        """Clear expression entry without deleting saved history.

        The RPN stack is kept; it is cleared with the word ``clear``.
        """
        self.query_one(Input).clear()
        self.query_one("#result", Static).update(self._idle_text())


def run_app(session: CalculatorSession) -> int:
    """Run the terminal interface and return its process exit status."""
    app = CalculatorApp(session)
    app.run()
    return app.return_code or 0
