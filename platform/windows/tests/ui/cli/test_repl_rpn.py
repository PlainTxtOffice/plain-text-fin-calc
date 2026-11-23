"""Verify the prompt's RPN mode: stack output, saved keys, and mode changes."""

import pytest
from typer.testing import CliRunner

from plain_text_fin_calc.adapters.history_store import load_history
from plain_text_fin_calc.adapters.settings_store import load_settings
from plain_text_fin_calc.application import session as session_module
from plain_text_fin_calc.application import startup
from plain_text_fin_calc.application.session import CalculatorSession
from plain_text_fin_calc.config.settings import Settings
from plain_text_fin_calc.domains.calc.history import History
from plain_text_fin_calc.ui.cli.app import app


def _session(monkeypatch, tmp_path, settings):
    calculator = CalculatorSession(
        History(), settings, tmp_path / "history.json",
        tmp_path / "settings.json",
    )
    monkeypatch.setattr(startup, "configure_logging", lambda: None)
    monkeypatch.setattr(startup, "load_session", lambda: calculator)
    return calculator


@pytest.fixture
def rpn_session(monkeypatch, tmp_path):
    return _session(monkeypatch, tmp_path, Settings(input_mode="rpn"))


@pytest.fixture
def session(monkeypatch, tmp_path):
    return _session(monkeypatch, tmp_path, Settings())


def _run(text):
    result = CliRunner().invoke(app, ["--cli"], input=text)
    assert result.exit_code == 0, result.output
    return result


def _saved(session):
    return [
        (entry.expression, entry.result, entry.rpn_input)
        for entry in load_history(session.history_path).entries
    ]


def test_rpn_lines_show_stack_and_save_keys(rpn_session):
    rpn_session.settings = Settings(input_mode="rpn", decimal_places=2)
    result = _run("3 4 +\n5 *\nhistory\nexit\n")
    assert "fin-calc rpn> " in result.stdout
    assert "fin-calc> " not in result.stdout
    assert "X: 7.00\n" in result.stdout
    assert "X: 35.00\n" in result.stdout
    assert "3 + 4 = 7.00\n" in result.stdout
    assert "7 * 5 = 35.00\n" in result.stdout
    assert not result.stderr
    assert _saved(rpn_session) == [
        ("3 + 4", "7", "3 4 +"),
        ("7 * 5", "35", "5 *"),
    ]


def test_rpn_line_without_calculation_shows_all_levels(rpn_session):
    result = _run("1 2 3\nexit\n")
    assert "Z: 1\nY: 2\nX: 3\n" in result.stdout
    assert not rpn_session.history_path.exists()


def test_rpn_prompt_recovers_from_failed_lines(rpn_session):
    result = _run("5 0 /\n+\n3 4 +\nquit\n")
    assert "Error: Division by zero" in result.stderr
    assert "Error: Too few operands" in result.stderr
    assert result.stderr.count("Error:") == 2
    assert "X: 7\n" in result.stdout
    assert _saved(rpn_session) == [("3 + 4", "7", "3 4 +")]


def test_rpn_prompt_recovers_from_failed_save(rpn_session, monkeypatch):
    write_history = session_module.write_history
    attempts = []

    def write_once_writable(history, path):
        attempts.append(True)
        if len(attempts) == 1:
            raise PermissionError("history is read-only")
        write_history(history, path)

    monkeypatch.setattr(session_module, "write_history", write_once_writable)
    result = _run("3 4 +\n3 4 +\nexit\n")
    assert "Error: history is read-only" in result.stderr
    assert result.stdout.count("X: 7\n") == 1
    assert _saved(rpn_session) == [("3 + 4", "7", "3 4 +")]


def test_clear_word_empties_the_stack(rpn_session):
    result = _run("3 4 + clear\nexit\n")
    assert "Stack is empty.\n" in result.stdout
    assert _saved(rpn_session) == [("3 + 4", "7", "3 4 +")]


def test_config_switches_mode_for_the_next_line(session):
    result = _run(
        "config input_mode rpn\n3 4 +\nconfig input-mode algebraic\n3+4\nexit\n"
    )
    out = result.stdout
    assert out.count("Settings saved.") == 2
    assert out.index("input_mode = rpn") < out.index("input_mode = algebraic")
    assert "fin-calc rpn> X: 7\n" in out
    assert "fin-calc> 7\n" in out
    assert not result.stderr
    assert load_settings(session.settings_path).input_mode == "algebraic"
    assert _saved(session) == [("3 + 4", "7", "3 4 +"), ("3+4", "7", None)]


def test_config_lists_and_validates_input_mode(session):
    result = _run("config\nconfig input_mode other\nconfig INPUT_MODE RPN\nexit\n")
    assert "input_mode = algebraic" in result.stdout
    assert "config input_mode <algebraic|rpn>" in result.stdout
    assert "Error: Input mode must be one of: algebraic, rpn." in result.stderr
    assert result.stdout.count("Settings saved.") == 1
    assert session.settings.input_mode == "rpn"


def test_invalid_input_mode_keeps_settings(session):
    result = _run("config input_mode other\nexit\n")
    assert "Error: Input mode must be one of: algebraic, rpn." in result.stderr
    assert session.settings == Settings()
    assert not session.settings_path.exists()


def test_mode_change_clears_the_stack(rpn_session):
    result = _run(
        "1 2\nconfig input_mode algebraic\nconfig input_mode rpn\n+\nexit\n"
    )
    assert "Error: Too few operands" in result.stderr
    assert not rpn_session.history_path.exists()


def test_failed_settings_write_keeps_mode_and_stack(rpn_session, monkeypatch):
    def deny_write(*_args):
        raise PermissionError("settings are read-only")

    monkeypatch.setattr(session_module, "write_settings", deny_write)
    result = _run("1 2\nconfig input_mode algebraic\n+\nexit\n")
    assert "settings are read-only" in result.stderr
    assert "Settings saved." not in result.stdout
    assert "X: 3\n" in result.stdout
    assert rpn_session.settings.input_mode == "rpn"


def test_help_follows_the_input_mode(rpn_session):
    result = _run("help\nconfig input_mode algebraic\nhelp\nexit\n")
    out = result.stdout
    assert "Enter numbers and operators separated by spaces" in out
    assert "chs (change sign)" in out
    assert "Expressions need no quotes" in out
    assert "config input_mode rpn: switch to RPN entry" in out
    assert out.index("separated by spaces, such as 3 4 +, and press") < out.index(
        "Expressions need no quotes"
    )
    assert not rpn_session.history_path.exists()
