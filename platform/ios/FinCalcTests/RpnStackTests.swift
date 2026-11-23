import Foundation
import Testing

@testable import FinCalc

/// Drives an `RpnStack` the way the session does: one key at a time, with
/// the status cleared before each key and set when a key is rejected.
///
/// Keys are written as in the shared RPN test vectors, separated by spaces:
/// ENTER, SWAP, DROP, bksp, sign, log, C, and digits, "." and operators. A
/// word such as "100" or "0.25" is typed one character at a time.
struct RpnMachine {
    var stack = RpnStack()
    var tape: [RpnTapeRecord] = []
    var status = ""

    private static let namedKeys = [
        "ENTER": "enter",
        "SWAP": "swap",
        "DROP": "drop",
        "bksp": "backspace",
        "sign": "sign",
        "log": "log",
        "C": "C",
    ]

    /// The keys that type a number; a negative one ends with the sign key.
    static func typing(_ number: String) -> String {
        number.hasPrefix("-") ? "\(number.dropFirst()) sign" : number
    }

    mutating func press(_ keys: String) {
        for word in keys.split(separator: " ").map(String.init) {
            if let key = Self.namedKeys[word] {
                pressKey(key)
            } else {
                for character in word {
                    pressKey(String(character))
                }
            }
        }
    }

    mutating func pressKey(_ key: String) {
        status = ""
        do {
            if let record = try stack.press(key) {
                tape.append(record)
            }
        } catch {
            status = Self.message(of: error)
        }
    }

    mutating func reuse(_ value: String) {
        status = ""
        do {
            try stack.reuse(value)
        } catch {
            status = Self.message(of: error)
        }
    }

    /// Tape entries as "expression = result | rpn_input".
    var lines: [String] {
        tape.map { "\($0.expression) = \($0.result) | \($0.rpnInput)" }
    }

    private static func message(of error: any Error) -> String {
        (error as? EvaluationError)?.message ?? error.localizedDescription
    }
}

/// Each tape expression, split on spaces and evaluated algebraically, must
/// give the stored result exactly.
private func expectReproducible(_ tape: [RpnTapeRecord]) throws {
    for record in tape {
        let tokens = record.expression.split(separator: " ").map(String.init)
        #expect(try RpnStack.resultString(tokens) == record.result)
    }
}

private func run(_ keys: String) -> RpnMachine {
    var machine = RpnMachine()
    machine.press(keys)
    return machine
}

@Suite("RPN stack helpers")
struct RpnStackHelperTests {
    @Test(arguments: ["0", "-0", "0.", "-0.00", "000", "0.0"])
    func zeroTexts(text: String) {
        #expect(RpnStack.isZeroText(text))
    }

    @Test(arguments: ["", "-", ".", "-.", "1", "0.1", "0..0", "0-", "--0", "0e0"])
    func nonZeroTexts(text: String) {
        #expect(!RpnStack.isZeroText(text))
    }

    @Test(arguments: [
        ("0.", "0"),
        ("-0", "0"),
        ("1.50", "1.5"),
        ("007", "7"),
        ("-5", "-5"),
        ("5.", "5"),
        ("0.25", "0.25"),
    ])
    func canon(text: String, expected: String) throws {
        #expect(try RpnStack.canon(text) == expected)
    }

    @Test func canonRejectsText() {
        #expect(throws: EvaluationError("Invalid number: abc")) {
            try RpnStack.canon("abc")
        }
    }

    @Test func emptyState() {
        let stack = RpnStack()
        #expect(stack.levels.isEmpty)
        #expect(stack.entry == nil)
        #expect(stack.liftEnabled)
        #expect(stack.keys.isEmpty)
        #expect(stack.isEmpty)
        #expect(stack.visibleX == nil)
        #expect(stack.visibleY == nil)
    }
}

@Suite("RPN stack vectors")
struct RpnStackVectorTests {
    // Final stack (X first) and tape of the shared vectors that end in a
    // calculation.
    @Test(arguments: [
        // V1
        ("3 ENTER 4 +", ["7"], ["3 + 4 = 7 | 3 ENTER 4 +"]),
        // V2
        (
            "0 . 1 ENTER 0 . 2 +", ["0.3"],
            ["0.1 + 0.2 = 0.3 | 0.1 ENTER 0.2 +"],
        ),
        // V3
        (
            ". 5 ENTER . 2 5 -", ["0.25"],
            ["0.5 - 0.25 = 0.25 | 0.5 ENTER 0.25 -"],
        ),
        // V4
        (
            "3 ENTER 4 + 5 *", ["35"],
            ["3 + 4 = 7 | 3 ENTER 4 +", "7 * 5 = 35 | 5 *"],
        ),
        // V5
        (
            "1 ENTER 2 ENTER 3 + +", ["6"],
            ["2 + 3 = 5 | 1 ENTER 2 ENTER 3 +", "1 + 5 = 6 | +"],
        ),
        // V6
        (
            "2 ENTER 3 + 4 ENTER 5 + *", ["45"],
            [
                "2 + 3 = 5 | 2 ENTER 3 +",
                "4 + 5 = 9 | 4 ENTER 5 +",
                "5 * 9 = 45 | *",
            ],
        ),
        // V7
        ("5 sign ENTER 3 *", ["-15"], ["-5 * 3 = -15 | -5 ENTER 3 *"]),
        // V8
        ("3 ENTER 5 sign -", ["8"], ["3 - -5 = 8 | 3 ENTER -5 -"]),
        // V9
        (
            "3 ENTER 4 + sign 2 *", ["-14"],
            ["3 + 4 = 7 | 3 ENTER 4 +", "-7 * 2 = -14 | CHS 2 *"],
        ),
        // V10
        ("2 sign ENTER 2 ^", ["4"], ["-2 ^ 2 = 4 | -2 ENTER 2 ^"]),
        // V11
        (
            "1 ENTER 3 / 3 *", ["0.9999999999999999999999999999"],
            [
                "1 / 3 = 0.3333333333333333333333333333 | 1 ENTER 3 /",
                "0.3333333333333333333333333333 * 3 = "
                    + "0.9999999999999999999999999999 | 3 *",
            ],
        ),
        // V12
        (
            "2 ENTER 3 /", ["0.6666666666666666666666666667"],
            ["2 / 3 = 0.6666666666666666666666666667 | 2 ENTER 3 /"],
        ),
        // V13, continued after the error
        ("5 ENTER 0 / bksp 2 /", ["2.5"], ["5 / 2 = 2.5 | 5 ENTER 2 /"]),
        // V15, continued after the error
        ("3 + ENTER +", ["6"], ["3 + 3 = 6 | 3 ENTER +"]),
        // V16
        (
            "4 ENTER ENTER ENTER * *", ["64", "4", "4", "4"],
            ["4 * 4 = 16 | 4 ENTER ENTER ENTER *", "4 * 16 = 64 | *"],
        ),
        // V17
        ("8 ENTER 2 SWAP /", ["0.25"], ["2 / 8 = 0.25 | 8 ENTER 2 SWAP /"]),
        // V19
        (
            "1 ENTER 2 ENTER 3 DROP +", ["3"],
            ["1 + 2 = 3 | 1 ENTER 2 ENTER 3 DROP +"],
        ),
        // V21
        (
            "1 ENTER 2 ENTER 3 ENTER 4 ENTER 5 + + +", ["14", "2", "2", "2"],
            [
                "4 + 5 = 9 | 1 ENTER 2 ENTER 3 ENTER 4 ENTER 5 +",
                "3 + 9 = 12 | +",
                "2 + 12 = 14 | +",
            ],
        ),
        // V25
        ("1 2 bksp 3 ENTER 2 +", ["15"], ["13 + 2 = 15 | 13 ENTER 2 +"]),
        // V28
        ("0 sign ENTER 5 +", ["5"], ["0 + 5 = 5 | 0 ENTER 5 +"]),
        // V43, continued after the error
        (
            "5 ENTER 3 bksp + ENTER +", ["10"],
            ["5 + 5 = 10 | 5 ENTER ENTER +"],
        ),
    ] as [(String, [String], [String])])
    func finalStackAndTape(
        keys: String,
        levels: [String],
        tape: [String],
    ) throws {
        let machine = run(keys)
        #expect(machine.stack.levels == levels)
        #expect(machine.stack.entry == nil)
        #expect(machine.stack.liftEnabled)
        #expect(machine.stack.keys.isEmpty)
        #expect(machine.lines == tape)
        try expectReproducible(machine.tape)
    }

    @Test func v1StepByStep() {
        var machine = RpnMachine()
        machine.press("3")
        #expect(machine.stack.entry == "3")
        #expect(machine.stack.levels.isEmpty)
        #expect(machine.stack.visibleX == "3")
        #expect(machine.stack.visibleY == nil)

        machine.press("ENTER")
        #expect(machine.stack.levels == ["3", "3"])
        #expect(machine.stack.entry == nil)
        #expect(!machine.stack.liftEnabled)
        #expect(machine.stack.visibleX == "3")
        #expect(machine.stack.visibleY == "3")

        machine.press("4")
        #expect(machine.stack.levels == ["3"])
        #expect(machine.stack.entry == "4")
        #expect(machine.stack.liftEnabled)
        #expect(machine.stack.visibleX == "4")
        #expect(machine.stack.visibleY == "3")
        #expect(machine.tape.isEmpty)

        machine.press("+")
        #expect(machine.stack.levels == ["7"])
        #expect(machine.stack.entry == nil)
        #expect(machine.stack.liftEnabled)
        #expect(machine.stack.keys.isEmpty)
        #expect(machine.stack.visibleX == "7")
        #expect(machine.stack.visibleY == nil)
        #expect(machine.lines == ["3 + 4 = 7 | 3 ENTER 4 +"])
    }

    @Test func v3DecimalPointStartsWithZero() {
        var machine = RpnMachine()
        machine.press(". 5")
        #expect(machine.stack.entry == "0.5")
        machine.press("ENTER . 2 5")
        #expect(machine.stack.entry == "0.25")
        #expect(machine.stack.levels == ["0.5"])
    }

    @Test func v4NumberAfterResultLiftsStack() {
        let machine = run("3 ENTER 4 + 5")
        #expect(machine.stack.levels == ["7"])
        #expect(machine.stack.entry == "5")
        #expect(machine.stack.visibleX == "5")
        #expect(machine.stack.visibleY == "7")
    }

    @Test func v5FirstOperatorKeepsDeeperLevel() {
        let machine = run("1 ENTER 2 ENTER 3 +")
        #expect(machine.stack.levels == ["5", "1"])
    }

    @Test func v7SignWhileTypingIsPartOfTheNumber() {
        var machine = RpnMachine()
        machine.press("5 sign")
        #expect(machine.stack.entry == "-5")
        #expect(machine.stack.keys.isEmpty)
        machine.press("sign")
        #expect(machine.stack.entry == "5")
    }

    @Test func v9SignChangeOfResultIsLoggedWithoutTapeEntry() {
        var machine = run("3 ENTER 4 +")
        machine.press("sign")
        #expect(machine.stack.levels == ["-7"])
        #expect(machine.stack.keys == ["CHS"])
        #expect(machine.tape.count == 1)
    }

    @Test func v13DivisionByZeroChangesNothing() {
        var machine = run("5 ENTER 0")
        let before = machine.stack
        machine.press("/")
        #expect(machine.status == "Division by zero")
        #expect(machine.stack == before)
        #expect(machine.stack.levels == ["5"])
        #expect(machine.stack.entry == "0")
        #expect(machine.stack.liftEnabled)
        #expect(machine.stack.keys == ["5", "ENTER"])
        #expect(machine.stack.visibleX == "0")
        #expect(machine.stack.visibleY == "5")
        #expect(machine.tape.isEmpty)

        machine.press("bksp")
        #expect(machine.status.isEmpty)
        #expect(machine.stack.entry == nil)
        #expect(machine.stack.levels == ["5"])
        #expect(machine.stack.visibleX == "5")
        #expect(machine.stack.visibleY == nil)

        machine.press("2 /")
        #expect(machine.stack.levels == ["2.5"])
        #expect(machine.lines == ["5 / 2 = 2.5 | 5 ENTER 2 /"])
    }

    @Test(arguments: ["+", "-", "*", "/", "^", "log", "swap", "drop", "enter"])
    func v14TooFewOperandsOnEmptyStack(key: String) {
        var machine = RpnMachine()
        machine.pressKey(key)
        #expect(machine.status == "Too few operands")
        #expect(machine.stack == RpnStack())
        #expect(machine.tape.isEmpty)
    }

    @Test(arguments: ["sign", "backspace", "C"])
    func v14KeysWithoutEffectOnEmptyStack(key: String) {
        var machine = RpnMachine()
        machine.pressKey(key)
        #expect(machine.status.isEmpty)
        #expect(machine.stack == RpnStack())
        #expect(machine.tape.isEmpty)
    }

    @Test func v15OperatorWithOneNumberKeepsTheEntry() {
        var machine = run("3 +")
        #expect(machine.status == "Too few operands")
        #expect(machine.stack.entry == "3")
        #expect(machine.stack.levels.isEmpty)
        #expect(machine.stack.visibleX == "3")
        #expect(machine.tape.isEmpty)

        machine.press("ENTER +")
        #expect(machine.stack.levels == ["6"])
        #expect(machine.lines == ["3 + 3 = 6 | 3 ENTER +"])
    }

    @Test func v16FullStackReplicatesTop() {
        var machine = run("4 ENTER ENTER ENTER")
        #expect(machine.stack.levels == ["4", "4", "4", "4"])
        #expect(!machine.stack.liftEnabled)
        machine.press("*")
        #expect(machine.stack.levels == ["16", "4", "4", "4"])
        machine.press("*")
        #expect(machine.stack.levels == ["64", "4", "4", "4"])
    }

    @Test func v17SwapExchangesXAndY() {
        let machine = run("8 ENTER 2 SWAP")
        #expect(machine.stack.levels == ["8", "2"])
        #expect(machine.stack.liftEnabled)
    }

    @Test func v18SwapNeedsTwoNumbers() {
        let machine = run("8 SWAP")
        #expect(machine.status == "Too few operands")
        #expect(machine.stack.entry == "8")
        #expect(machine.stack.levels.isEmpty)
    }

    @Test func v19DropRemovesX() {
        let machine = run("1 ENTER 2 ENTER 3 DROP")
        #expect(machine.stack.levels == ["2", "1"])
    }

    @Test func v20DropOnFullStackReplicatesTop() {
        var machine = run("1 ENTER 2 ENTER 3 ENTER 4")
        #expect(machine.stack.levels == ["3", "2", "1"])
        #expect(machine.stack.entry == "4")

        machine.press("DROP")
        #expect(machine.stack.levels == ["3", "2", "1", "1"])
        #expect(machine.stack.visibleX == "3")
        #expect(machine.stack.visibleY == "2")
        machine.press("DROP")
        #expect(machine.stack.levels == ["2", "1", "1", "1"])
        machine.press("DROP")
        #expect(machine.stack.levels == ["1", "1", "1", "1"])
        #expect(machine.tape.isEmpty)

        machine.press("C")
        #expect(machine.stack == RpnStack())
    }

    @Test func v21FifthNumberPushesOutTheOldest() {
        var machine = run("1 ENTER 2 ENTER 3 ENTER 4 ENTER")
        #expect(machine.stack.levels == ["4", "4", "3", "2"])
        #expect(!machine.stack.liftEnabled)
        machine.press("5")
        #expect(machine.stack.levels == ["4", "3", "2"])
        #expect(machine.stack.entry == "5")
        machine.press("+")
        #expect(machine.stack.levels == ["9", "3", "2", "2"])
        machine.press("+")
        #expect(machine.stack.levels == ["12", "2", "2", "2"])
        machine.press("+")
        #expect(machine.stack.levels == ["14", "2", "2", "2"])
    }

    @Test func v22LogMatchesAlgebraicResult() throws {
        let machine = run("1 0 0 log")
        let expected = try RpnStack.resultString(["log", "(", "100", ")"])
        #expect(DecimalMath.parseNumber(expected) == 2)
        #expect(machine.stack.levels == [expected])
        #expect(machine.stack.liftEnabled)
        #expect(machine.lines == ["log ( 100 ) = \(expected) | 100 LOG"])
        try expectReproducible(machine.tape)
    }

    @Test func v23LogOfZeroChangesNothing() {
        let machine = run("0 log")
        #expect(machine.status == "Log undefined for non-positive values")
        #expect(machine.stack.entry == "0")
        #expect(machine.stack.levels.isEmpty)
        #expect(machine.tape.isEmpty)
    }

    @Test func v24ClearEntryThenClearAll() {
        var machine = run("3 ENTER 4 C")
        #expect(machine.stack.levels == ["3"])
        #expect(machine.stack.entry == nil)
        #expect(machine.stack.visibleX == "3")
        #expect(machine.stack.visibleY == nil)

        machine.press("C")
        #expect(machine.stack == RpnStack())
        #expect(machine.stack.visibleX == nil)

        machine.press("+")
        #expect(machine.status == "Too few operands")
    }

    @Test func v25BackspaceEditsTheEntry() {
        var machine = RpnMachine()
        machine.press("1 2")
        #expect(machine.stack.entry == "12")
        machine.press("bksp")
        #expect(machine.stack.entry == "1")
        machine.press("3")
        #expect(machine.stack.entry == "13")
    }

    @Test func v26SecondDecimalPointIsRejected() {
        let machine = run("1 . 5 .")
        #expect(machine.status == "Invalid input: .")
        #expect(machine.stack.entry == "1.5")
    }

    @Test func v27EntryStopsAt28Digits() {
        let digits = "1234567890123456789012345678"
        var machine = run(digits)
        #expect(machine.stack.entry == digits)
        #expect(machine.status.isEmpty)
        machine.press("9")
        #expect(machine.status == "Invalid input: 9")
        #expect(machine.stack.entry == digits)

        // The sign and the decimal point do not count as digits.
        machine.press("sign")
        #expect(machine.stack.entry == "-" + digits)
        machine.press("9")
        #expect(machine.status == "Invalid input: 9")
        machine.press(".")
        #expect(machine.status.isEmpty)
        machine.press("9")
        #expect(machine.status == "Invalid input: 9")
        #expect(machine.stack.entry == "-" + digits + ".")
    }

    @Test func v28NegativeZeroIsStoredAsZero() {
        var machine = RpnMachine()
        machine.press("0 sign")
        #expect(machine.stack.entry == "-0")
        machine.press("ENTER")
        #expect(machine.stack.levels == ["0", "0"])
        #expect(machine.stack.keys == ["0", "ENTER"])
    }

    @Test func v29ZeroToThePowerOfZero() {
        let machine = run("0 ENTER 0 ^")
        #expect(machine.status == "Invalid exponentiation: 0 ^ 0")
        #expect(machine.stack.levels == ["0"])
        #expect(machine.stack.entry == "0")
        #expect(machine.tape.isEmpty)
    }

    @Test func v30ResultOutOfRange() {
        let machine = run("9 ENTER 9 9 9 9 9 9 9 ^")
        #expect(machine.status == "Result out of range")
        #expect(machine.stack.levels == ["9"])
        #expect(machine.stack.entry == "9999999")
        #expect(machine.tape.isEmpty)
    }

    @Test func v31ReuseOnEmptyStack() throws {
        let third = "0.3333333333333333333333333333"
        var machine = RpnMachine()
        machine.reuse(third)
        #expect(machine.stack.levels == [third])
        #expect(machine.stack.entry == nil)
        #expect(machine.stack.liftEnabled)
        #expect(machine.tape.isEmpty)

        machine.press("3 *")
        #expect(machine.lines == [
            "\(third) * 3 = 0.9999999999999999999999999999 | \(third) 3 *",
        ])
        try expectReproducible(machine.tape)
    }

    @Test func v32ReuseAfterResultLiftsStack() {
        var machine = run("2 ENTER 3 +")
        #expect(machine.stack.levels == ["5"])
        machine.reuse("7")
        #expect(machine.stack.levels == ["7", "5"])
        #expect(machine.stack.visibleX == "7")
        #expect(machine.stack.visibleY == "5")
        machine.press("*")
        #expect(machine.lines.last == "5 * 7 = 35 | 7 *")
    }

    @Test func v33ReuseReplacesTheNumberBeingTyped() {
        var machine = run("9 7")
        machine.reuse("42")
        #expect(machine.stack.entry == nil)
        #expect(machine.stack.levels == ["42"])
        machine.press("3")
        #expect(machine.stack.entry == "3")
        #expect(machine.stack.levels == ["42"])
        #expect(machine.stack.visibleX == "3")
        #expect(machine.stack.visibleY == "42")
    }

    @Test func v34ReuseAfterEnterOverwritesX() {
        var machine = run("2 ENTER")
        #expect(machine.stack.levels == ["2", "2"])
        #expect(!machine.stack.liftEnabled)
        machine.reuse("7")
        #expect(machine.stack.levels == ["7", "2"])
        #expect(machine.stack.liftEnabled)
        machine.press("+")
        #expect(machine.lines == ["2 + 7 = 9 | 2 ENTER 7 +"])
    }

    @Test func reuseOfInvalidValueChangesNothing() {
        var machine = run("2 ENTER 3")
        let before = machine.stack
        machine.reuse("abc")
        #expect(machine.status == "Invalid number: abc")
        #expect(machine.stack == before)
    }

    @Test func reuseStoresTheCanonicalNumber() {
        var machine = RpnMachine()
        machine.reuse("1.50")
        machine.reuse("-0")
        #expect(machine.stack.levels == ["0", "1.5"])
        #expect(machine.stack.keys == ["1.5", "0"])
    }

    @Test(arguments: [
        ("0.1", "+", "0.2", "0.3"),
        ("0.3", "-", "0.1", "0.2"),
        ("1.1", "*", "1.1", "1.21"),
        ("0.07", "*", "100", "7"),
        ("4.35", "*", "100", "435"),
        ("1.005", "*", "1000", "1005"),
        ("1", "/", "3", nil),
        ("2", "/", "3", nil),
        ("5", "-", "-5", "10"),
        ("-2", "^", "3", "-8"),
        ("2", "^", "0.5", nil),
        (
            "1234567890123456789012345678", "-",
            "1234567890123456789012345677", "1",
        ),
    ] as [(String, String, String, String?)])
    func v37MatchesAlgebraicEvaluator(
        y: String,
        op: String,
        x: String,
        expected: String?,
    ) throws {
        let keys =
            "\(RpnMachine.typing(y)) ENTER \(RpnMachine.typing(x)) \(op)"
        let machine = run(keys)
        let algebraic = try Evaluator.evaluate([y, op, x]).description
        #expect(machine.status.isEmpty)
        #expect(machine.tape.count == 1)
        #expect(machine.tape.first?.expression == "\(y) \(op) \(x)")
        #expect(machine.tape.first?.result == algebraic)
        #expect(machine.tape.first?.rpnInput == "\(y) ENTER \(x) \(op)")
        #expect(machine.stack.levels == [algebraic])
        if let expected {
            #expect(algebraic == expected)
        }
        try expectReproducible(machine.tape)
    }

    @Test func v40KeystrokeLogKeepsTheNewest64Tokens() {
        var machine = run("1 ENTER")
        for _ in 0..<70 {
            machine.press("ENTER")
        }
        machine.press("+")
        #expect(machine.tape.count == 1)
        #expect(machine.tape.first?.expression == "1 + 1")
        #expect(machine.tape.first?.result == "2")
        let tokens = (machine.tape.first?.rpnInput ?? "")
            .split(separator: " ").map(String.init)
        #expect(tokens.count == 64)
        #expect(tokens.first == "...")
        #expect(tokens.last == "+")
        #expect(tokens.dropFirst().dropLast().allSatisfy { $0 == "ENTER" })
    }

    @Test func v42LiftAfterKeysOtherThanEnter() {
        var machine = run("5 ENTER sign")
        #expect(machine.stack.levels == ["-5", "5"])
        #expect(machine.stack.liftEnabled)
        #expect(machine.stack.keys == ["5", "ENTER", "CHS"])
        machine.press("3")
        #expect(machine.stack.levels == ["-5", "5"])
        #expect(machine.stack.entry == "3")
        #expect(machine.stack.visibleY == "-5")

        machine = RpnMachine()
        machine.press("0 ENTER C")
        #expect(machine.stack == RpnStack())
        machine.press("sign")
        #expect(machine.stack == RpnStack())
        #expect(machine.status.isEmpty)

        machine = RpnMachine()
        machine.press("7 ENTER")
        #expect(machine.stack.levels == ["7", "7"])
        machine.press("sign sign")
        #expect(machine.stack.levels == ["7", "7"])
        #expect(machine.stack.liftEnabled)
    }

    @Test func signChangeOfZeroStaysZero() {
        var machine = run("0 ENTER 5 C")
        #expect(machine.stack.levels == ["0"])
        machine.press("sign")
        #expect(machine.stack.levels == ["0"])
        #expect(machine.stack.keys == ["0", "ENTER", "CHS"])
    }

    @Test func v43CancelledEntryDoesNotBringBackTheDuplicate() {
        var machine = run("5 ENTER 3 bksp")
        #expect(machine.stack.levels == ["5"])
        #expect(machine.stack.entry == nil)
        #expect(machine.stack.liftEnabled)
        machine.press("+")
        #expect(machine.status == "Too few operands")
        machine.press("ENTER +")
        #expect(machine.lines == ["5 + 5 = 10 | 5 ENTER ENTER +"])
    }

    @Test func backspaceRemovesALoneMinusSign() {
        var machine = run("5 sign bksp")
        #expect(machine.stack.entry == nil)
        #expect(machine.stack == RpnStack())
        machine.press("0 . bksp")
        #expect(machine.stack.entry == "0")
    }

    @Test func equalsActsAsEnter() {
        var machine = run("3")
        machine.pressKey("=")
        #expect(machine.stack.levels == ["3", "3"])
        #expect(!machine.stack.liftEnabled)
        #expect(machine.stack.keys == ["3", "ENTER"])
    }

    @Test(arguments: ["(", ")"])
    func parenthesesAreRejected(key: String) {
        var machine = run("3 ENTER 4")
        let before = machine.stack
        machine.pressKey(key)
        #expect(machine.status == "Invalid input: \(key)")
        #expect(machine.stack == before)
    }

    @Test func minusKeyIsAlwaysSubtraction() {
        var machine = RpnMachine()
        machine.press("-")
        #expect(machine.status == "Too few operands")
        #expect(machine.stack == RpnStack())
    }
}

@Suite("RPN stack restore")
struct RpnStackRestoreTests {
    @Test func v41RestoresSavedState() {
        var machine = RpnMachine()
        machine.stack = RpnStack.restored(
            levels: ["5", "3"],
            entry: "7",
            liftEnabled: true,
            keys: ["5", "ENTER", "3"],
        )
        #expect(machine.stack.visibleX == "7")
        #expect(machine.stack.visibleY == "5")
        machine.press("+")
        #expect(machine.lines == ["5 + 7 = 12 | 5 ENTER 3 7 +"])
        #expect(machine.stack.levels == ["12", "3"])
    }

    @Test func restoresStateDirectlyAfterEnter() {
        let stack = RpnStack.restored(
            levels: ["2", "2", "1"],
            entry: "",
            liftEnabled: false,
            keys: ["1", "ENTER", "2", "ENTER"],
        )
        #expect(stack.levels == ["2", "2", "1"])
        #expect(stack.entry == nil)
        #expect(!stack.liftEnabled)
        #expect(stack.keys == ["1", "ENTER", "2", "ENTER"])
    }

    @Test func restoreStoresCanonicalLevels() {
        let stack = RpnStack.restored(
            levels: ["1.50", "-0"],
            entry: "",
            liftEnabled: true,
            keys: ["...", "CHS", "LOG", "SWAP", "DROP", "+", "-", "*", "/", "^"],
        )
        #expect(stack.levels == ["1.5", "0"])
        #expect(stack.keys.count == 10)
    }

    @Test func restoredStateRoundTrips() {
        let original = run("1 ENTER 2 ENTER 3 sign").stack
        let restored = RpnStack.restored(
            levels: original.levels,
            entry: original.entry ?? "",
            liftEnabled: original.liftEnabled,
            keys: original.keys,
        )
        #expect(restored == original)
    }

    @Test(arguments: [
        // An invalid level.
        (["abc"], "", true, [String]()),
        // Five levels.
        (["1", "2", "3", "4", "5"], "", true, []),
        // Lift disabled together with an entry.
        (["2", "2"], "7", false, []),
        // Lift disabled without the ENTER duplicate.
        (["2", "3"], "", false, []),
        (["2"], "", false, []),
        // Entries that are not a typed number.
        (["1"], "1.2.3", true, []),
        (["1"], "-", true, []),
        (["1"], "1e5", true, []),
        (["1"], "12345678901234567890123456789", true, []),
        // An unknown keystroke token.
        (["1"], "", true, ["ENTER", "what"]),
        // Too many keystroke tokens.
        (["1"], "", true, Array(repeating: "ENTER", count: 65)),
    ] as [([String], String, Bool, [String])])
    func invalidSavedStateGivesEmptyStack(
        levels: [String],
        entry: String,
        liftEnabled: Bool,
        keys: [String],
    ) {
        let stack = RpnStack.restored(
            levels: levels,
            entry: entry,
            liftEnabled: liftEnabled,
            keys: keys,
        )
        #expect(stack == RpnStack())
    }
}
