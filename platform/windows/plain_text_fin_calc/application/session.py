"""Coordinate text calculations with saved history and display settings."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from plain_text_fin_calc.adapters.history_store import (
    load_history,
    write_history,
)
from plain_text_fin_calc.adapters.settings_store import (
    load_settings,
    write_settings,
)
from plain_text_fin_calc.config.path_handler import HISTORY_FILE, SETTINGS_FILE
from plain_text_fin_calc.domains.calc.errors import EvaluationError
from plain_text_fin_calc.domains.calc.evaluator import evaluate, result_text
from plain_text_fin_calc.domains.calc.formatting import format_result
from plain_text_fin_calc.domains.calc.history import History, HistoryEntry
from plain_text_fin_calc.domains.calc.parsing import parse_expression
from plain_text_fin_calc.domains.calc.rpn_stack import RpnStack, run_line

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from plain_text_fin_calc.config.settings import Settings
    from plain_text_fin_calc.domains.calc.rpn_stack import RpnRecord


def _to_entries(records: Sequence[RpnRecord]) -> list[HistoryEntry]:
    """Map RPN tape records to timestamped history entries, in order."""
    return [
        HistoryEntry(
            record.expression,
            record.result,
            datetime.now(tz=UTC),
            record.rpn_input,
        )
        for record in records
    ]


@dataclass
class CalculatorSession:
    """Own the history, settings, and RPN stack for one running interface.

    The RPN stack lives only as long as the session; it is never saved.
    """

    history: History
    settings: Settings
    history_path: Path
    settings_path: Path = SETTINGS_FILE
    rpn: RpnStack = field(default_factory=RpnStack)

    def update_settings(self, settings: Settings) -> None:
        """Persist settings before applying them to this session.

        - History limits take effect at the next calculation or session load.
        - A changed input mode clears the RPN stack; history is kept.
        - A failed settings write leaves the active settings, the input mode,
          and the stack unchanged.
        """
        write_settings(settings, self.settings_path)
        if settings.input_mode != self.settings.input_mode:
            self.rpn = RpnStack()
        self.settings = settings

    def calculate(self, expression: str) -> str:
        """Evaluate and save an expression, returning its display result.

        Failed calculations or writes leave the in-memory history unchanged.
        Stored results retain full Decimal precision.
        """
        result = result_text(evaluate(parse_expression(expression)))
        entry = HistoryEntry(expression.strip(), result, datetime.now(tz=UTC))
        self._write_entries([entry])
        return format_result(result, self.settings.decimal_places)

    def run_rpn_line(self, line: str) -> None:
        """Apply a line of RPN tokens to the session stack and save results.

        - Each calculating token is saved as its own history entry with the
          keys that led to it, all in one write.
        - A line is all-or-nothing: a refused token (EvaluationError) or a
          failed write (OSError) leaves the stack and the history unchanged.
        """
        stack, records = run_line(self.rpn, line)
        self._write_entries(_to_entries(records))
        self.rpn = stack

    def calculate_rpn(self, line: str) -> str:
        """Run a line of RPN tokens on an empty stack and return the last X.

        - The session stack is neither read nor changed.
        - Calculations are saved as in ``run_rpn_line``; a line without a
          calculating token writes nothing.
        - Raises EvaluationError("Stack is empty") when the line leaves no
          number to return; nothing is saved then.
        """
        stack, records = run_line(RpnStack(), line)
        if not stack.levels:
            msg = "Stack is empty"
            raise EvaluationError(msg)
        self._write_entries(_to_entries(records))
        return format_result(stack.levels[0], self.settings.decimal_places)

    def _write_entries(self, entries: Sequence[HistoryEntry]) -> None:
        """Append entries under the history cap and write the file once.

        Nothing is written for an empty sequence. A failed write raises
        OSError and leaves the in-memory history unchanged.
        """
        if not entries:
            return
        updated = History(
            entries=list(self.history.entries),
            max_entries=self.settings.max_history_entries,
        )
        for entry in entries:
            updated.append(entry)
        write_history(updated, self.history_path)
        self.history.entries[:] = updated.entries


def load_session() -> CalculatorSession:
    """Load the same history and settings used by the graphical interface."""
    history = load_history(HISTORY_FILE)
    settings = load_settings(SETTINGS_FILE)
    history.trim_to(settings.max_history_entries)
    return CalculatorSession(history, settings, HISTORY_FILE, SETTINGS_FILE)
