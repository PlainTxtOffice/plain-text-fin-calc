"""User-configurable application settings."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from plain_text_fin_calc.domains.calc.history import DEFAULT_HISTORY_CAP
from plain_text_fin_calc.domains.calc.text_tape import TextTapeFormat

Theme = Literal["dark", "light"]
THEMES: tuple[Theme, ...] = ("dark", "light")
DEFAULT_THEME: Theme = "dark"

InputMode = Literal["algebraic", "rpn"]
INPUT_MODES: tuple[InputMode, ...] = ("algebraic", "rpn")
DEFAULT_INPUT_MODE: InputMode = "algebraic"


@dataclass
class Settings:
    """User-configurable application settings.

    Parameters
    ----------
    decimal_places : int | None
        Decimal places shown for results; None means full precision.
    theme : Theme
        Theme name, "dark" or "light".
    max_history_entries : int | None
        Maximum retained history entries; None means unlimited.
    text_tape : TextTapeFormat
        Date and time layout for plain text exports.
    input_mode : InputMode
        How calculations are entered: "algebraic" (the default) or "rpn"
        (reverse Polish notation).

    """

    decimal_places: int | None = None
    theme: Theme = DEFAULT_THEME
    max_history_entries: int | None = DEFAULT_HISTORY_CAP
    text_tape: TextTapeFormat = field(default_factory=TextTapeFormat)
    input_mode: InputMode = DEFAULT_INPUT_MODE
