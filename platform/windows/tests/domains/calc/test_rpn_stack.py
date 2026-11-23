"""Run the RPN behaviour vectors against the domain stack.

Vector names (V, W, L) follow the RPN behaviour specification shared with the
Android and iOS apps; W and L vectors are specific to the Windows version.
"""

from __future__ import annotations

import random

import pytest

from plain_text_fin_calc.domains.calc.errors import EvaluationError
from plain_text_fin_calc.domains.calc.evaluator import evaluate, result_text
from plain_text_fin_calc.domains.calc.formatting import format_stack_lines
from plain_text_fin_calc.domains.calc.parsing import parse_expression
from plain_text_fin_calc.domains.calc.rpn_stack import (
    MAX_KEYS,
    RpnRecord,
    RpnStack,
    canon,
    is_zero_text,
    result_string,
    run_line,
)

_KEY_NAMES = {"ENTER": "enter", "SWAP": "swap", "DROP": "drop", "bksp": "backspace"}
_PLAIN_KEYS = {"sign", "C", "log", "+", "-", "*", "/", "^", ".", "(", ")", "="}
THIRD = "0.3333333333333333333333333333"


def assert_algebraic_parity(record: RpnRecord) -> None:
    """Every tape line must be reproduced exactly by the algebraic engine."""
    assert result_string(record.expression.split(" ")) == record.result
    assert result_text(evaluate(parse_expression(record.expression))) == record.result


class Rpn:
    """Type vector keys on a stack and collect the tape lines they produce."""

    def __init__(self) -> None:
        self.stack = RpnStack()
        self.records: list[RpnRecord] = []

    @property
    def levels(self) -> list[str]:
        return list(self.stack.levels)

    @property
    def tape(self) -> list[str]:
        return [
            f"{r.expression} = {r.result} | {r.rpn_input}" for r in self.records
        ]

    def _apply(self, step) -> None:
        self.stack = step.stack
        if step.record is not None:
            assert_algebraic_parity(step.record)
            self.records.append(step.record)

    def keys(self, text: str) -> Rpn:
        """Press vector keys; numbers are typed one character at a time."""
        for token in text.split():
            if token in _KEY_NAMES:
                self._apply(self.stack.press(_KEY_NAMES[token]))
            elif token in _PLAIN_KEYS:
                self._apply(self.stack.press(token))
            else:
                for char in token:
                    self._apply(self.stack.press(char))
        return self

    def reuse(self, value: str) -> Rpn:
        self._apply(self.stack.reuse(value))
        return self

    def fails(self, key: str, message: str) -> None:
        """The key is refused with this message and nothing changes."""
        before = self.stack
        lines = self.tape
        with pytest.raises(EvaluationError) as error:
            self.keys(key)
        assert str(error.value) == message
        assert self.stack == before
        assert self.tape == lines


def test_v01_add_shows_registers_at_each_step():
    rpn = Rpn().keys("3")
    assert rpn.stack == RpnStack((), "3")
    assert rpn.stack.visible_y is None
    rpn.keys("ENTER")
    assert rpn.levels == ["3", "3"]
    assert rpn.stack.lift is False
    assert rpn.stack.entry is None
    assert rpn.stack.visible_y == "3"
    rpn.keys("4")
    assert rpn.stack == RpnStack(("3",), "4", True, ("3", "ENTER"))
    assert rpn.stack.visible_y == "3"
    rpn.keys("+")
    assert rpn.stack == RpnStack(("7",))
    assert rpn.stack.visible_y is None
    assert rpn.tape == ["3 + 4 = 7 | 3 ENTER 4 +"]


@pytest.mark.parametrize(
    ("keys", "levels", "tape"),
    [
        pytest.param(
            "0 . 1 ENTER 0 . 2 +", ["0.3"],
            ["0.1 + 0.2 = 0.3 | 0.1 ENTER 0.2 +"], id="V2",
        ),
        pytest.param(
            ". 5 ENTER . 2 5 -", ["0.25"],
            ["0.5 - 0.25 = 0.25 | 0.5 ENTER 0.25 -"], id="V3",
        ),
        pytest.param(
            "3 ENTER 4 + 5 *", ["35"],
            ["3 + 4 = 7 | 3 ENTER 4 +", "7 * 5 = 35 | 5 *"], id="V4",
        ),
        pytest.param(
            "1 ENTER 2 ENTER 3 + +", ["6"],
            ["2 + 3 = 5 | 1 ENTER 2 ENTER 3 +", "1 + 5 = 6 | +"], id="V5",
        ),
        pytest.param(
            "2 ENTER 3 + 4 ENTER 5 + *", ["45"],
            [
                "2 + 3 = 5 | 2 ENTER 3 +",
                "4 + 5 = 9 | 4 ENTER 5 +",
                "5 * 9 = 45 | *",
            ],
            id="V6",
        ),
        pytest.param(
            "5 sign ENTER 3 *", ["-15"],
            ["-5 * 3 = -15 | -5 ENTER 3 *"], id="V7",
        ),
        pytest.param(
            "3 ENTER 5 sign -", ["8"], ["3 - -5 = 8 | 3 ENTER -5 -"], id="V8",
        ),
        pytest.param(
            "3 ENTER 4 + sign 2 *", ["-14"],
            ["3 + 4 = 7 | 3 ENTER 4 +", "-7 * 2 = -14 | CHS 2 *"], id="V9",
        ),
        pytest.param(
            "2 sign ENTER 2 ^", ["4"], ["-2 ^ 2 = 4 | -2 ENTER 2 ^"], id="V10",
        ),
        pytest.param(
            "1 ENTER 3 / 3 *", ["0.9999999999999999999999999999"],
            [
                f"1 / 3 = {THIRD} | 1 ENTER 3 /",
                f"{THIRD} * 3 = 0.9999999999999999999999999999 | 3 *",
            ],
            id="V11",
        ),
        pytest.param(
            "2 ENTER 3 /", ["0.6666666666666666666666666667"],
            ["2 / 3 = 0.6666666666666666666666666667 | 2 ENTER 3 /"], id="V12",
        ),
        pytest.param(
            "4 ENTER ENTER ENTER * *", ["64", "4", "4", "4"],
            ["4 * 4 = 16 | 4 ENTER ENTER ENTER *", "4 * 16 = 64 | *"], id="V16",
        ),
        pytest.param(
            "8 ENTER 2 SWAP /", ["0.25"],
            ["2 / 8 = 0.25 | 8 ENTER 2 SWAP /"], id="V17",
        ),
        pytest.param(
            "1 ENTER 2 ENTER 3 DROP +", ["3"],
            ["1 + 2 = 3 | 1 ENTER 2 ENTER 3 DROP +"], id="V19",
        ),
        pytest.param(
            "1 ENTER 2 ENTER 3 ENTER 4 ENTER 5 + + +", ["14", "2", "2", "2"],
            [
                "4 + 5 = 9 | 1 ENTER 2 ENTER 3 ENTER 4 ENTER 5 +",
                "3 + 9 = 12 | +",
                "2 + 12 = 14 | +",
            ],
            id="V21",
        ),
        pytest.param(
            "1 2 bksp 3 ENTER 2 +", ["15"],
            ["13 + 2 = 15 | 13 ENTER 2 +"], id="V25",
        ),
        pytest.param(
            "0 sign ENTER 5 +", ["5"], ["0 + 5 = 5 | 0 ENTER 5 +"], id="V28",
        ),
        pytest.param(
            "1 . 5 0 ENTER 2 +", ["3.5"],
            ["1.5 + 2 = 3.5 | 1.5 ENTER 2 +"], id="W1-trailing-zeros-dropped",
        ),
        pytest.param(
            "0 0 7 ENTER 5 . +", ["12"], ["7 + 5 = 12 | 7 ENTER 5 +"], id="W2",
        ),
    ],
)
def test_key_sequences_give_levels_and_tape(keys, levels, tape):
    rpn = Rpn().keys(keys)
    assert rpn.levels == levels
    assert rpn.tape == tape
    assert rpn.stack.entry is None
    assert rpn.stack.keys == ()


def test_v04_v05_intermediate_states():
    rpn = Rpn().keys("3 ENTER 4 + 5")
    assert rpn.stack == RpnStack(("7",), "5")
    assert rpn.stack.visible_y == "7"
    rpn = Rpn().keys("1 ENTER 2 ENTER 3 +")
    assert rpn.levels == ["5", "1"]


def test_v09_sign_change_of_x_is_logged_without_tape_line():
    rpn = Rpn().keys("3 ENTER 4 + sign")
    assert rpn.levels == ["-7"]
    assert rpn.stack.keys == ("CHS",)
    assert len(rpn.records) == 1


def test_v13_division_by_zero_changes_nothing_then_recovers():
    rpn = Rpn().keys("5 ENTER 0")
    rpn.fails("/", "Division by zero")
    assert rpn.stack == RpnStack(("5",), "0", True, ("5", "ENTER"))
    assert rpn.stack.visible_y == "5"
    rpn.keys("bksp")
    assert rpn.stack.entry is None
    assert rpn.levels == ["5"]
    rpn.keys("2 /")
    assert rpn.levels == ["2.5"]
    assert rpn.tape == ["5 / 2 = 2.5 | 5 ENTER 2 /"]


@pytest.mark.parametrize(
    "key", ["+", "-", "*", "/", "^", "log", "SWAP", "DROP", "ENTER"]
)
def test_v14_empty_stack_refuses_keys_that_need_operands(key):
    rpn = Rpn()
    rpn.fails(key, "Too few operands")
    assert rpn.stack == RpnStack()


@pytest.mark.parametrize("key", ["sign", "bksp", "C"])
def test_v14_empty_stack_ignores_editing_keys(key):
    assert Rpn().keys(key).stack == RpnStack()


def test_v15_operator_with_one_number_keeps_the_typed_number():
    rpn = Rpn().keys("3")
    rpn.fails("+", "Too few operands")
    assert rpn.stack == RpnStack((), "3")
    rpn.keys("ENTER +")
    assert rpn.levels == ["6"]
    assert rpn.tape == ["3 + 3 = 6 | 3 ENTER +"]


def test_v16_v21_full_stack_repeats_top_level():
    rpn = Rpn().keys("4 ENTER ENTER ENTER")
    assert rpn.levels == ["4", "4", "4", "4"]
    assert rpn.stack.lift is False
    rpn.keys("*")
    assert rpn.levels == ["16", "4", "4", "4"]
    rpn = Rpn().keys("1 ENTER 2 ENTER 3 ENTER 4 ENTER")
    assert rpn.levels == ["4", "4", "3", "2"]
    rpn.keys("5")
    assert (rpn.levels, rpn.stack.entry) == (["4", "3", "2"], "5")
    rpn.keys("+")
    assert rpn.levels == ["9", "3", "2", "2"]


def test_v17_v18_swap():
    assert Rpn().keys("8 ENTER 2 SWAP").levels == ["8", "2"]
    rpn = Rpn().keys("8")
    rpn.fails("SWAP", "Too few operands")
    assert rpn.stack == RpnStack((), "8")


def test_v20_drop_on_a_full_stack_repeats_top_and_makes_no_tape_line():
    rpn = Rpn().keys("1 ENTER 2 ENTER 3 ENTER 4")
    assert (rpn.levels, rpn.stack.entry) == (["3", "2", "1"], "4")
    rpn.keys("DROP")
    assert rpn.levels == ["3", "2", "1", "1"]
    assert rpn.stack.visible_y == "2"
    assert rpn.keys("DROP").levels == ["2", "1", "1", "1"]
    assert rpn.keys("DROP").levels == ["1", "1", "1", "1"]
    assert rpn.records == []
    assert rpn.keys("C").stack == RpnStack()


def test_v22_log_matches_the_algebraic_result():
    rpn = Rpn().keys("1 0 0 log")
    expected = result_string(["log", "(", "100", ")"])
    assert expected == "2"
    assert rpn.levels == [expected]
    assert rpn.tape == [f"log ( 100 ) = {expected} | 100 LOG"]


def test_v23_log_of_zero_is_refused():
    rpn = Rpn().keys("0")
    rpn.fails("log", "Log undefined for non-positive values")
    assert rpn.stack.entry == "0"
    assert rpn.records == []


def test_v24_clear_removes_the_typed_number_then_the_stack():
    rpn = Rpn().keys("3 ENTER 4 C")
    assert rpn.stack == RpnStack(("3",), None, True, ("3", "ENTER"))
    assert rpn.keys("C").stack == RpnStack()
    rpn.fails("+", "Too few operands")


def test_v25_backspace_edits_the_typed_number():
    rpn = Rpn().keys("1 2")
    assert rpn.stack.entry == "12"
    assert rpn.keys("bksp").stack.entry == "1"
    assert rpn.keys("3").stack.entry == "13"


def test_v26_second_decimal_point_is_refused():
    rpn = Rpn().keys("1 . 5")
    rpn.fails(".", "Invalid input: .")
    assert rpn.stack.entry == "1.5"


def test_v27_twenty_ninth_digit_is_refused():
    digits = "1234567890123456789012345678"
    rpn = Rpn().keys(digits)
    rpn.fails("9", "Invalid input: 9")
    assert rpn.stack.entry == digits


def test_v28_negative_zero_entry_is_stored_as_zero():
    rpn = Rpn().keys("0 sign")
    assert rpn.stack.entry == "-0"
    assert rpn.keys("ENTER").levels == ["0", "0"]


def test_v29_v30_engine_errors_change_nothing():
    rpn = Rpn().keys("0 ENTER 0")
    rpn.fails("^", "Invalid exponentiation: 0 ^ 0")
    assert (rpn.levels, rpn.stack.entry) == (["0"], "0")
    rpn = Rpn().keys("9 ENTER 9 9 9 9 9 9 9")
    rpn.fails("^", "Result out of range")
    assert (rpn.levels, rpn.stack.entry) == (["9"], "9999999")
    assert rpn.records == []


def test_v31_reuse_on_empty_stack():
    rpn = Rpn().reuse(THIRD)
    assert rpn.stack == RpnStack((THIRD,), None, True, (THIRD,))
    rpn.keys("3 *")
    assert rpn.tape == [
        f"{THIRD} * 3 = 0.9999999999999999999999999999 | {THIRD} 3 *"
    ]


def test_v32_reuse_after_a_result_lifts_the_stack():
    rpn = Rpn().keys("2 ENTER 3 +").reuse("7")
    assert rpn.levels == ["7", "5"]
    rpn.keys("*")
    assert rpn.tape[-1] == "5 * 7 = 35 | 7 *"


def test_v33_reuse_replaces_the_number_being_typed():
    rpn = Rpn().keys("9 7").reuse("42")
    assert (rpn.levels, rpn.stack.entry) == (["42"], None)
    rpn.keys("3")
    assert (rpn.levels, rpn.stack.entry) == (["42"], "3")
    assert rpn.stack.visible_y == "42"


def test_v34_reuse_directly_after_enter_overwrites_x():
    rpn = Rpn().keys("2 ENTER")
    assert (rpn.levels, rpn.stack.lift) == (["2", "2"], False)
    rpn.reuse("7")
    assert (rpn.levels, rpn.stack.lift) == (["7", "2"], True)
    rpn.keys("+")
    assert rpn.tape == ["2 + 7 = 9 | 2 ENTER 7 +"]


def test_v35_stack_and_tape_keep_full_precision():
    rpn = Rpn().keys("1 ENTER 3 /")
    assert rpn.levels == [THIRD]
    assert format_stack_lines(rpn.stack, 2) == ["X: 0.33"]
    rpn.keys("3 *")
    assert format_stack_lines(rpn.stack, 2) == ["X: 1.00"]
    assert rpn.records[1] == RpnRecord(
        f"{THIRD} * 3", "0.9999999999999999999999999999", "3 *"
    )


@pytest.mark.parametrize(
    ("y", "operator", "x", "expected"),
    [
        ("0.1", "+", "0.2", "0.3"),
        ("0.3", "-", "0.1", "0.2"),
        ("1.1", "*", "1.1", "1.21"),
        ("0.07", "*", "100", "7"),
        ("4.35", "*", "100", "435"),
        ("1.005", "*", "1000", "1005"),
        ("1", "/", "3", THIRD),
        ("2", "/", "3", "0.6666666666666666666666666667"),
        ("5", "-", "-5", "10"),
        ("-2", "^", "3", "-8"),
        ("2", "^", "0.5", "1.414213562373095048801688724"),
        (
            "1234567890123456789012345678", "-",
            "1234567890123456789012345677", "1",
        ),
    ],
)
def test_v37_rpn_result_is_identical_to_the_algebraic_result(
    y, operator, x, expected
):
    def typed(number: str) -> str:
        return f"{number[1:]} sign" if number.startswith("-") else number

    rpn = Rpn().keys(f"{typed(y)} ENTER {typed(x)} {operator}")
    (record,) = rpn.records
    algebraic = result_text(evaluate(parse_expression(f"{y} {operator} {x}")))
    assert record.result == algebraic == expected
    assert record.result == result_string([y, operator, x])
    assert record.expression == f"{y} {operator} {x}"
    assert rpn.levels == [algebraic]


def test_v40_keystroke_log_keeps_the_newest_keys():
    rpn = Rpn().keys("1 " + "ENTER " * 71 + "+")
    (record,) = rpn.records
    tokens = record.rpn_input.split(" ")
    assert (record.expression, record.result) == ("1 + 1", "2")
    assert len(tokens) == MAX_KEYS == 64
    assert tokens[0] == "..."
    assert tokens[1] == "ENTER"
    assert tokens[-1] == "+"


def test_v42_lift_after_keys_other_than_enter():
    rpn = Rpn().keys("5 ENTER sign")
    assert rpn.stack == RpnStack(("-5", "5"), None, True, ("5", "ENTER", "CHS"))
    rpn.keys("3")
    assert (rpn.levels, rpn.stack.entry) == (["-5", "5"], "3")
    assert rpn.stack.visible_y == "-5"
    assert Rpn().keys("0 ENTER C sign").stack == RpnStack()
    rpn = Rpn().keys("7 ENTER sign sign")
    assert (rpn.levels, rpn.stack.lift) == (["7", "7"], True)


def test_v43_cancelled_entry_leaves_no_trace():
    rpn = Rpn().keys("5 ENTER 3 bksp")
    assert rpn.stack == RpnStack(("5",), None, True, ("5", "ENTER"))
    rpn.fails("+", "Too few operands")
    rpn.keys("ENTER +")
    assert rpn.tape == ["5 + 5 = 10 | 5 ENTER ENTER +"]


def test_w3_negative_zero_result_follows_algebraic_mode():
    rpn = Rpn().keys("0 ENTER 5 sign *")
    assert rpn.tape == ["0 * -5 = 0 | 0 ENTER -5 *"]
    assert result_text(evaluate(parse_expression("0 * -5"))) == "0"
    assert rpn.levels == ["0"]
    rpn.keys("sign")
    assert rpn.levels == ["0"]
    assert rpn.stack.keys == ("CHS",)


def test_negative_zero_result_is_not_kept_as_an_operand():
    rpn = Rpn().keys("0 ENTER 5 sign * 3 *")
    assert rpn.tape == [
        "0 * -5 = 0 | 0 ENTER -5 *",
        "0 * 3 = 0 | 3 *",
    ]


@pytest.mark.parametrize(
    ("keys", "result", "level"),
    [
        ("1 . 5 0 sign ENTER 0 *", "0", "0"),
        ("1 0 sign ENTER 3 1 ^ 0 *", "0", "0"),
        ("0 sign ENTER 5 /", "0", "0"),
    ],
)
def test_zero_results_go_on_the_stack_without_a_sign(keys, result, level):
    rpn = Rpn().keys(keys)
    assert rpn.records[-1].result == result
    assert rpn.levels == [level]
    assert rpn.keys("2 /").records[-1].expression == f"{level} / 2"


def test_sign_change_of_an_exponent_zero_gives_zero():
    rpn = Rpn().keys("1 0 ENTER 3 0 ^ 0 *")
    assert rpn.levels == ["0"]
    assert rpn.keys("sign").levels == ["0"]


def test_reused_number_beyond_28_digits_is_rounded_once():
    rounded = "1.234567890123456789012345679E+29"
    rpn = Rpn().reuse("123456789012345678901234567895")
    assert rpn.levels == [rounded]
    assert rpn.keys("sign").levels == ["-" + rounded]
    assert rpn.keys("sign").levels == [rounded]
    assert rpn.stack.keys == (rounded, "CHS", "CHS")


def test_reused_negative_number_beyond_28_digits_matches_text_evaluation():
    rpn = Rpn().reuse("-1000000000000000000000000000.49").keys("0 . 5 +")
    (record,) = rpn.records
    assert record.expression == "-1000000000000000000000000000 + 0.5"
    assert_algebraic_parity(record)


def test_random_keys_always_give_tape_lines_the_text_evaluator_reproduces():
    keys = [
        *"0123456789", ".", "sign", "enter", "swap", "drop", "log", "backspace",
        "+", "-", "*", "/", "^",
    ]
    reused = ["-0", "0E+27", "-0.00", "1E+30", "-123456789012345678901234567895"]
    rng = random.Random(20261123)
    lines = 0
    for _ in range(400):
        stack = RpnStack()
        for _ in range(60):
            try:
                if rng.random() < 0.03:
                    step = stack.reuse(rng.choice(reused))
                else:
                    step = stack.press(rng.choice(keys))
            except EvaluationError:
                continue
            stack = step.stack
            assert not any(level.startswith("-") and is_zero_text(level)
                           for level in stack.levels)
            if step.record is not None:
                assert_algebraic_parity(step.record)
                lines += 1
    assert lines > 1000


def test_w4_sign_change_of_a_zero_with_decimals_gives_zero():
    rpn = Rpn().keys("1 . 5 0 ENTER 1 . 5 0 -")
    assert rpn.tape == ["1.5 - 1.5 = 0 | 1.5 ENTER 1.5 -"]
    assert rpn.keys("sign").levels == ["0"]


def test_w5_exponent_notation_results_are_valid_operands():
    rpn = Rpn().keys("1 0 ENTER 3 0 ^ 2 *")
    assert rpn.tape == [
        "10 ^ 30 = 1E+30 | 10 ENTER 30 ^",
        "1E+30 * 2 = 2E+30 | 2 *",
    ]


def test_w6_invalid_exponentiation_names_the_operands():
    rpn = Rpn().keys("8 sign ENTER 0 . 5")
    rpn.fails("^", "Invalid exponentiation: -8 ^ 0.5")
    assert (rpn.levels, rpn.stack.entry) == (["-8"], "0.5")


def test_w7_guard_keys():
    rpn = Rpn()
    rpn.fails("(", "Invalid input: (")
    rpn.fails(")", "Invalid input: )")
    with pytest.raises(EvaluationError, match="Invalid input: percent"):
        RpnStack().press("percent")
    rpn.keys("5 = 3 +")
    assert rpn.tape == ["5 + 3 = 8 | 5 ENTER 3 +"]


def test_w8_reuse_stores_the_canonical_number():
    assert RpnStack().reuse("7.00").stack.levels == ("7",)
    assert RpnStack().reuse("-0").stack.levels == ("0",)
    assert RpnStack().reuse("1E+30").stack.levels == ("1E+30",)
    with pytest.raises(EvaluationError, match="Invalid number: abc"):
        RpnStack().reuse("abc")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("0.", "0"), ("-0", "0"), ("-0.00", "0"), ("1.50", "1.5"),
        ("007", "7"), ("-5", "-5"), ("5.", "5"), ("0.5", "0.5"),
        ("0E+27", "0"), ("-0E-8", "0"), ("1E+30", "1E+30"), ("-7.00", "-7"),
        ("123456789012345678901234567895", "1.234567890123456789012345679E+29"),
    ],
)
def test_w9_canon(text, expected):
    assert canon(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("0", True), ("-0", True), ("0.", True), ("-0.00", True),
        (".0", True), ("000", True), ("", False), ("-", False),
        (".", False), ("0.01", False), ("10", False), ("0E+3", True),
        ("-0E+27", True), ("0.00E-8", True), ("1E+3", False), ("0E", False),
    ],
)
def test_is_zero_text(text, expected):
    assert is_zero_text(text) is expected


def test_stack_is_immutable_and_failed_key_returns_no_new_stack():
    stack = RpnStack().press("5").stack
    with pytest.raises(AttributeError):
        stack.entry = "6"  # type: ignore[misc]
    with pytest.raises(EvaluationError):
        stack.press("+")
    assert stack == RpnStack((), "5")


def lines_of(records) -> list[str]:
    for record in records:
        assert_algebraic_parity(record)
    return [f"{r.expression} = {r.result} | {r.rpn_input}" for r in records]


@pytest.mark.parametrize(
    ("line", "levels", "tape"),
    [
        pytest.param("3 4 +", ("7",), ["3 + 4 = 7 | 3 4 +"], id="L1"),
        pytest.param(
            "3 enter 4 +", ("7",), ["3 + 4 = 7 | 3 ENTER 4 +"], id="L2-lower",
        ),
        pytest.param(
            "3 ENTER 4 +", ("7",), ["3 + 4 = 7 | 3 ENTER 4 +"], id="L2-upper",
        ),
        pytest.param(
            "3 ENTER 4 + 5 *", ("35",),
            ["3 + 4 = 7 | 3 ENTER 4 +", "7 * 5 = 35 | 5 *"], id="L3",
        ),
        pytest.param(
            "-5 3 *", ("-15",), ["-5 * 3 = -15 | -5 3 *"], id="L5-negative",
        ),
        pytest.param("3 -5 -", ("8",), ["3 - -5 = 8 | 3 -5 -"], id="L5-minus"),
        pytest.param(
            "-.5 2 *", ("-1",), ["-0.5 * 2 = -1 | -0.5 2 *"], id="L5-point",
        ),
        pytest.param(
            "8 2 swap /", ("0.25",), ["2 / 8 = 0.25 | 8 2 SWAP /"], id="L6-swap",
        ),
        pytest.param(
            "1 2 3 drop +", ("3",), ["1 + 2 = 3 | 1 2 3 DROP +"], id="L6-drop",
        ),
        pytest.param(
            "100 log", ("2",), ["log ( 100 ) = 2 | 100 LOG"],
            id="L6-log",
        ),
        pytest.param("2 enter *", ("4",), ["2 * 2 = 4 | 2 ENTER *"], id="L6-enter"),
        pytest.param(
            "1 2 3 4 5 + + +", ("14", "2", "2", "2"),
            ["4 + 5 = 9 | 1 2 3 4 5 +", "3 + 9 = 12 | +", "2 + 12 = 14 | +"],
            id="L7",
        ),
        pytest.param("3 4 + clear", (), ["3 + 4 = 7 | 3 4 +"], id="L8"),
        pytest.param(
            "0.10 0.20 +", ("0.3",), ["0.1 + 0.2 = 0.3 | 0.1 0.2 +"],
            id="L10-zeros",
        ),
        pytest.param("-0 5 +", ("5",), ["0 + 5 = 5 | 0 5 +"], id="L10-negzero"),
        pytest.param("5. 2 +", ("7",), ["5 + 2 = 7 | 5 2 +"], id="L10-point"),
        pytest.param(" \t3   4\t+ ", ("7",), ["3 + 4 = 7 | 3 4 +"], id="spaces"),
    ],
)
def test_run_line(line, levels, tape):
    stack, records = run_line(RpnStack(), line)
    assert stack.levels == levels
    assert stack.entry is None
    assert lines_of(records) == tape


def test_l4_numbers_stay_on_the_stack_between_lines():
    stack, records = run_line(RpnStack(), "1 2 3")
    assert stack == RpnStack(("3", "2", "1"), None, True, ("1", "2", "3"))
    assert records == ()
    stack, records = run_line(stack, "+")
    assert stack.levels == ("5", "1")
    assert lines_of(records) == ["2 + 3 = 5 | 1 2 3 +"]


def test_l6_chs_changes_the_sign_of_x():
    stack, records = run_line(RpnStack(), "7 chs")
    assert stack.levels == ("-7",)
    assert stack.keys == ("7", "CHS")
    assert records == ()


_NEEDS_OPERANDS = [
    ("+", "Too few operands"),
    ("-", "Too few operands"),
    ("- 3", "Too few operands"),
]
_ALWAYS_REFUSED = [
    ("5 0 /", "Division by zero"),
    ("3 x", "Invalid input: x"),
    ("1e5", "Invalid input: 1e5"),
    ("1.5.2", "Invalid input: 1.5.2"),
    ("--5", "Invalid input: --5"),
    ("3 ( 4", "Invalid input: ("),
    ("3 4 =", "Invalid input: ="),
    ("1" * 29, "Invalid input: " + "1" * 29),
    ("3 4 + 0 /", "Division by zero"),
    ("", "Empty expression"),
    ("   ", "Empty expression"),
    ("1 " * 129, "Expression exceeds 128 tokens"),
    ("1" * 2049, "Expression exceeds 2048 characters"),
]


def assert_line_refused(start: RpnStack, line: str, message: str) -> None:
    before = RpnStack(start.levels, start.entry, start.lift, start.keys)
    with pytest.raises(EvaluationError) as error:
        run_line(start, line)
    assert str(error.value) == message
    assert start == before


@pytest.mark.parametrize(("line", "message"), _NEEDS_OPERANDS + _ALWAYS_REFUSED)
def test_l9_a_failed_line_is_refused_on_an_empty_stack(line, message):
    assert_line_refused(RpnStack(), line, message)


@pytest.mark.parametrize(("line", "message"), _ALWAYS_REFUSED)
def test_l9_a_failed_line_leaves_a_filled_stack_unchanged(line, message):
    assert_line_refused(RpnStack(("9", "8"), keys=("9", "8")), line, message)


def test_run_line_accepts_the_largest_allowed_line():
    stack, _ = run_line(RpnStack(), "1 " * 128)
    assert stack.levels == ("1", "1", "1", "1")
    run_line(RpnStack(), "1" * 28)


@pytest.mark.parametrize(
    ("levels", "places", "expected"),
    [
        ((), None, []),
        (("3",), None, ["X: 3"]),
        (("3", "2", "1"), None, ["Z: 1", "Y: 2", "X: 3"]),
        (("4", "3", "2", "1"), 2, ["T: 1.00", "Z: 2.00", "Y: 3.00", "X: 4.00"]),
    ],
)
def test_format_stack_lines(levels, places, expected):
    assert format_stack_lines(RpnStack(levels), places) == expected
