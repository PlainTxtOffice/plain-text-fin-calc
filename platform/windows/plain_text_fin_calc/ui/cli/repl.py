"""Read expressions repeatedly and present saved calculation results."""

from __future__ import annotations

from typing import TYPE_CHECKING

import typer

from plain_text_fin_calc.domains.calc.errors import EvaluationError
from plain_text_fin_calc.domains.calc.formatting import format_stack_lines
from plain_text_fin_calc.ui.cli.commands import show_history
from plain_text_fin_calc.ui.cli.settings.commands import run_config

if TYPE_CHECKING:
    from plain_text_fin_calc.application.session import CalculatorSession

_PROMPT = "fin-calc> "
_RPN_PROMPT = "fin-calc rpn> "
_HELP = (
    "Enter an expression, such as 125 * 1.08, and press Enter.\n"
    "Supports +, -, *, /, ^, parentheses, and log(x) (base 10).\n"
    "Expressions need no quotes; negative numbers need no -- prefix.\n"
    "history: show saved calculations; help: show this help.\n"
    "config: show settings; config <setting> <value>: save a change.\n"
    "config input_mode rpn: switch to RPN entry (reverse Polish notation).\n"
    "exit or quit: leave the prompt. Ctrl+C or end of input also exits.\n"
    "Successful calculations are saved with full precision."
)
_RPN_HELP = (
    "Enter numbers and operators separated by spaces, such as 3 4 +, "
    "and press Enter.\n"
    "Operators: + - * / ^. Words: enter, swap, drop, chs (change sign), "
    "log (base 10), clear.\n"
    "Write negative numbers with the sign attached, such as -5; "
    "a lone - subtracts.\n"
    "Each line shows the stack afterwards. A line with an error changes "
    "nothing.\n"
    "history: show saved calculations; help: show this help.\n"
    "config: show settings; config input_mode algebraic: switch to "
    "algebraic entry.\n"
    "exit or quit: leave the prompt. Ctrl+C or end of input also exits.\n"
    "Successful calculations are saved with full precision."
)


def _is_rpn(session: CalculatorSession) -> bool:
    """Return whether the prompt currently reads RPN token lines."""
    return session.settings.input_mode == "rpn"


def _run_calculation(session: CalculatorSession, line: str) -> None:
    """Calculate one input line in the session's input mode and print it.

    Algebraic mode prints the result. RPN mode prints the stack after the
    line, or "Stack is empty.". Errors go to stderr and change nothing.
    """
    try:
        if _is_rpn(session):
            session.run_rpn_line(line)
            lines = format_stack_lines(
                session.rpn,
                session.settings.decimal_places,
            )
            output = "\n".join(lines) if lines else "Stack is empty."
        else:
            output = session.calculate(line)
    except (EvaluationError, OSError) as error:
        typer.echo(f"Error: {error}", err=True)
    else:
        typer.echo(output)


def _read_expressions(session: CalculatorSession) -> None:
    """Read commands until exit, saving results and reporting errors.

    The prompt follows the saved input mode, read again before every line.
    """
    while True:
        prompt = _RPN_PROMPT if _is_rpn(session) else _PROMPT
        expression = input(prompt).strip()
        if not expression:
            continue
        command = expression.lower()
        if command in {"exit", "quit"}:
            return
        if command == "help":
            typer.echo(_RPN_HELP if _is_rpn(session) else _HELP)
        elif command == "history":
            show_history(session)
        elif command.split(maxsplit=1)[0] == "config":
            run_config(session, command.split()[1:])
        else:
            _run_calculation(session, expression)


def run_repl(session: CalculatorSession) -> int:
    """Run a persistent prompt until exit, EOF, or Ctrl+C.

    Each successful calculation is saved immediately through the session.
    Invalid expressions and failed saves print an error and allow retrying.
    Normal exit, EOF, and Ctrl+C return status zero.
    """
    typer.echo("Plain Text Fin Calc — type help for commands, exit to quit.")
    try:
        _read_expressions(session)
    except (EOFError, KeyboardInterrupt):
        typer.echo()
    return 0
