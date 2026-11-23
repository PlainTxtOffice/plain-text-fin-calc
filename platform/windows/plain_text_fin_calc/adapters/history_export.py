"""Write calculator history to a user-selected export file."""

from __future__ import annotations

import csv
from typing import TYPE_CHECKING

from plain_text_fin_calc.domains.calc.text_tape import format_text_tape

if TYPE_CHECKING:
    from pathlib import Path

    from plain_text_fin_calc.domains.calc.history import History
    from plain_text_fin_calc.domains.calc.text_tape import TextTapeFormat


def write_history_csv(history: History, path: Path) -> None:
    """Write calculator history entries to a CSV file.

    - Columns are timestamp, expression, result and rpn_input; rpn_input
      holds the keys of an RPN calculation and is empty for algebraic entries.
    - Parent directories are created when needed.
    - Existing files are overwritten.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as export_file:
        writer = csv.writer(export_file)
        writer.writerow(["timestamp", "expression", "result", "rpn_input"])
        for entry in history.entries:
            writer.writerow(
                [
                    entry.timestamp.isoformat(),
                    entry.expression,
                    entry.result,
                    entry.rpn_input or "",
                ],
            )


def write_history_text(
    history: History,
    path: Path,
    options: TextTapeFormat,
) -> None:
    """Save a UTF-8 tape with LF line endings in the chosen layout.

    RPN entries are followed by their ``RPN input:`` line.
    """
    text = format_text_tape(history.entries, options)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
