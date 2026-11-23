"""Four-level reverse Polish (RPN) stack for the calculator domain.

- Owns the stack rules: lift, ENTER, swap, drop, sign change, and the
  keystroke log that is stored with each calculation.
- All arithmetic goes through the algebraic evaluator, so a result equals
  the algebraic result of the same expression exactly.
- Performs no I/O and holds no interface state.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from plain_text_fin_calc.domains.calc.errors import EvaluationError
from plain_text_fin_calc.domains.calc.evaluator import evaluate, result_text
from plain_text_fin_calc.domains.calc.expression import DIGITS, OPERATORS
from plain_text_fin_calc.domains.calc.parsing import (
    MAX_EXPRESSION_LENGTH,
    MAX_EXPRESSION_TOKENS,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

MAX_LEVELS = 4
MAX_ENTRY_DIGITS = 28
MAX_KEYS = 64

_TRUNCATED = "..."
_TOO_FEW_OPERANDS = "Too few operands"
_ZERO_TEXT = re.compile(r"-?(0+\.?0*|\.0+)([eE][+-]?[0-9]+)?")
_NUMBER_TEXT = re.compile(r"-?([0-9]+\.?[0-9]*|\.[0-9]+)")
# Words accepted in a text line, mapped to the keypad key they press.
_WORD_KEYS = {
    "enter": "enter",
    "swap": "swap",
    "drop": "drop",
    "log": "log",
    "chs": "sign",
    "clear": "C",
}


def result_string(tokens: Sequence[str]) -> str:
    """Return the string algebraic mode stores for the same tokens.

    Raises EvaluationError with the evaluator's own message.
    """
    return result_text(evaluate(list(tokens)))


def is_zero_text(text: str) -> bool:
    """Return whether the text spells zero.

    Covers plain and exponent spellings, such as 0, -0, 0., -0.00 and 0E+27.
    """
    return _ZERO_TEXT.fullmatch(text) is not None


def canon(text: str) -> str:
    """Return the stored form of a typed or reused number.

    - Zero is decided by its text and always stored as "0", so no negative
      zero enters the stack from typing or reuse.
    - Other numbers take the stored result spelling, without trailing
      zeros. Negating twice makes the evaluator round a reused number of
      more than 28 digits, so every stack value fits the working precision
      and a later sign change is exact.
    - Raises EvaluationError when the text is not a number.
    """
    if is_zero_text(text):
        return "0"
    return result_string(["-", "(", "-", text, ")"])


def _count_digits(text: str) -> int:
    """Count the digit characters, ignoring a sign and a decimal point."""
    return sum(char in DIGITS for char in text)


def _push(levels: tuple[str, ...], value: str) -> tuple[str, ...]:
    """Put a value in X and lift the rest; the old top level is lost."""
    return (value, *levels)[:MAX_LEVELS]


def _log_key(keys: tuple[str, ...], token: str) -> tuple[str, ...]:
    """Append a key to the log, keeping only the newest keys.

    A shortened log starts with "..." in place of the keys that were dropped.
    """
    logged = (*keys, token)
    if len(logged) <= MAX_KEYS:
        return logged
    return (_TRUNCATED, *logged[2:])


@dataclass(frozen=True)
class RpnRecord:
    """Describe one tape line produced by an RPN calculation.

    - ``expression`` is the equivalent algebraic expression, such as "3 + 4".
    - ``result`` is the full-precision result string.
    - ``rpn_input`` lists the accepted keys that led to the result.
    """

    expression: str
    result: str
    rpn_input: str


@dataclass(frozen=True)
class RpnStep:
    """Hold the stack after an accepted key and its tape line, if any."""

    stack: RpnStack
    record: RpnRecord | None = None


@dataclass(frozen=True)
class RpnStack:
    """Represent the RPN stack (X, Y, Z, T) and the number being typed.

    - Instances are immutable: every key returns a new stack or raises
      EvaluationError, so a refused key leaves the caller's stack as it was.
    - ``levels`` lists X first and holds zero to four number strings; levels
      can be empty, so operands the user never entered cannot reach the tape.
    - ``entry`` is the number being typed; it is shown as X while present.
    - ``lift`` is False only directly after ENTER, when the next number
      overwrites X.
    - ``keys`` logs the accepted keys since the last tape line.
    """

    levels: tuple[str, ...] = ()
    entry: str | None = None
    lift: bool = True
    keys: tuple[str, ...] = ()

    @property
    def visible_y(self) -> str | None:
        """Return the value for the Y line, or None when there is none.

        While a number is being typed it is the top of the stack; otherwise
        it is the second level.
        """
        index = 0 if self.entry is not None else 1
        return self.levels[index] if len(self.levels) > index else None

    def press(self, key: str) -> RpnStep:
        """Apply one keypad key and return the new stack.

        - Keys: "0" to "9", ".", "backspace", "sign", "enter", "swap",
          "drop", "C", "log", "+", "-", "*", "/" and "^"; "=" acts as "enter".
        - Operators and log return a tape record with the step.
        - Raises EvaluationError("Too few operands"), the evaluator's own
          message, or "Invalid input: <key>" for a refused or unknown key.
        """
        if key in DIGITS:
            return RpnStep(self._add_digit(key))
        if key in OPERATORS:
            return self._calc_binary(key)
        if key == "log":
            return self._calc_log()
        moves = {
            ".": self._add_point,
            "backspace": self._backspace,
            "sign": self._toggle_sign,
            "enter": self._enter,
            "=": self._enter,
            "swap": self._swap,
            "drop": self._drop,
            "C": self._clear,
        }
        move = moves.get(key)
        if move is None:
            msg = f"Invalid input: {key}"
            raise EvaluationError(msg)
        return RpnStep(move())

    def reuse(self, value: str) -> RpnStep:
        """Put a saved result in X without creating a tape line.

        A number being typed is discarded. Directly after ENTER the value
        overwrites X; otherwise the stack lifts. Raises EvaluationError when
        the value is not a number.
        """
        number = canon(value)
        levels = (
            _push(self.levels, number)
            if self.lift
            else (number, *self.levels[1:])
        )
        return RpnStep(RpnStack(levels, keys=_log_key(self.keys, number)))

    def number(self, text: str) -> RpnStep:
        """Enter a complete number written as text.

        Accepts an optional leading minus, digits, and one decimal point,
        with at most 28 digits; exponent notation is refused. The effect
        equals typing the number and ending it. Raises
        EvaluationError("Invalid input: <text>") for anything else.
        """
        if (
            _NUMBER_TEXT.fullmatch(text) is None
            or _count_digits(text) > MAX_ENTRY_DIGITS
        ):
            msg = f"Invalid input: {text}"
            raise EvaluationError(msg)
        return self.reuse(text)

    def _start_entry(self, text: str) -> RpnStack:
        """Begin typing a number, overwriting an ENTER duplicate in X."""
        levels = self.levels if self.lift else self.levels[1:]
        return replace(self, levels=levels, entry=text, lift=True)

    def _add_digit(self, digit: str) -> RpnStack:
        """Type a digit, refusing a twenty-ninth so numbers stay exact."""
        if self.entry is None:
            return self._start_entry(digit)
        if _count_digits(self.entry) >= MAX_ENTRY_DIGITS:
            msg = f"Invalid input: {digit}"
            raise EvaluationError(msg)
        return replace(self, entry=self.entry + digit)

    def _add_point(self) -> RpnStack:
        """Type the decimal point, refusing a second one."""
        if self.entry is None:
            return self._start_entry("0.")
        if "." in self.entry:
            msg = "Invalid input: ."
            raise EvaluationError(msg)
        return replace(self, entry=self.entry + ".")

    def _backspace(self) -> RpnStack:
        """Delete the last typed character; a number with no digit ends."""
        if self.entry is None:
            return self
        rest = self.entry[:-1]
        return replace(self, entry=rest if _count_digits(rest) else None)

    def _toggle_sign(self) -> RpnStack:
        """Change the sign of the typed number, or of X when none is typed.

        Changing the sign of X is logged as CHS; a sign typed with a number
        is part of that number. Zero stays "0".
        """
        if self.entry is not None:
            entry = self.entry
            toggled = entry[1:] if entry.startswith("-") else "-" + entry
            return replace(self, entry=toggled)
        if not self.levels:
            return self
        x = self.levels[0]
        x = "0" if is_zero_text(x) else result_string(["-", x])
        return replace(
            self,
            levels=(x, *self.levels[1:]),
            lift=True,
            keys=_log_key(self.keys, "CHS"),
        )

    def _clear(self) -> RpnStack:
        """Clear the typed number first; with none, clear the whole stack."""
        if self.entry is not None:
            return replace(self, entry=None)
        return RpnStack()

    def _terminate(self) -> RpnStack:
        """Push the typed number, if any, so every stack key sees it as X."""
        if self.entry is None:
            return self
        number = canon(self.entry)
        return replace(
            self,
            levels=_push(self.levels, number),
            entry=None,
            keys=_log_key(self.keys, number),
        )

    def _require(self, count: int) -> RpnStack:
        """Return the stack with the typed number pushed and enough levels.

        Raises EvaluationError("Too few operands") otherwise.
        """
        stack = self._terminate()
        if len(stack.levels) < count:
            raise EvaluationError(_TOO_FEW_OPERANDS)
        return stack

    def _enter(self) -> RpnStack:
        """Duplicate X and disable lift, so the next number overwrites X."""
        stack = self._require(1)
        return replace(
            stack,
            levels=_push(stack.levels, stack.levels[0]),
            lift=False,
            keys=_log_key(stack.keys, "ENTER"),
        )

    def _swap(self) -> RpnStack:
        """Exchange X and Y."""
        stack = self._require(2)
        x, y, *rest = stack.levels
        return replace(
            stack,
            levels=(y, x, *rest),
            lift=True,
            keys=_log_key(stack.keys, "SWAP"),
        )

    def _drop(self) -> RpnStack:
        """Discard X; a full stack repeats its top level as it drops."""
        stack = self._require(1)
        rest = stack.levels[1:]
        if len(stack.levels) == MAX_LEVELS:
            rest = (*rest, stack.levels[-1])
        return replace(
            stack,
            levels=rest,
            lift=True,
            keys=_log_key(stack.keys, "DROP"),
        )

    def _calc_binary(self, operator: str) -> RpnStep:
        """Replace Y and X with ``Y operator X`` and record the tape line."""
        stack = self._require(2)
        x, y, *rest = stack.levels
        result = result_string([y, operator, x])
        if len(stack.levels) == MAX_LEVELS:
            rest.append(stack.levels[-1])
        return RpnStep(
            RpnStack((result, *rest)),
            RpnRecord(
                f"{y} {operator} {x}",
                result,
                " ".join(_log_key(stack.keys, operator)),
            ),
        )

    def _calc_log(self) -> RpnStep:
        """Replace X with its base-10 logarithm and record the tape line."""
        stack = self._require(1)
        x = stack.levels[0]
        result = result_string(["log", "(", x, ")"])
        return RpnStep(
            RpnStack((result, *stack.levels[1:])),
            RpnRecord(
                f"log ( {x} )",
                result,
                " ".join(_log_key(stack.keys, "LOG")),
            ),
        )


def run_line(
    stack: RpnStack,
    line: str,
) -> tuple[RpnStack, tuple[RpnRecord, ...]]:
    """Apply a line of whitespace-separated RPN tokens to a stack.

    - Tokens are numbers, the operators + - * / ^, and the words enter, swap,
      drop, chs, log and clear in any letter case.
    - A negative number carries its sign, such as -5; a lone - subtracts.
    - Returns the final stack and the tape records in order.
    - A line is all-or-nothing: any refused token raises EvaluationError and
      the caller's stack is unchanged.
    - Length and token limits match algebraic text input.
    """
    if len(line) > MAX_EXPRESSION_LENGTH:
        msg = f"Expression exceeds {MAX_EXPRESSION_LENGTH} characters"
        raise EvaluationError(msg)
    tokens = line.split()
    if not tokens:
        msg = "Empty expression"
        raise EvaluationError(msg)
    if len(tokens) > MAX_EXPRESSION_TOKENS:
        msg = f"Expression exceeds {MAX_EXPRESSION_TOKENS} tokens"
        raise EvaluationError(msg)
    records: list[RpnRecord] = []
    for token in tokens:
        key = _WORD_KEYS.get(token.lower())
        if key is not None:
            step = stack.press(key)
        elif token in OPERATORS:
            step = stack.press(token)
        else:
            step = stack.number(token)
        stack = step.stack
        if step.record is not None:
            records.append(step.record)
    return stack, tuple(records)
