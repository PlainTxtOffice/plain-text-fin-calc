import Foundation
import Testing

@testable import FinCalc

/// RPN mode through the session: display lines, tape, saving, settings.
@Suite("Calculator session in RPN mode")
@MainActor
struct RpnSessionTests {
    let folder = TemporaryFolder()

    private func makeSession(
        settings: Settings = Settings(inputMode: .rpn),
    ) -> CalculatorSession {
        CalculatorSession(
            history: History(),
            settings: settings,
            historyURL: folder.file("history.json"),
            settingsURL: folder.file("settings.json"),
        )
    }

    /// Press keys written as in the shared RPN test vectors.
    private func press(_ session: CalculatorSession, _ keys: String) {
        for word in keys.split(separator: " ").map(String.init) {
            switch word {
            case "ENTER": session.enter()
            case "SWAP": session.swap()
            case "DROP": session.drop()
            case "bksp": session.backspace()
            case "sign": session.toggleSign()
            case "C": session.clear()
            case "log": session.addSymbol("log")
            default:
                for character in word {
                    session.addSymbol(String(character))
                }
            }
        }
    }

    /// The X line as the display draws it; "0" is the empty placeholder.
    private func xLine(_ session: CalculatorSession) -> String {
        session.displayText.isEmpty
            ? "0" : KeyLabels.format(session.displayText)
    }

    /// The Y line as the display draws it.
    private func yLine(_ session: CalculatorSession) -> String {
        DisplayView.yLine(session.rpnYText)
    }

    /// Tape entries as "expression = result | rpn_input".
    private func lines(_ session: CalculatorSession) -> [String] {
        session.history.entries.map {
            "\($0.expression) = \($0.result) | \($0.rpnInput ?? "")"
        }
    }

    @Test func v1DisplayTapeAndSavedHistory() {
        let session = makeSession()
        #expect(session.isRPN)
        #expect(xLine(session) == "0")
        #expect(yLine(session) == "Y:")

        press(session, "3")
        #expect(xLine(session) == "3")
        #expect(yLine(session) == "Y:")
        press(session, "ENTER")
        #expect(xLine(session) == "3")
        #expect(yLine(session) == "Y: 3")
        #expect(session.rpnLevels == ["3", "3"])
        #expect(!session.rpnLiftEnabled)
        press(session, "4")
        #expect(xLine(session) == "4")
        #expect(yLine(session) == "Y: 3")
        #expect(session.rpnLevels == ["3"])
        #expect(session.rpnEntry == "4")
        #expect(session.rpnLiftEnabled)
        #expect(session.rpnKeys == ["3", "ENTER"])
        press(session, "+")
        #expect(xLine(session) == "7")
        #expect(yLine(session) == "Y:")
        #expect(session.rpnLevels == ["7"])
        #expect(session.rpnEntry.isEmpty)
        #expect(session.rpnKeys.isEmpty)
        #expect(session.statusText.isEmpty)
        #expect(lines(session) == ["3 + 4 = 7 | 3 ENTER 4 +"])

        session.waitForPendingWrites()
        let saved = HistoryStore.loadHistory(from: folder.file("history.json"))
        #expect(saved.entries.map(\.rpnInput) == ["3 ENTER 4 +"])
        #expect(saved.entries.map(\.expression) == ["3 + 4"])
        #expect(saved.entries.map(\.result) == ["7"])
    }

    @Test func v4NumberAfterResult() {
        let session = makeSession()
        press(session, "3 ENTER 4 + 5")
        #expect(xLine(session) == "5")
        #expect(yLine(session) == "Y: 7")
        press(session, "*")
        #expect(lines(session) == [
            "3 + 4 = 7 | 3 ENTER 4 +",
            "7 * 5 = 35 | 5 *",
        ])
    }

    @Test func v7NegativeEntryShowsMinusSign() {
        let session = makeSession()
        press(session, "5 sign")
        #expect(session.displayText == "-5")
        #expect(xLine(session) == "\u{2212}5")
        press(session, "ENTER 3 *")
        #expect(lines(session) == ["-5 * 3 = -15 | -5 ENTER 3 *"])
    }

    @Test func v13ErrorShowsStatusAndKeepsState() {
        let session = makeSession()
        press(session, "5 ENTER 0 /")
        #expect(session.statusText == "Division by zero")
        #expect(xLine(session) == "0")
        #expect(yLine(session) == "Y: 5")
        #expect(session.rpnEntry == "0")
        #expect(session.rpnLevels == ["5"])
        #expect(session.rpnKeys == ["5", "ENTER"])
        #expect(session.history.entries.isEmpty)

        // Every key clears the status, backspace included.
        press(session, "bksp")
        #expect(session.statusText.isEmpty)
        #expect(xLine(session) == "5")
        #expect(yLine(session) == "Y:")
        press(session, "2 /")
        #expect(lines(session) == ["5 / 2 = 2.5 | 5 ENTER 2 /"])
    }

    @Test func v14EmptyStack() {
        let session = makeSession()
        for key in ["+", "-", "*", "/", "^", "log", "SWAP", "DROP", "ENTER"] {
            press(session, key)
            #expect(session.statusText == "Too few operands")
            #expect(session.rpnLevels.isEmpty)
            #expect(session.rpnEntry.isEmpty)
        }
        press(session, "3 +")
        #expect(session.statusText == "Too few operands")
        // The sign key clears the status too.
        press(session, "sign")
        #expect(session.statusText.isEmpty)
        #expect(session.displayText == "-3")
        #expect(session.history.entries.isEmpty)
    }

    @Test func v14KeysWithoutEffectShowNoStatus() {
        let session = makeSession()
        press(session, "sign bksp C")
        #expect(session.statusText.isEmpty)
        #expect(xLine(session) == "0")
        #expect(yLine(session) == "Y:")
    }

    @Test func v20DropDisplay() {
        let session = makeSession()
        press(session, "1 ENTER 2 ENTER 3 ENTER 4 DROP")
        #expect(session.rpnLevels == ["3", "2", "1", "1"])
        #expect(xLine(session) == "3")
        #expect(yLine(session) == "Y: 2")
        #expect(session.history.entries.isEmpty)
    }

    @Test func v24ClearEntryThenClearAll() {
        let session = makeSession()
        press(session, "3 ENTER 4 C")
        #expect(xLine(session) == "3")
        #expect(yLine(session) == "Y:")
        #expect(session.rpnLevels == ["3"])
        press(session, "C")
        #expect(session.displayText.isEmpty)
        #expect(xLine(session) == "0")
        #expect(session.rpnLevels.isEmpty)
        press(session, "+")
        #expect(session.statusText == "Too few operands")
    }

    @Test func v26AndV27RejectedKeysShowInvalidInput() {
        let session = makeSession()
        press(session, "1 . 5 .")
        #expect(session.statusText == "Invalid input: .")
        #expect(session.displayText == "1.5")
        press(session, "C 1234567890123456789012345678 9")
        #expect(session.statusText == "Invalid input: 9")
        #expect(session.displayText == "1234567890123456789012345678")
    }

    @Test func v31ReuseOnEmptyStack() {
        let session = makeSession()
        session.insertResult("0.3333333333333333333333333333")
        #expect(session.rpnLevels == ["0.3333333333333333333333333333"])
        #expect(session.rpnEntry.isEmpty)
        #expect(session.rpnLiftEnabled)
        press(session, "3 *")
        #expect(lines(session) == [
            "0.3333333333333333333333333333 * 3 = "
                + "0.9999999999999999999999999999 | "
                + "0.3333333333333333333333333333 3 *",
        ])
    }

    @Test func v32ReuseAfterResult() {
        let session = makeSession()
        press(session, "2 ENTER 3 +")
        session.insertResult("7")
        #expect(session.rpnLevels == ["7", "5"])
        #expect(xLine(session) == "7")
        #expect(yLine(session) == "Y: 5")
        press(session, "*")
        #expect(lines(session).last == "5 * 7 = 35 | 7 *")
    }

    @Test func v33ReuseWhileTyping() {
        let session = makeSession()
        press(session, "9 7")
        session.insertResult("42")
        #expect(session.rpnEntry.isEmpty)
        #expect(session.rpnLevels == ["42"])
        press(session, "3")
        #expect(session.rpnEntry == "3")
        #expect(session.rpnLevels == ["42"])
        #expect(xLine(session) == "3")
        #expect(yLine(session) == "Y: 42")
    }

    @Test func v34ReuseRightAfterEnter() {
        let session = makeSession()
        press(session, "2 ENTER")
        session.insertResult("7")
        #expect(session.rpnLevels == ["7", "2"])
        #expect(session.rpnLiftEnabled)
        press(session, "+")
        #expect(lines(session) == ["2 + 7 = 9 | 2 ENTER 7 +"])
    }

    @Test func reuseClearsStatusAndReportsInvalidValues() {
        let session = makeSession()
        press(session, "+")
        #expect(session.statusText == "Too few operands")
        session.insertResult("7")
        #expect(session.statusText.isEmpty)
        session.insertResult("abc")
        #expect(session.statusText == "Invalid number: abc")
        #expect(session.rpnLevels == ["7"])
    }

    @Test func v35DisplayRoundingKeepsFullPrecision() {
        let session = makeSession(
            settings: Settings(decimalPlaces: 2, inputMode: .rpn),
        )
        press(session, "1 ENTER 3 /")
        #expect(xLine(session) == "0.33")
        #expect(session.rpnLevels == ["0.3333333333333333333333333333"])
        press(session, "3")
        // A typed number is shown as typed; Y is rounded for display.
        #expect(xLine(session) == "3")
        #expect(yLine(session) == "Y: 0.33")
        press(session, "*")
        #expect(xLine(session) == "1.00")
        #expect(
            session.history.entries.last?.expression
                == "0.3333333333333333333333333333 * 3",
        )
        #expect(
            session.history.entries.last?.result
                == "0.9999999999999999999999999999",
        )
    }

    @Test func v36ModeSwitchClearsPendingInput() {
        let session = makeSession()
        press(session, "1 ENTER 2 + 5 ENTER 7")
        #expect(session.rpnLevels == ["5", "3"])
        #expect(session.rpnEntry == "7")
        #expect(session.history.entries.count == 1)

        // Applying settings without a mode change keeps the stack.
        session.applySettings(Settings(decimalPlaces: 2, inputMode: .rpn))
        #expect(session.rpnLevels == ["5", "3"])
        #expect(session.rpnEntry == "7")
        #expect(session.rpnKeys == ["5", "ENTER"])

        session.applySettings(Settings())
        #expect(!session.isRPN)
        #expect(session.displayText.isEmpty)
        #expect(session.inputTokens.isEmpty)
        #expect(session.history.entries.count == 1)

        session.applySettings(Settings(inputMode: .rpn))
        #expect(session.rpnLevels.isEmpty)
        #expect(session.rpnEntry.isEmpty)
        #expect(session.rpnKeys.isEmpty)
        #expect(session.rpnLiftEnabled)
        #expect(session.history.entries.count == 1)
        #expect(
            SettingsStore.loadSettings(from: folder.file("settings.json"))
                .inputMode == .rpn,
        )
    }

    @Test func v36AlgebraicInputIsClearedByModeSwitch() {
        let session = makeSession(settings: Settings())
        session.addSymbol("2")
        session.addSymbol("+")
        #expect(session.displayText == "2 +")

        // Applying settings without a mode change keeps the expression.
        session.applySettings(Settings(decimalPlaces: 2))
        #expect(session.inputTokens == ["2", "+"])

        session.applySettings(Settings(inputMode: .rpn))
        #expect(session.isRPN)
        #expect(session.rpnLevels.isEmpty)
        #expect(session.rpnEntry.isEmpty)
        #expect(session.rpnKeys.isEmpty)
        #expect(session.displayText.isEmpty)

        session.applySettings(Settings())
        #expect(session.inputTokens.isEmpty)
        #expect(session.displayText.isEmpty)
    }

    @Test func modeSwitchClearsStatus() {
        let session = makeSession()
        press(session, "+")
        #expect(session.statusText == "Too few operands")
        session.applySettings(Settings())
        #expect(session.statusText.isEmpty)
    }

    @Test(arguments: [
        ("0.1", "+", "0.2"),
        ("0.3", "-", "0.1"),
        ("1.1", "*", "1.1"),
        ("0.07", "*", "100"),
        ("4.35", "*", "100"),
        ("1.005", "*", "1000"),
        ("1", "/", "3"),
        ("2", "/", "3"),
        ("5", "-", "-5"),
        ("-2", "^", "3"),
        ("2", "^", "0.5"),
        (
            "1234567890123456789012345678", "-",
            "1234567890123456789012345677",
        ),
    ])
    func v37BothModesRecordTheSameEntry(y: String, op: String, x: String) {
        let rpn = makeSession()
        press(
            rpn,
            "\(RpnMachine.typing(y)) ENTER \(RpnMachine.typing(x)) \(op)",
        )

        let algebraic = makeSession(settings: Settings())
        press(algebraic, RpnMachine.typing(y))
        algebraic.addSymbol(op)
        press(algebraic, RpnMachine.typing(x))
        algebraic.evaluate()

        #expect(rpn.history.entries.count == 1)
        #expect(algebraic.history.entries.count == 1)
        #expect(
            rpn.history.entries.first?.expression
                == algebraic.history.entries.first?.expression,
        )
        #expect(
            rpn.history.entries.first?.result
                == algebraic.history.entries.first?.result,
        )
        #expect(rpn.displayText == algebraic.displayText)
        #expect(algebraic.history.entries.first?.rpnInput == nil)
        #expect(rpn.history.entries.first?.rpnInput != nil)
    }

    @Test func v41RestoresSavedStack() {
        let session = makeSession()
        session.restoreRPN(
            levels: ["5", "3"],
            entry: "7",
            liftEnabled: true,
            keys: ["5", "ENTER", "3"],
        )
        #expect(xLine(session) == "7")
        #expect(yLine(session) == "Y: 5")
        press(session, "+")
        #expect(lines(session) == ["5 + 7 = 12 | 5 ENTER 3 7 +"])
        #expect(session.rpnLevels == ["12", "3"])
    }

    @Test func v41InvalidSavedStackStartsEmpty() {
        let session = makeSession()
        session.restoreRPN(
            levels: ["abc"], entry: "", liftEnabled: true, keys: [],
        )
        #expect(session.rpnLevels.isEmpty)
        session.restoreRPN(
            levels: ["1", "2", "3", "4", "5"],
            entry: "",
            liftEnabled: true,
            keys: [],
        )
        #expect(session.rpnLevels.isEmpty)
        session.restoreRPN(
            levels: ["2", "2"], entry: "7", liftEnabled: false, keys: [],
        )
        #expect(session.rpnLevels.isEmpty)
        #expect(session.rpnEntry.isEmpty)
        #expect(xLine(session) == "0")
    }

    @Test func v41SavedStateOfTheOtherModeIsIgnored() {
        let algebraic = makeSession(settings: Settings())
        algebraic.restoreRPN(
            levels: ["5", "3"],
            entry: "7",
            liftEnabled: true,
            keys: ["5", "ENTER", "3"],
        )
        #expect(algebraic.rpnLevels.isEmpty)
        #expect(algebraic.rpnEntry.isEmpty)
        #expect(algebraic.displayText.isEmpty)

        let rpn = makeSession()
        rpn.restoreInput(tokens: ["2", "+"], resultPending: false)
        #expect(rpn.inputTokens.isEmpty)
        #expect(rpn.displayText.isEmpty)
    }

    /// Mirror RootView's per-value `onChange` handlers: a saved value is
    /// rewritten only when the session value it follows has changed.
    private func saveChanges(
        from before: SavedInput,
        to after: SavedInput,
        into saved: inout SavedInput,
    ) {
        if before.tokens != after.tokens { saved.tokens = after.tokens }
        if before.resultPending != after.resultPending {
            saved.resultPending = after.resultPending
        }
        if before.rpnLevels != after.rpnLevels {
            saved.rpnLevels = after.rpnLevels
        }
        if before.rpnEntry != after.rpnEntry {
            saved.rpnEntry = after.rpnEntry
        }
        if before.rpnLiftEnabled != after.rpnLiftEnabled {
            saved.rpnLiftEnabled = after.rpnLiftEnabled
        }
        if before.rpnKeys != after.rpnKeys { saved.rpnKeys = after.rpnKeys }
    }

    @Test func savedInputDescribesTheActiveModeOnly() {
        let rpn = makeSession()
        press(rpn, "5 ENTER 3 ENTER")
        #expect(rpn.savedInput == SavedInput(
            rpnLevels: "3 3 5",
            rpnLiftEnabled: false,
            rpnKeys: "5 ENTER 3 ENTER",
        ))
        press(rpn, "7")
        #expect(rpn.savedInput == SavedInput(
            rpnLevels: "3 5",
            rpnEntry: "7",
            rpnKeys: "5 ENTER 3 ENTER",
        ))

        let algebraic = makeSession(settings: Settings())
        algebraic.addSymbol("2")
        algebraic.addSymbol("+")
        #expect(algebraic.savedInput == SavedInput(tokens: "2 +"))
    }

    @Test func launchRestoresTheActiveModesSavedInput() {
        let rpn = makeSession()
        let stack = SavedInput(
            rpnLevels: "5 3", rpnEntry: "7", rpnKeys: "5 ENTER 3",
        )
        #expect(rpn.restoreSavedInput(stack) == stack)
        #expect(xLine(rpn) == "7")
        #expect(yLine(rpn) == "Y: 5")

        let algebraic = makeSession(settings: Settings())
        let expression = SavedInput(tokens: "2 +")
        #expect(algebraic.restoreSavedInput(expression) == expression)
        #expect(algebraic.displayText == "2 +")
    }

    @Test func launchDropsSavedInputOfTheOtherMode() {
        let both = SavedInput(
            tokens: "2 +",
            rpnLevels: "5 3",
            rpnEntry: "7",
            rpnKeys: "5 ENTER 3",
        )
        let algebraic = makeSession(settings: Settings())
        #expect(algebraic.restoreSavedInput(both) == SavedInput(tokens: "2 +"))
        #expect(algebraic.rpnLevels.isEmpty)
        #expect(algebraic.rpnEntry.isEmpty)

        let rpn = makeSession()
        #expect(
            rpn.restoreSavedInput(both) == SavedInput(
                rpnLevels: "5 3", rpnEntry: "7", rpnKeys: "5 ENTER 3",
            ),
        )
        #expect(rpn.inputTokens.isEmpty)
    }

    @Test func launchDropsInvalidSavedStack() {
        let session = makeSession()
        let invalid = SavedInput(rpnLevels: "abc", rpnKeys: "5 ENTER")
        #expect(session.restoreSavedInput(invalid) == SavedInput())
        #expect(session.rpnLevels.isEmpty)
    }

    @Test func launchKeepsInputTheSessionAlreadyHas() {
        let session = makeSession()
        press(session, "9")
        let saved = SavedInput(rpnLevels: "5 3")
        #expect(session.restoreSavedInput(saved) == SavedInput(rpnEntry: "9"))
        #expect(session.rpnLevels.isEmpty)
    }

    /// A stack left in saved state while the app starts in algebraic mode
    /// must not come back after a later switch to RPN mode.
    @Test func staleSavedStackIsNotRestoredAfterAModeSwitch() {
        // Saved state still holds an RPN stack, but the app starts in
        // algebraic mode.
        var saved = SavedInput(rpnLevels: "5 3", rpnKeys: "5 ENTER 3")
        let first = makeSession(settings: Settings())
        saved = first.restoreSavedInput(saved)
        #expect(saved == SavedInput())

        // Switch to RPN and type 7; only changed values are saved again.
        var before = first.savedInput
        first.applySettings(Settings(inputMode: .rpn))
        saveChanges(from: before, to: first.savedInput, into: &saved)
        before = first.savedInput
        press(first, "7")
        saveChanges(from: before, to: first.savedInput, into: &saved)
        #expect(saved == SavedInput(rpnEntry: "7"))

        // The app is ended in the background and starts again in RPN mode.
        let second = makeSession()
        #expect(second.restoreSavedInput(saved) == SavedInput(rpnEntry: "7"))
        #expect(second.rpnLevels.isEmpty)
        #expect(second.rpnEntry == "7")
        #expect(xLine(second) == "7")
        #expect(yLine(second) == "Y:")
        press(second, "+")
        #expect(second.statusText == "Too few operands")
        #expect(second.history.entries.isEmpty)
    }

    /// The same in reverse: an expression left in saved state while the
    /// app starts in RPN mode must not come back in algebraic mode.
    @Test func staleSavedExpressionIsNotRestoredAfterAModeSwitch() {
        var saved = SavedInput(tokens: "2 +")
        let first = makeSession()
        saved = first.restoreSavedInput(saved)
        #expect(saved == SavedInput())

        var before = first.savedInput
        first.applySettings(Settings())
        saveChanges(from: before, to: first.savedInput, into: &saved)
        before = first.savedInput
        first.addSymbol("7")
        saveChanges(from: before, to: first.savedInput, into: &saved)
        #expect(saved == SavedInput(tokens: "7"))

        let second = makeSession(settings: Settings())
        #expect(second.restoreSavedInput(saved) == SavedInput(tokens: "7"))
        #expect(second.inputTokens == ["7"])
    }

    @Test func v42YRegisterShowsMinusSign() {
        let session = makeSession()
        press(session, "5 ENTER sign 3")
        #expect(session.rpnLevels == ["-5", "5"])
        #expect(session.rpnEntry == "3")
        #expect(session.rpnKeys == ["5", "ENTER", "CHS"])
        #expect(yLine(session) == "Y: \u{2212}5")
    }

    @Test func evaluateActsAsEnterAndParenthesesAreRejected() {
        let session = makeSession()
        press(session, "3")
        session.evaluate()
        #expect(session.rpnLevels == ["3", "3"])
        #expect(!session.rpnLiftEnabled)
        #expect(session.history.entries.isEmpty)

        session.addSymbol("(")
        #expect(session.statusText == "Invalid input: (")
        session.addSymbol(")")
        #expect(session.statusText == "Invalid input: )")
        #expect(session.rpnLevels == ["3", "3"])
    }

    @Test func stackKeysDoNothingInAlgebraicMode() {
        let session = makeSession(settings: Settings())
        session.addSymbol("2")
        session.enter()
        session.swap()
        session.drop()
        #expect(session.inputTokens == ["2"])
        #expect(session.statusText.isEmpty)
        #expect(session.history.entries.isEmpty)
    }

    @Test func historyCapAppliesToRPNEntries() {
        let session = makeSession(
            settings: Settings(maxHistoryEntries: 2, inputMode: .rpn),
        )
        press(session, "1 ENTER 1 + 1 + 1 +")
        #expect(session.history.entries.map(\.result) == ["3", "4"])
    }

    @Test func displayAccessibilityText() {
        #expect(
            DisplayView.accessibilityText(
                expression: "7", yRegister: "5", status: "",
            ) == "X 7. Y 5.",
        )
        #expect(
            DisplayView.accessibilityText(
                expression: "", yRegister: "", status: "Too few operands",
            ) == "X 0. Y empty. Too few operands",
        )
        // Algebraic mode is unchanged.
        #expect(
            DisplayView.accessibilityText(
                expression: "2 +", yRegister: nil, status: "",
            ) == "2 +",
        )
        #expect(
            DisplayView.accessibilityText(
                expression: "2 +", yRegister: nil, status: "Oops",
            ) == "2 +. Oops",
        )
    }

    @Test func keypadLabelsForStackKeys() {
        #expect(KeypadKey.enter.label == "ENTER")
        #expect(KeypadKey.drop.label == "DROP")
        #expect(KeypadKey.swap.label == "x\u{2194}\u{FE0E}y")
        #expect(KeypadKey.enter.accessibilityLabel == "enter")
        #expect(KeypadKey.drop.accessibilityLabel == "drop")
        #expect(KeypadKey.swap.accessibilityLabel == "swap x and y")
        #expect(KeypadKey.enter.isAccent)
        #expect(!KeypadKey.enter.isOperator)
        #expect(KeypadKey.swap.isOperator)
        #expect(KeypadKey.drop.isOperator)
    }
}
