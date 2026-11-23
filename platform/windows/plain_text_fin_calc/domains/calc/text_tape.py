"""Format saved calculations as a readable plain text tape."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from plain_text_fin_calc.domains.calc.formatting import format_history_line

if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import datetime

    from plain_text_fin_calc.domains.calc.history import HistoryEntry

DATE_PATTERNS = {
    "YYYY-MM-DD": "%Y-%m-%d",
    "MM/DD/YYYY": "%m/%d/%Y",
    "DD/MM/YYYY": "%d/%m/%Y",
}


@dataclass(frozen=True, kw_only=True)
class TextTapeFormat:
    """Choose the time zone and timestamp layout for a text tape."""

    date_headings: bool = True
    entry_times: bool = True
    time_zone: str = "local"
    date_format: str = "YYYY-MM-DD"
    twelve_hour: bool = False
    seconds: bool = False
    utc_offset: bool = False

    def format_time(self, timestamp: datetime) -> str:
        """Format an already converted timestamp in the chosen clock style."""
        hour = (
            str(timestamp.hour % 12 or 12)
            if self.twelve_hour
            else f"{timestamp.hour:02}"
        )
        clock = f"{hour}:{timestamp:%M}"
        if self.seconds:
            clock += f":{timestamp:%S}"
        if self.twelve_hour:
            clock += " AM" if timestamp.hour < 12 else " PM"  # noqa: PLR2004
        if self.utc_offset:
            clock += f" UTC{timestamp:%:z}"
        return clock


def format_text_tape(
    entries: Iterable[HistoryEntry],
    options: TextTapeFormat,
) -> str:
    """Render entries in tape order, preserving their full saved precision."""
    lines: list[str] = []
    previous_date = None
    zone = None if options.time_zone == "local" else ZoneInfo(options.time_zone)
    for entry in entries:
        line = format_history_line(entry, None)
        if options.date_headings or options.entry_times:
            stamp = entry.timestamp.astimezone(zone)
            if options.date_headings and stamp.date() != previous_date:
                if lines:
                    lines.append("")
                previous_date = stamp.date()
                lines.append(stamp.strftime(DATE_PATTERNS[options.date_format]))
            if options.entry_times:
                line = f"{options.format_time(stamp)}  {line}"
        lines.append(line)
    lines.append("")
    return "\n".join(lines)
