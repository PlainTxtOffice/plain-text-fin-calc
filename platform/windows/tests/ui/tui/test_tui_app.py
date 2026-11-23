"""Drive actual Textual input, error recovery, history, and quit bindings."""

import asyncio

from textual.widgets import Input, RichLog, Static

from plain_text_fin_calc.adapters.history_store import load_history
from plain_text_fin_calc.application.session import CalculatorSession
from plain_text_fin_calc.domains.calc.history import History
from plain_text_fin_calc.config.settings import Settings
from plain_text_fin_calc.ui.tui.app import CalculatorApp


def test_terminal_calculation_error_recovery_and_quit(tmp_path):
    session = CalculatorSession(
        History(), Settings(decimal_places=2), tmp_path / "history.json"
    )

    async def exercise():
        app = CalculatorApp(session)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.press(*"0.1+0.2", "enter")
            assert "0.30" in str(app.query_one("#result", Static).content)
            assert load_history(session.history_path).entries[0].result == "0.3"
            tape_lines = app.query_one(RichLog).lines
            assert tape_lines[0].text.rstrip() == "0.1+0.2 = 0.30"
            await pilot.press(*"1/0", "enter")
            assert "Division by zero" in str(
                app.query_one("#result", Static).content
            )
            assert len(session.history.entries) == 1
            await pilot.press("escape")
            assert app.query_one(Input).value == ""
            await pilot.press(*"2^10", "enter")
            assert session.history.entries[-1].result == "1024"
            await pilot.press("ctrl+q")
        assert app.return_code == 0

    asyncio.run(exercise())


def test_terminal_loads_history_and_reports_save_errors(tmp_path, monkeypatch):
    session = CalculatorSession(
        History(), Settings(theme="light"), tmp_path / "history.json"
    )
    session.calculate("2+3")

    def deny_write(*args):
        raise PermissionError("read-only history")

    async def exercise():
        app = CalculatorApp(session)
        async with app.run_test(size=(80, 24)) as pilot:
            assert app.theme == "textual-light"
            assert app.query_one(RichLog).lines
            monkeypatch.setattr(
                "plain_text_fin_calc.application.session.write_history", deny_write
            )
            await pilot.press(*"3+4", "enter")
            assert "read-only history" in str(
                app.query_one("#result", Static).content
            )
            assert len(session.history.entries) == 1

    asyncio.run(exercise())


def _type(text):
    return ["space" if char == " " else char for char in text]


def _result(app):
    return str(app.query_one("#result", Static).content)


def test_terminal_rpn_lines_show_stack_and_save_keys(tmp_path):
    session = CalculatorSession(
        History(), Settings(decimal_places=2, input_mode="rpn"),
        tmp_path / "history.json",
    )

    async def exercise():
        app = CalculatorApp(session)
        async with app.run_test(size=(80, 24)) as pilot:
            idle = "Enter numbers and operators separated by spaces and press Enter."
            assert _result(app) == idle
            assert app.query_one(Input).placeholder == "Example: 3 4 + or 100 log"
            await pilot.press("escape")
            assert _result(app) == idle

            await pilot.press(*_type("3 4 +"), "enter")
            assert _result(app) == "X: 7.00"
            assert app.query_one(RichLog).lines[0].text.rstrip() == "3 + 4 = 7.00"
            (entry,) = load_history(session.history_path).entries
            assert (entry.result, entry.rpn_input) == ("7", "3 4 +")
            assert app.query_one(Input).value == ""

            await pilot.press("5", "enter")
            assert _result(app) == "Y: 7.00  X: 5.00"

            await pilot.press(*_type("0 /"), "enter")
            assert _result(app) == "Error: Division by zero"
            assert len(session.history.entries) == 1
            assert session.rpn.levels == ("5", "7")
            assert app.query_one(Input).value == "0 /"

            await pilot.press("escape")
            assert app.query_one(Input).value == ""
            assert _result(app) == "Y: 7.00  X: 5.00"

            await pilot.press(*_type("clear"), "enter")
            assert _result(app) == "Stack is empty."
            await pilot.press("escape")
            assert _result(app) == idle
            await pilot.press("ctrl+q")
        assert app.return_code == 0

    asyncio.run(exercise())


def test_terminal_rpn_reports_save_errors(tmp_path, monkeypatch):
    session = CalculatorSession(
        History(), Settings(input_mode="rpn"), tmp_path / "history.json"
    )

    def deny_write(*args):
        raise PermissionError("read-only history")

    async def exercise():
        app = CalculatorApp(session)
        async with app.run_test(size=(80, 24)) as pilot:
            monkeypatch.setattr(
                "plain_text_fin_calc.application.session.write_history", deny_write
            )
            await pilot.press(*_type("3 4 +"), "enter")
            assert "read-only history" in _result(app)
            assert not session.history.entries
            assert session.rpn.levels == ()

    asyncio.run(exercise())


def test_terminal_algebraic_mode_keeps_its_texts(tmp_path):
    session = CalculatorSession(History(), Settings(), tmp_path / "history.json")

    async def exercise():
        app = CalculatorApp(session)
        async with app.run_test(size=(80, 24)) as pilot:
            assert _result(app) == "Enter an expression and press Enter."
            assert (
                app.query_one(Input).placeholder
                == "Example: 0.1 + 0.2 or log(100)"
            )
            await pilot.press(*_type("3 4 +"), "enter")
            assert _result(app).startswith("Error:")
            await pilot.press("escape")
            assert _result(app) == "Enter an expression and press Enter."
            await pilot.press(*"3+4", "enter")
            assert _result(app) == "Result: 7"
            assert session.history.entries[0].rpn_input is None

    asyncio.run(exercise())
