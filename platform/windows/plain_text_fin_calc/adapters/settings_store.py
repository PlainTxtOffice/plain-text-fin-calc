"""JSON file persistence for application settings.

Invalid or missing files always produce default Settings; loading
never raises to the caller.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from typing import TYPE_CHECKING
from zoneinfo import available_timezones

from plain_text_fin_calc.config.settings import (
    DEFAULT_INPUT_MODE,
    DEFAULT_THEME,
    THEMES,
    InputMode,
    Settings,
    Theme,
)
from plain_text_fin_calc.domains.calc.formatting import MAX_DECIMAL_PLACES
from plain_text_fin_calc.domains.calc.history import (
    MAX_HISTORY_CAP,
    MIN_HISTORY_CAP,
)
from plain_text_fin_calc.domains.calc.text_tape import (
    DATE_PATTERNS,
    TextTapeFormat,
)

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


def _read_optional_bounded_int(
    raw: object,
    minimum: int,
    maximum: int,
) -> int | None:
    """Return raw as an int clamped to maximum, or None if invalid.

    Parameters
    ----------
    raw : object
        The raw JSON value to validate.
    minimum : int
        The smallest acceptable value; values below this are rejected.
    maximum : int
        The largest acceptable value; values above this are clamped down
        to it rather than rejected.

    Returns
    -------
    int | None
        The value (clamped to `maximum`) if `raw` is an int >= `minimum`,
        else None.

    """
    if isinstance(raw, int) and not isinstance(raw, bool) and raw >= minimum:
        return min(raw, maximum)
    return None


def _read_history_cap(raw: dict) -> int | None:
    """Read the history cap, distinguishing absent, null, and invalid.

    Parameters
    ----------
    raw : dict
        The decoded settings JSON object.

    Returns
    -------
    int | None
        An explicit JSON ``null`` means unlimited (None); a missing or
        invalid value falls back to the default cap; valid ints are
        clamped to the maximum.

    """
    if "max_history_entries" not in raw:
        return Settings().max_history_entries
    value = raw["max_history_entries"]
    if value is None:
        return None
    validated = _read_optional_bounded_int(
        value,
        minimum=MIN_HISTORY_CAP,
        maximum=MAX_HISTORY_CAP,
    )
    if validated is None:
        return Settings().max_history_entries
    return validated


def _read_theme(raw: object) -> Theme:
    """Return raw as a known theme name, or the default theme.

    Parameters
    ----------
    raw : object
        The raw JSON value to validate.

    Returns
    -------
    Theme
        The matching theme name, else ``DEFAULT_THEME``.

    """
    for name in THEMES:
        if raw == name:
            return name
    return DEFAULT_THEME


def _read_input_mode(raw: object) -> InputMode:
    """Return "rpn" only for that exact saved string.

    A missing key, null, another type, or any other string gives the
    default mode, so settings files saved before the input mode existed load
    as algebraic.
    """
    return "rpn" if raw == "rpn" else DEFAULT_INPUT_MODE


def _read_text_tape(raw: object) -> TextTapeFormat:
    """Use each valid saved switch independently, including explicit false."""
    defaults = TextTapeFormat()
    if not isinstance(raw, dict):
        return defaults

    def flag(name: str, default: bool) -> bool:  # noqa: FBT001
        value = raw.get(name)
        return value if isinstance(value, bool) else default

    zone = raw.get("time_zone")
    date_format = raw.get("date_format")
    return TextTapeFormat(
        date_headings=flag("date_headings", defaults.date_headings),
        entry_times=flag("entry_times", defaults.entry_times),
        time_zone=zone
        if isinstance(zone, str)
        and zone != "local"
        and zone in available_timezones()
        else defaults.time_zone,
        date_format=date_format
        if isinstance(date_format, str) and date_format in DATE_PATTERNS
        else defaults.date_format,
        twelve_hour=flag("twelve_hour", defaults.twelve_hour),
        seconds=flag("seconds", defaults.seconds),
        utc_offset=flag("utc_offset", defaults.utc_offset),
    )


def load_settings(path: Path) -> Settings:
    """Load settings from a JSON file.

    Parameters
    ----------
    path : Path
        Path to the settings JSON file.

    Returns
    -------
    Settings
        Loaded settings; individual invalid fields fall back to their
        defaults, and a missing or corrupt file yields all defaults.

    """
    if not path.exists():
        return Settings()
    try:
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            return Settings()
        raw = json.loads(text)
    except OSError, ValueError:
        logger.exception("Failed to load settings from %s", path)
        return Settings()
    if not isinstance(raw, dict):
        logger.error("Settings JSON root must be an object: %s", path)
        return Settings()

    return Settings(
        decimal_places=_read_optional_bounded_int(
            raw.get("decimal_places"),
            minimum=0,
            maximum=MAX_DECIMAL_PLACES,
        ),
        theme=_read_theme(raw.get("theme")),
        max_history_entries=_read_history_cap(raw),
        text_tape=_read_text_tape(raw.get("text_tape")),
        input_mode=_read_input_mode(raw.get("input_mode")),
    )


def write_settings(settings: Settings, path: Path) -> None:
    """Write settings to a JSON file.

    Parameters
    ----------
    settings : Settings
        The settings to persist.
    path : Path
        Path to the settings JSON file.

    """
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = asdict(settings)
    try:
        path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    except OSError:
        logger.exception("Failed to write settings to %s", path)
        raise
