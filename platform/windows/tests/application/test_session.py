"""Verify calculator workflows preserve precision and report write failures."""

from pathlib import Path

import pytest

from plain_text_fin_calc.adapters.history_store import load_history, write_history
from plain_text_fin_calc.adapters.settings_store import load_settings
from plain_text_fin_calc.application import session as session_module
from plain_text_fin_calc.application.session import CalculatorSession
from plain_text_fin_calc.domains.calc.errors import EvaluationError
from plain_text_fin_calc.domains.calc.history import History
from plain_text_fin_calc.domains.calc.rpn_stack import RpnStack
from plain_text_fin_calc.config.settings import Settings


def test_history_roundtrip_retains_precision_and_applies_cap(tmp_path):
    path = tmp_path / "history.json"
    session = CalculatorSession(
        History(), Settings(decimal_places=2, max_history_entries=1), path
    )
    assert session.calculate("1 / 3") == "0.33"
    assert load_history(path).entries[0].result.startswith("0.333333333")
    assert session.calculate("2 + 2") == "4.00"
    assert len(session.history.entries) == 1
    assert load_history(path).entries[0].expression == "2 + 2"


def test_invalid_expression_does_not_write(tmp_path):
    path = tmp_path / "history.json"
    session = CalculatorSession(History(), Settings(), path)
    with pytest.raises(EvaluationError):
        session.calculate("1/0")
    assert not path.exists()
    assert not session.history.entries


def test_write_failure_does_not_claim_saved_result(monkeypatch, tmp_path):
    path = tmp_path / "history.json"
    session = CalculatorSession(History(), Settings(), path)

    def deny_write(*args, **kwargs):
        raise PermissionError("read-only history")

    monkeypatch.setattr(Path, "write_text", deny_write)
    with pytest.raises(PermissionError):
        write_history(History(), path)
    with pytest.raises(PermissionError):
        session.calculate("1+1")
    assert not session.history.entries


def _rpn_session(tmp_path, **settings):
    return CalculatorSession(
        History(), Settings(input_mode="rpn", **settings),
        tmp_path / "history.json", tmp_path / "settings.json",
    )


def test_rpn_line_saves_each_calculation_with_its_keys(tmp_path):
    session = _rpn_session(tmp_path)
    session.run_rpn_line("3 4 + 5 *")
    saved = load_history(session.history_path).entries
    assert saved == session.history.entries
    assert [(e.expression, e.result, e.rpn_input) for e in saved] == [
        ("3 + 4", "7", "3 4 +"),
        ("7 * 5", "35", "5 *"),
    ]
    assert session.rpn.levels == ("35",)


def test_rpn_line_applies_history_cap(tmp_path):
    session = _rpn_session(tmp_path, max_history_entries=1)
    session.run_rpn_line("3 4 + 5 *")
    assert [e.expression for e in session.history.entries] == ["7 * 5"]
    assert [e.expression for e in load_history(session.history_path).entries] == [
        "7 * 5"
    ]


def test_rpn_line_without_calculation_writes_nothing(tmp_path):
    session = _rpn_session(tmp_path)
    session.run_rpn_line("1 2 3")
    assert session.rpn.levels == ("3", "2", "1")
    assert not session.history_path.exists()


@pytest.mark.parametrize("before", ["", "8 9"])
def test_failed_rpn_line_changes_nothing(tmp_path, before):
    session = _rpn_session(tmp_path)
    if before:
        session.run_rpn_line(before)
    stack = session.rpn
    with pytest.raises(EvaluationError, match="Division by zero"):
        session.run_rpn_line("3 4 + 5 0 /")
    assert not session.history_path.exists()
    assert not session.history.entries
    assert session.rpn == stack


def test_rpn_write_failure_keeps_stack_and_history(monkeypatch, tmp_path):
    session = _rpn_session(tmp_path)
    session.run_rpn_line("9")

    def deny_write(*args, **kwargs):
        raise PermissionError("read-only history")

    monkeypatch.setattr(session_module, "write_history", deny_write)
    with pytest.raises(PermissionError):
        session.run_rpn_line("3 4 +")
    assert not session.history.entries
    assert session.rpn.levels == ("9",)
    with pytest.raises(PermissionError):
        session.calculate_rpn("3 4 +")
    assert not session.history.entries


def test_calculate_rpn_uses_a_fresh_stack_and_returns_x(tmp_path):
    session = _rpn_session(tmp_path)
    session.run_rpn_line("100 200")
    stack = session.rpn
    assert session.calculate_rpn("3 4 +") == "7"
    assert session.rpn == stack
    (entry,) = load_history(session.history_path).entries
    assert (entry.expression, entry.result, entry.rpn_input) == (
        "3 + 4", "7", "3 4 +",
    )
    session.settings = Settings(decimal_places=2)
    assert session.calculate_rpn("3 4 +") == "7.00"
    assert len(session.history.entries) == 2


def test_calculate_rpn_without_calculation_or_result(tmp_path):
    session = _rpn_session(tmp_path)
    assert session.calculate_rpn("3 4") == "4"
    with pytest.raises(EvaluationError, match="^Stack is empty$"):
        session.calculate_rpn("3 drop")
    with pytest.raises(EvaluationError, match="^Stack is empty$"):
        session.calculate_rpn("3 4 + clear")
    with pytest.raises(EvaluationError, match="^Empty expression$"):
        session.calculate_rpn("")
    assert not session.history_path.exists()
    assert not session.history.entries


def test_changing_input_mode_clears_stack_and_keeps_history(tmp_path):
    session = _rpn_session(tmp_path)
    session.run_rpn_line("3 4 + 9")
    session.update_settings(Settings(input_mode="rpn", decimal_places=2))
    assert session.rpn.levels == ("9", "7")
    session.update_settings(Settings(input_mode="algebraic"))
    assert session.rpn == RpnStack()
    assert len(session.history.entries) == 1
    assert load_settings(session.settings_path).input_mode == "algebraic"


def test_failed_settings_write_keeps_mode_and_stack(monkeypatch, tmp_path):
    session = _rpn_session(tmp_path)
    session.run_rpn_line("3 4")

    def deny_write(*args):
        raise PermissionError("settings are read-only")

    monkeypatch.setattr(session_module, "write_settings", deny_write)
    with pytest.raises(PermissionError):
        session.update_settings(Settings(input_mode="algebraic"))
    assert session.settings.input_mode == "rpn"
    assert session.rpn.levels == ("4", "3")


def test_algebraic_entries_have_no_rpn_input(tmp_path):
    session = CalculatorSession(History(), Settings(), tmp_path / "history.json")
    session.calculate("1 + 2")
    assert load_history(session.history_path).entries[0].rpn_input is None


def test_algebraic_results_drop_trailing_zeros_and_negative_zero(tmp_path):
    session = CalculatorSession(History(), Settings(), tmp_path / "history.json")
    assert session.calculate("0.07 * 100") == "7"
    assert session.calculate("0 * -5") == "0"
    saved = load_history(session.history_path).entries
    assert [entry.result for entry in saved] == ["7", "0"]
