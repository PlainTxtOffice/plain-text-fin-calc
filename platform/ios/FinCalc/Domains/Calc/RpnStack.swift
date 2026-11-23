import Foundation

/// A finished RPN calculation, ready to append to the tape.
struct RpnTapeRecord: Equatable, Sendable {
    /// The equivalent algebraic expression, e.g. "3 + 4".
    let expression: String
    /// The full-precision result as the evaluator prints it.
    let result: String
    /// The accepted keystrokes since the previous record, e.g. "3 ENTER 4 +".
    let rpnInput: String
}

/// Reverse Polish notation stack machine with four levels (X, Y, Z, T).
///
/// It follows the HP model: stack lift, lift disabled directly after ENTER,
/// and T replicated when a full stack drops. Unlike the hardware, levels can
/// be empty, so an operator with too few operands is an error and no operand
/// the user never entered reaches the tape. Cancelling a typed number removes
/// it, and DROP enables stack lift.
///
/// All arithmetic goes through `Evaluator`, so a result is the exact string
/// algebraic mode stores for the same calculation. Every key is
/// all-or-nothing: when a key throws, the stack is unchanged.
struct RpnStack: Equatable, Sendable {
    static let maxLevels = 4
    /// Most digits one typed number may hold, the evaluator's precision.
    static let maxEntryDigits = DecimalMath.precision
    /// Most keystroke tokens kept between two tape records.
    static let maxLoggedKeys = 64
    /// First keystroke token once older ones were dropped.
    static let truncationMark = "..."

    private static let digitKeys: Set<String> = [
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    ]
    private static let operatorKeys: Set<String> = ["+", "-", "*", "/", "^"]
    private static let namedLogTokens: Set<String> = [
        "ENTER", "SWAP", "DROP", "CHS", "LOG", truncationMark,
    ]

    /// Stack values, X first; each is a canonical number string.
    private(set) var levels: [String] = []
    /// The number being typed, shown as X while present.
    private(set) var entry: String?
    /// False only directly after ENTER: the next number overwrites X.
    private(set) var liftEnabled = true
    /// Accepted keystrokes since the last tape record.
    private(set) var keys: [String] = []

    /// True when nothing is on the stack and no number is being typed.
    var isEmpty: Bool { levels.isEmpty && entry == nil }

    /// The value shown as X: the typed number, else the first level.
    var visibleX: String? { entry ?? levels.first }

    /// The value shown as Y: the first level while typing, else the second.
    var visibleY: String? {
        if entry != nil { return levels.first }
        return levels.count > 1 ? levels[1] : nil
    }

    /// Apply one keypad key.
    ///
    /// Keys: "0"..."9", ".", "backspace", "sign", "enter", "swap", "drop",
    /// "C", "log", "+", "-", "*", "/", "^". "=" acts as "enter".
    ///
    /// - Returns: The tape record of a completed calculation, or nil.
    /// - Throws: `EvaluationError`; the stack is then unchanged.
    @discardableResult
    mutating func press(_ key: String) throws -> RpnTapeRecord? {
        var next = self
        let record = try next.apply(key)
        self = next
        return record
    }

    /// Put a tape result on the stack.
    ///
    /// A number being typed is discarded; directly after ENTER the value
    /// overwrites X; otherwise it lifts the stack.
    ///
    /// - Throws: `EvaluationError` if `value` is not a number; the stack is
    ///   then unchanged.
    mutating func reuse(_ value: String) throws {
        let number = try Self.canon(value)
        entry = nil
        if liftEnabled {
            push(number)
        } else {
            levels[0] = number
        }
        liftEnabled = true
        logKey(number)
    }

    /// Rebuild a stack from saved state, or return an empty stack if any
    /// part of the saved state is invalid.
    static func restored(
        levels: [String],
        entry: String,
        liftEnabled: Bool,
        keys: [String],
    ) -> RpnStack {
        guard levels.count <= maxLevels, keys.count <= maxLoggedKeys else {
            return RpnStack()
        }
        var stack = RpnStack()
        for level in levels {
            guard let number = try? canon(level) else { return RpnStack() }
            stack.levels.append(number)
        }
        if !entry.isEmpty {
            guard let digits = entryDigitCount(entry),
                  (1...maxEntryDigits).contains(digits),
                  liftEnabled
            else {
                return RpnStack()
            }
            stack.entry = entry
        }
        if !liftEnabled {
            guard stack.levels.count >= 2, stack.levels[0] == stack.levels[1]
            else {
                return RpnStack()
            }
        }
        for key in keys {
            let isKnown = namedLogTokens.contains(key)
                || operatorKeys.contains(key)
                || (try? canon(key)) != nil
            guard isKnown else { return RpnStack() }
        }
        stack.liftEnabled = liftEnabled
        stack.keys = keys
        return stack
    }

    /// The string algebraic mode stores for these tokens.
    static func resultString(_ tokens: [String]) throws -> String {
        try Evaluator.evaluate(tokens).description
    }

    /// True for a zero written with any sign or decimal point: "0", "-0",
    /// "0.", "-0.00".
    static func isZeroText(_ text: String) -> Bool {
        var body = Substring(text)
        if body.hasPrefix("-") { body = body.dropFirst() }
        var zeros = 0
        var points = 0
        for character in body {
            if character == "0" {
                zeros += 1
            } else if character == "." {
                points += 1
            } else {
                return false
            }
        }
        return zeros > 0 && points <= 1
    }

    /// The canonical form of a number: "1.50" is "1.5", "-0" is "0".
    ///
    /// Zero is decided by its text so no negative zero reaches the engine.
    static func canon(_ text: String) throws -> String {
        if isZeroText(text) { return "0" }
        return try resultString([text])
    }

    // MARK: - Keys

    private mutating func apply(_ key: String) throws -> RpnTapeRecord? {
        if Self.digitKeys.contains(key) {
            try addDigit(key)
            return nil
        }
        if Self.operatorKeys.contains(key) {
            return try applyOperator(key)
        }
        switch key {
        case ".": try addDecimalPoint()
        case "backspace": backspace()
        case "sign": try changeSign()
        case "enter", "=": try enter()
        case "log": return try applyLog()
        case "swap": try swapXY()
        case "drop": try dropX()
        case "C": clear()
        default: throw EvaluationError("Invalid input: \(key)")
        }
        return nil
    }

    private mutating func addDigit(_ digit: String) throws {
        guard let typed = entry else {
            startEntry()
            entry = digit
            return
        }
        guard (Self.entryDigitCount(typed) ?? 0) < Self.maxEntryDigits else {
            throw EvaluationError("Invalid input: \(digit)")
        }
        entry = typed + digit
    }

    private mutating func addDecimalPoint() throws {
        guard let typed = entry else {
            startEntry()
            entry = "0."
            return
        }
        guard !typed.contains(".") else {
            throw EvaluationError("Invalid input: .")
        }
        entry = typed + "."
    }

    private mutating func backspace() {
        guard let typed = entry else { return }
        let shorter = String(typed.dropLast())
        entry = (Self.entryDigitCount(shorter) ?? 0) > 0 ? shorter : nil
    }

    /// Toggle the sign of the typed number, or negate X when none is typed.
    private mutating func changeSign() throws {
        if let typed = entry {
            entry = typed.hasPrefix("-")
                ? String(typed.dropFirst()) : "-" + typed
            return
        }
        guard let x = levels.first else { return }
        if x != "0" {
            let negated = try Self.resultString(["-", x])
            levels[0] = Self.isZeroText(negated) ? "0" : negated
        }
        liftEnabled = true
        logKey("CHS")
    }

    private mutating func enter() throws {
        try terminate()
        guard let x = levels.first else { throw Self.tooFewOperands }
        push(x)
        liftEnabled = false
        logKey("ENTER")
    }

    private mutating func applyOperator(_ op: String) throws -> RpnTapeRecord {
        try terminate()
        guard levels.count >= 2 else { throw Self.tooFewOperands }
        let y = levels[1]
        let x = levels[0]
        let result = try Self.resultString([y, op, x])
        let wasFull = levels.count == Self.maxLevels
        let top = levels[levels.count - 1]
        levels.removeFirst(2)
        levels.insert(result, at: 0)
        // A full stack drops with T replicated.
        if wasFull { levels.append(top) }
        liftEnabled = true
        logKey(op)
        return takeRecord(expression: "\(y) \(op) \(x)", result: result)
    }

    private mutating func applyLog() throws -> RpnTapeRecord {
        try terminate()
        guard let x = levels.first else { throw Self.tooFewOperands }
        let result = try Self.resultString(["log", "(", x, ")"])
        levels[0] = result
        liftEnabled = true
        logKey("LOG")
        return takeRecord(expression: "log ( \(x) )", result: result)
    }

    private mutating func swapXY() throws {
        try terminate()
        guard levels.count >= 2 else { throw Self.tooFewOperands }
        levels.swapAt(0, 1)
        liftEnabled = true
        logKey("SWAP")
    }

    private mutating func dropX() throws {
        try terminate()
        guard !levels.isEmpty else { throw Self.tooFewOperands }
        if levels.count == Self.maxLevels {
            levels = [levels[1], levels[2], levels[3], levels[3]]
        } else {
            levels.removeFirst()
        }
        liftEnabled = true
        logKey("DROP")
    }

    /// Clear the typed number if there is one, otherwise the whole stack.
    private mutating func clear() {
        if entry != nil {
            entry = nil
        } else {
            self = RpnStack()
        }
    }

    // MARK: - Helpers

    private static let tooFewOperands = EvaluationError("Too few operands")

    /// Insert a value as X; the old T is lost when the stack is full.
    private mutating func push(_ value: String) {
        levels.insert(value, at: 0)
        if levels.count > Self.maxLevels {
            levels.removeLast()
        }
    }

    /// Finish the typed number and put it on the stack.
    private mutating func terminate() throws {
        guard let typed = entry else { return }
        let number = try Self.canon(typed)
        push(number)
        logKey(number)
        entry = nil
    }

    /// Begin a new number; directly after ENTER it overwrites the duplicate.
    private mutating func startEntry() {
        if !liftEnabled {
            levels.removeFirst()
        }
        liftEnabled = true
    }

    /// Record an accepted keystroke, keeping the newest tokens.
    private mutating func logKey(_ token: String) {
        keys.append(token)
        guard keys.count > Self.maxLoggedKeys else { return }
        if keys[0] != Self.truncationMark {
            keys[0] = Self.truncationMark
        }
        keys.remove(at: 1)
    }

    /// Build the tape record from the keystroke log and start a new log.
    private mutating func takeRecord(
        expression: String,
        result: String,
    ) -> RpnTapeRecord {
        let record = RpnTapeRecord(
            expression: expression,
            result: result,
            rpnInput: keys.joined(separator: " "),
        )
        keys = []
        return record
    }

    /// The number of digits in text made of an optional leading "-", digits,
    /// and at most one "."; nil for any other text.
    private static func entryDigitCount(_ text: String) -> Int? {
        var body = Substring(text)
        if body.hasPrefix("-") { body = body.dropFirst() }
        var digits = 0
        var points = 0
        for character in body {
            if character == "." {
                points += 1
            } else if character.isASCII, character.isNumber {
                digits += 1
            } else {
                return nil
            }
        }
        return points <= 1 ? digits : nil
    }
}
