import Foundation
import Observation

/// Own the expression, history, and settings for the running app.
///
/// Views send key presses here and render the published state; parsing,
/// evaluation, and persistence stay out of the view layer.
@MainActor
@Observable
final class CalculatorSession {
    private(set) var history: History
    private(set) var settings: Settings
    /// The expression being entered, or the formatted result after `=`.
    /// In RPN mode, the X register: the number being typed, or the top of
    /// the stack at display precision; empty when the stack is empty.
    private(set) var displayText = ""
    /// The latest error or save failure; empty when there is none.
    private(set) var statusText = ""

    private var builder = ExpressionBuilder()
    private var rpn = RpnStack()
    @ObservationIgnored private let historyURL: URL
    @ObservationIgnored private let settingsURL: URL
    // One serial queue keeps history writes in order, off the main thread.
    @ObservationIgnored private let writeQueue = DispatchQueue(
        label: "com.plaintxtoffice.fincalc.history-write",
        qos: .utility,
    )

    init(
        history: History,
        settings: Settings,
        historyURL: URL,
        settingsURL: URL,
    ) {
        var history = history
        history.trim(to: settings.maxHistoryEntries)
        self.history = history
        self.settings = settings
        self.historyURL = historyURL
        self.settingsURL = settingsURL
    }

    /// Load saved history and settings from the app's data folder.
    static func load(
        historyURL: URL = PathHandler.historyFile,
        settingsURL: URL = PathHandler.settingsFile,
    ) -> CalculatorSession {
        CalculatorSession(
            history: HistoryStore.loadHistory(from: historyURL),
            settings: SettingsStore.loadSettings(from: settingsURL),
            historyURL: historyURL,
            settingsURL: settingsURL,
        )
    }

    /// Tokens of the expression being entered, saved for relaunch.
    var inputTokens: [String] { builder.tokens }
    /// True while the input ends in a reused result.
    var hasPendingResult: Bool { builder.resultPending }

    /// True when keys act on the RPN stack instead of an expression.
    var isRPN: Bool { settings.inputMode == .rpn }
    /// The Y register at display precision; empty when it holds no value.
    var rpnYText: String { rpn.visibleY.map(formatResult) ?? "" }
    /// RPN stack values, X first, saved for relaunch.
    var rpnLevels: [String] { rpn.levels }
    /// The number being typed in RPN mode; empty when there is none.
    var rpnEntry: String { rpn.entry ?? "" }
    /// False directly after ENTER, when the next number overwrites X.
    var rpnLiftEnabled: Bool { rpn.liftEnabled }
    /// RPN keystrokes accepted since the last tape entry.
    var rpnKeys: [String] { rpn.keys }

    /// The unfinished input of the active mode, as saved for relaunch.
    ///
    /// The other mode's values are empty: its input is always empty here.
    var savedInput: SavedInput {
        SavedInput(
            tokens: inputTokens.joined(separator: " "),
            resultPending: hasPendingResult,
            rpnLevels: rpnLevels.joined(separator: " "),
            rpnEntry: rpnEntry,
            rpnLiftEnabled: rpnLiftEnabled,
            rpnKeys: rpnKeys.joined(separator: " "),
        )
    }

    /// Restore saved input at launch and return the values to keep saved.
    ///
    /// Only the active mode's values are restored, and only while that
    /// mode has no input yet. The returned values describe the session
    /// afterwards, so saved input of the other mode, or input that failed
    /// validation, is dropped instead of being restored at a later launch.
    func restoreSavedInput(_ saved: SavedInput) -> SavedInput {
        if isRPN {
            if rpn.levels.isEmpty, rpn.entry == nil,
               !(saved.rpnLevels.isEmpty && saved.rpnEntry.isEmpty)
            {
                restoreRPN(
                    levels: saved.rpnLevels.split(separator: " ")
                        .map(String.init),
                    entry: saved.rpnEntry,
                    liftEnabled: saved.rpnLiftEnabled,
                    keys: saved.rpnKeys.split(separator: " ")
                        .map(String.init),
                )
            }
        } else if builder.tokens.isEmpty, !saved.tokens.isEmpty {
            restoreInput(
                tokens: saved.tokens.split(separator: " ").map(String.init),
                resultPending: saved.resultPending,
            )
        }
        return savedInput
    }

    /// Restore unfinished input saved before the app was terminated.
    ///
    /// Ignored in RPN mode, which restores its stack instead.
    func restoreInput(tokens: [String], resultPending: Bool) {
        guard !isRPN else { return }
        builder.restore(tokens, resultPending: resultPending)
        statusText = ""
        updateDisplay()
    }

    /// Restore an RPN stack saved before the app was terminated.
    ///
    /// Ignored in algebraic mode; invalid saved state gives an empty stack.
    func restoreRPN(
        levels: [String],
        entry: String,
        liftEnabled: Bool,
        keys: [String],
    ) {
        guard isRPN else { return }
        rpn = RpnStack.restored(
            levels: levels,
            entry: entry,
            liftEnabled: liftEnabled,
            keys: keys,
        )
        statusText = ""
        updateDisplay()
    }

    /// Add a digit, operator, parenthesis, or function token.
    ///
    /// In RPN mode an operator or `log` acts on the stack at once.
    func addSymbol(_ symbol: String) {
        if isRPN {
            pressRPN(symbol)
            return
        }
        statusText = ""
        if !builder.addSymbol(symbol) {
            statusText = "Invalid input: \(symbol)"
        }
        updateDisplay()
    }

    /// Evaluate the expression, record it, and show the formatted result.
    ///
    /// RPN mode has no `=`; there this acts as ENTER.
    func evaluate() {
        if isRPN {
            pressRPN("enter")
            return
        }
        let tokens = builder.tokens
        guard !tokens.isEmpty else { return }
        let result: Decimal
        do {
            result = try Evaluator.evaluate(tokens)
        } catch {
            statusText = error.localizedDescription
            return
        }

        let resultText = result.description
        history.append(HistoryEntry(
            expression: builder.toDisplay(),
            result: resultText,
            timestamp: .now,
        ))
        writeHistory()

        builder.clear()
        builder.insertResult(resultText)
        statusText = ""
        displayText = formatResult(resultText)
    }

    /// Clear the expression. In RPN mode, clear the number being typed, or
    /// the whole stack when none is being typed.
    func clear() {
        if isRPN {
            pressRPN("C")
            return
        }
        builder.clear()
        statusText = ""
        updateDisplay()
    }

    func backspace() {
        if isRPN {
            pressRPN("backspace")
            return
        }
        builder.backspace()
        updateDisplay()
    }

    func toggleSign() {
        if isRPN {
            pressRPN("sign")
            return
        }
        builder.toggleSign()
        updateDisplay()
    }

    /// RPN: finish the number being typed and duplicate it on the stack.
    func enter() {
        guard isRPN else { return }
        pressRPN("enter")
    }

    /// RPN: exchange the X and Y registers.
    func swap() {
        guard isRPN else { return }
        pressRPN("swap")
    }

    /// RPN: remove the X register.
    func drop() {
        guard isRPN else { return }
        pressRPN("drop")
    }

    /// Insert a past full-precision result into the expression, or put it
    /// on the stack in RPN mode.
    func insertResult(_ result: String) {
        if isRPN {
            statusText = ""
            do {
                try rpn.reuse(result)
            } catch {
                statusText = error.localizedDescription
            }
            updateDisplay()
            return
        }
        builder.insertResult(result)
        statusText = ""
        updateDisplay()
    }

    func clearHistory() {
        history.clearAll()
        writeHistory()
    }

    /// Apply and save new settings, trimming history to the new cap.
    ///
    /// Changing the input mode clears unfinished input and the RPN stack;
    /// history is kept.
    func applySettings(_ newSettings: Settings) {
        let modeChanged = newSettings.inputMode != settings.inputMode
        settings = newSettings
        if modeChanged {
            builder.clear()
            rpn = RpnStack()
            statusText = ""
        }
        history.trim(to: newSettings.maxHistoryEntries)
        writeHistory()
        do {
            try SettingsStore.writeSettings(newSettings, to: settingsURL)
        } catch {
            statusText = "Settings could not be saved"
        }
        updateDisplay()
    }

    /// Round a stored result to the configured display precision.
    func formatResult(_ result: String) -> String {
        Formatting.formatResult(result, decimalPlaces: settings.decimalPlaces)
    }

    /// Block until queued history writes finish, e.g. before suspension.
    func waitForPendingWrites() {
        writeQueue.sync {}
    }

    /// Send one key to the RPN stack and record a completed calculation.
    private func pressRPN(_ key: String) {
        statusText = ""
        do {
            if let record = try rpn.press(key) {
                history.append(HistoryEntry(
                    expression: record.expression,
                    result: record.result,
                    timestamp: .now,
                    rpnInput: record.rpnInput,
                ))
                writeHistory()
            }
        } catch {
            statusText = error.localizedDescription
        }
        updateDisplay()
    }

    private func updateDisplay() {
        if isRPN {
            displayText = rpn.entry ?? rpn.levels.first.map(formatResult) ?? ""
            return
        }
        // A lone result awaiting an operator shows at display precision.
        if builder.resultPending, builder.tokens.count == 1 {
            displayText = formatResult(builder.tokens[0])
        } else {
            displayText = builder.toDisplay()
        }
    }

    /// Snapshot entries and write them to disk off the main thread.
    private func writeHistory() {
        let snapshot = history
        let url = historyURL
        writeQueue.async { [weak self] in
            do {
                try HistoryStore.writeHistory(snapshot, to: url)
            } catch {
                Task { @MainActor in
                    self?.statusText = "History could not be saved"
                }
            }
        }
    }
}
