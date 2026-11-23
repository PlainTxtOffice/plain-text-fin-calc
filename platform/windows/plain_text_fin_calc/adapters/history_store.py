"""JSON file persistence for calculator history.

Reads and writes HistoryEntry lists to a JSON file.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING

from plain_text_fin_calc.domains.calc.history import History, HistoryEntry

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


def _read_rpn_input(raw: object) -> str | None:
    """Return saved RPN keys, or None for anything but a non-empty string.

    A missing, null, empty, or wrongly typed value marks an algebraic entry;
    it never invalidates the entry or the file.
    """
    return raw if isinstance(raw, str) and raw else None


def _load_entries(raw_entries: object) -> list[HistoryEntry]:
    """Convert decoded JSON into history entries."""
    if not isinstance(raw_entries, list):
        msg = "History JSON root must be a list"
        raise TypeError(msg)

    entries: list[HistoryEntry] = []
    for entry in raw_entries:
        if not isinstance(entry, dict):
            msg = "History entries must be objects"
            raise TypeError(msg)
        entries.append(
            HistoryEntry(
                expression=entry["expression"],
                result=entry["result"],
                timestamp=datetime.fromisoformat(entry["timestamp"]),
                rpn_input=_read_rpn_input(entry.get("rpn_input")),
            ),
        )
    return entries


def load_history(path: Path) -> History:
    """Load history entries from a JSON file.

    Parameters
    ----------
    path : Path
        Path to the history JSON file.

    Returns
    -------
    History
        Loaded history, or an empty History if the file is missing or corrupt.

    """
    if not path.exists():
        return History()
    try:
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            return History()
        raw_entries = json.loads(text)
        entries = _load_entries(raw_entries)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        logger.exception("Failed to load history from %s", path)
        return History()
    return History(entries=entries)


def write_history(history: History, path: Path) -> None:
    """Write all history entries to a JSON file.

    Log and propagate write failures so callers can report unsaved results.
    The "rpn_input" key is written only for RPN entries, so algebraic
    entries keep their earlier three-key form.

    Parameters
    ----------
    history : History
        The history model to persist.
    path : Path
        Path to the history JSON file.

    """
    path.parent.mkdir(parents=True, exist_ok=True)
    raw_entries = [
        {
            "expression": entry.expression,
            "result": entry.result,
            "timestamp": entry.timestamp.isoformat(),
        }
        | ({"rpn_input": entry.rpn_input} if entry.rpn_input else {})
        for entry in history.entries
    ]
    try:
        path.write_text(
            json.dumps(raw_entries, indent=2),
            encoding="utf-8",
        )
    except OSError:
        logger.exception("Failed to write history to %s", path)
        raise
