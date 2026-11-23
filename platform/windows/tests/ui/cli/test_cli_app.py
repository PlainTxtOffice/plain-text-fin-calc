"""Exercise command parsing, launch selection, and persistent calculations."""

import subprocess
import sys

import pytest
from typer.testing import CliRunner

from plain_text_fin_calc.adapters.history_store import load_history
from plain_text_fin_calc.application.session import CalculatorSession
from plain_text_fin_calc.domains.calc.history import History
from plain_text_fin_calc.config.settings import Settings
from plain_text_fin_calc.ui.cli import app as cli_app
from plain_text_fin_calc.ui.cli import commands, launch


@pytest.fixture
def session(monkeypatch, tmp_path):
    session = CalculatorSession(
        History(), Settings(), tmp_path / "history.json"
    )
    monkeypatch.setattr(commands, "configure_logging", lambda: None)
    monkeypatch.setattr(commands, "load_session", lambda: session)
    return session


def test_calculate_and_history_share_saved_state(session):
    runner = CliRunner()
    result = runner.invoke(cli_app.app, ["--cli", "calculate", "0.1 + 0.2"])
    assert result.exit_code == 0, result.output
    assert result.stdout == "0.3\n"
    assert load_history(session.history_path).entries[0].result == "0.3"
    before = session.history_path.read_bytes()
    result = runner.invoke(cli_app.app, ["history"])
    assert result.exit_code == 0
    assert result.stdout == "0.1 + 0.2 = 0.3\n"
    assert session.history_path.read_bytes() == before


def test_calculation_error_and_negative_expression(session):
    runner = CliRunner()
    result = runner.invoke(cli_app.app, ["calculate", "1/0"])
    assert result.exit_code == 1
    assert "Division by zero" in result.output
    assert not session.history_path.exists()
    result = runner.invoke(cli_app.app, ["calculate", "--", "-2 ^ 2"])
    assert result.exit_code == 0
    assert result.stdout == "4\n"


@pytest.mark.parametrize(
    "args",
    [["--gui", "--tui"], ["--cli", "--gui"], ["--tui", "calculate", "1+1"]],
)
def test_conflicting_modes_do_not_launch(monkeypatch, args):
    monkeypatch.setattr(
        cli_app, "launch_interface", lambda _: pytest.fail("unexpected launch")
    )
    assert CliRunner().invoke(cli_app.app, args).exit_code == 2


@pytest.mark.parametrize("mode", ["gui", "tui", "cli"])
def test_explicit_mode_launches_only_requested_interface(monkeypatch, mode):
    calls = []
    monkeypatch.setattr(
        cli_app,
        "launch_interface",
        lambda selected: calls.append(selected) or 7,
    )
    result = CliRunner().invoke(cli_app.app, [f"--{mode}"])
    assert result.exit_code == 7
    assert calls == [mode]


def test_no_arguments_noninteractive_fails_without_waiting(monkeypatch):
    monkeypatch.setattr(launch.sys.stdin, "isatty", lambda: False)
    result = CliRunner().invoke(cli_app.app, [])
    assert result.exit_code == 2
    assert "--help" in result.output


def test_chooser_reprompts_and_quit_is_side_effect_free(monkeypatch):
    monkeypatch.setattr(launch.sys.stdin, "isatty", lambda: True)
    answers = iter(["bad", "Q"])
    monkeypatch.setattr(launch.typer, "prompt", lambda _: next(answers))
    monkeypatch.setattr(
        cli_app, "launch_interface", lambda _: pytest.fail("unexpected launch")
    )
    assert cli_app.run_app([]) == 0


@pytest.mark.parametrize(
    "args",
    [
        ["--help"],
        ["--cli", "--help"],
        ["calculate", "--help"],
        ["--cli", "history", "--help"],
    ],
)
def test_help_imports_no_toolkits_and_loads_no_state(monkeypatch, args):
    monkeypatch.setattr(
        commands, "load_session", lambda: pytest.fail("unexpected state load")
    )
    assert CliRunner().invoke(cli_app.app, args).exit_code == 0
    code = (
        "import sys; from plain_text_fin_calc.ui.cli.app import run_app; "
        f"assert run_app({args!r}) == 0; "
        "assert not any(m.startswith(('PySide6', 'textual')) for m in sys.modules)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr


def _saved(session):
    return [
        (entry.expression, entry.result, entry.rpn_input)
        for entry in load_history(session.history_path).entries
    ]


def test_calculate_rpn_prints_x_and_saves_keys(session):
    result = CliRunner().invoke(cli_app.app, ["calculate", "--rpn", "3 4 +"])
    assert result.exit_code == 0, result.output
    assert result.stdout == "7\n"
    assert _saved(session) == [("3 + 4", "7", "3 4 +")]


def test_calculate_rpn_saves_every_calculation_of_the_line(session):
    result = CliRunner().invoke(
        cli_app.app, ["calculate", "--rpn", "3 ENTER 4 + 5 *"]
    )
    assert result.exit_code == 0, result.output
    assert result.stdout == "35\n"
    assert _saved(session) == [
        ("3 + 4", "7", "3 ENTER 4 +"),
        ("7 * 5", "35", "5 *"),
    ]


def test_calculate_rpn_negative_first_number_and_no_calculation(session):
    runner = CliRunner()
    result = runner.invoke(cli_app.app, ["calculate", "--rpn", "--", "-5 3 *"])
    assert result.exit_code == 0, result.output
    assert result.stdout == "-15\n"
    result = runner.invoke(cli_app.app, ["calculate", "--rpn", "3 4"])
    assert result.exit_code == 0, result.output
    assert result.stdout == "4\n"
    assert _saved(session) == [("-5 * 3", "-15", "-5 3 *")]


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("5 0 /", "Error: Division by zero"),
        ("3 4 + 0 /", "Error: Division by zero"),
        ("3 drop", "Error: Stack is empty"),
        ("", "Error: Empty expression"),
        ("3 x", "Error: Invalid input: x"),
    ],
)
def test_calculate_rpn_error_saves_nothing(session, line, message):
    result = CliRunner().invoke(cli_app.app, ["calculate", "--rpn", line])
    assert result.exit_code == 1
    assert message in result.stderr
    assert not result.stdout
    assert not session.history_path.exists()


@pytest.mark.parametrize("mode", ["algebraic", "rpn"])
def test_calculate_ignores_the_saved_input_mode(session, mode):
    session.settings = Settings(input_mode=mode)
    runner = CliRunner()
    result = runner.invoke(cli_app.app, ["calculate", "1 + 2"])
    assert result.exit_code == 0, result.output
    assert result.stdout == "3\n"
    result = runner.invoke(cli_app.app, ["calculate", "--rpn", "3 4 +"])
    assert result.exit_code == 0, result.output
    assert result.stdout == "7\n"
    assert _saved(session) == [("1 + 2", "3", None), ("3 + 4", "7", "3 4 +")]


def test_calculate_help_describes_rpn_option(monkeypatch):
    monkeypatch.setattr(
        commands, "load_session", lambda: pytest.fail("unexpected state load")
    )
    result = CliRunner().invoke(cli_app.app, ["calculate", "--help"])
    assert result.exit_code == 0
    assert "--rpn" in result.stdout
    assert "enter, swap, drop, chs, log, clear" in " ".join(result.stdout.split())
