import SwiftUI

/// One calculator key and the action it requests.
enum KeypadKey: Hashable {
    case symbol(String)
    case evaluate
    case clear
    case backspace
    case toggleSign
    /// RPN: finish the number being typed and duplicate it.
    case enter
    /// RPN: exchange the X and Y registers.
    case swap
    /// RPN: remove the X register.
    case drop

    var label: String {
        switch self {
        case .symbol(let symbol): KeyLabels.format(symbol)
        case .evaluate: "="
        case .clear: "C"
        case .backspace: "\u{232B}"
        case .toggleSign: "\u{00B1}"
        case .enter: "ENTER"
        // The variation selector keeps the arrow a text glyph.
        case .swap: "x\u{2194}\u{FE0E}y"
        case .drop: "DROP"
        }
    }

    var accessibilityLabel: String {
        switch self {
        case .symbol("*"): "multiply"
        case .symbol("/"): "divide"
        case .symbol("+"): "plus"
        case .symbol("-"): "minus"
        case .symbol("^"): "power"
        case .symbol("("): "open parenthesis"
        case .symbol(")"): "close parenthesis"
        case .symbol("."): "decimal point"
        case .symbol("log"): "log base 10"
        case .symbol(let symbol): symbol
        case .evaluate: "equals"
        case .clear: "clear"
        case .backspace: "delete"
        case .toggleSign: "change sign"
        case .enter: "enter"
        case .swap: "swap x and y"
        case .drop: "drop"
        }
    }

    var isOperator: Bool {
        switch self {
        case .symbol(let symbol):
            !symbol.allSatisfy(\.isNumber) && symbol != "."
        case .evaluate, .enter: false
        case .clear, .backspace, .toggleSign, .swap, .drop: true
        }
    }

    /// True for the tall accent key: `=`, or ENTER in RPN mode.
    var isAccent: Bool {
        self == .evaluate || self == .enter
    }
}

/// Display forms for operator tokens; tokens, saved history, and CSV
/// export stay ASCII.
enum KeyLabels {
    static func format(_ text: String) -> String {
        text.replacingOccurrences(of: "*", with: "\u{00D7}")
            .replacingOccurrences(of: "/", with: "\u{00F7}")
            .replacingOccurrences(of: "-", with: "\u{2212}")
    }
}

/// Grid of calculator keys.
///
/// Four columns of rows sit beside a fifth column whose tall `=` key
/// spans the bottom three rows, like an adding-machine keyboard. In RPN
/// mode the parenthesis keys become swap and DROP and the tall key ENTER.
struct KeypadView: View {
    var inputMode: InputMode = .algebraic
    let colors: ThemeColors
    let onKey: (KeypadKey) -> Void

    @State private var tapCount = 0

    private static let algebraicTopRow: [KeypadKey] = [
        .symbol("log"), .symbol("("), .symbol(")"), .clear,
    ]
    private static let rpnTopRow: [KeypadKey] = [
        .symbol("log"), .swap, .drop, .clear,
    ]
    private static let lowerRows: [[KeypadKey]] = [
        [.symbol("7"), .symbol("8"), .symbol("9"), .symbol("/")],
        [.symbol("4"), .symbol("5"), .symbol("6"), .symbol("*")],
        [.symbol("1"), .symbol("2"), .symbol("3"), .symbol("-")],
        [.symbol("0"), .symbol("."), .toggleSign, .symbol("+")],
    ]
    private static let spacing: CGFloat = 8

    private var keyRows: [[KeypadKey]] {
        let topRow = inputMode == .rpn
            ? Self.rpnTopRow : Self.algebraicTopRow
        return [topRow] + Self.lowerRows
    }

    private var tallKey: KeypadKey {
        inputMode == .rpn ? .enter : .evaluate
    }

    var body: some View {
        let rows = keyRows
        GeometryReader { proxy in
            let rowCount = CGFloat(rows.count)
            let rowHeight =
                (proxy.size.height - Self.spacing * (rowCount - 1)) / rowCount
            let columnWidth = (proxy.size.width - Self.spacing * 4) / 5
            HStack(spacing: Self.spacing) {
                VStack(spacing: Self.spacing) {
                    ForEach(rows, id: \.self) { row in
                        HStack(spacing: Self.spacing) {
                            ForEach(row, id: \.self) { key in
                                keyButton(key, height: rowHeight)
                            }
                        }
                    }
                }
                VStack(spacing: Self.spacing) {
                    keyButton(.backspace, height: rowHeight)
                    keyButton(.symbol("^"), height: rowHeight)
                    keyButton(
                        tallKey,
                        height: rowHeight * 3 + Self.spacing * 2,
                    )
                }
                .frame(width: max(columnWidth, 0))
            }
        }
        .sensoryFeedback(.selection, trigger: tapCount)
    }

    private func keyButton(_ key: KeypadKey, height: CGFloat) -> some View {
        Button {
            tapCount += 1
            onKey(key)
        } label: {
            Text(key.label)
                .font(.system(size: 24, weight: .medium, design: .rounded))
                .lineLimit(1)
                .minimumScaleFactor(0.6)
                // Keeps word labels such as ENTER and DROP off the key edges.
                .padding(.horizontal, 6)
                .frame(maxWidth: .infinity)
                .frame(height: max(height, 0))
                .contentShape(.rect)
        }
        .buttonStyle(KeyButtonStyle(
            background: background(for: key),
            foreground: key.isAccent
                ? colors.highlightedText : colors.keyText,
        ))
        .accessibilityLabel(key.accessibilityLabel)
    }

    private func background(for key: KeypadKey) -> Color {
        if key.isAccent { return colors.highlight }
        return key.isOperator ? colors.operatorKey : colors.key
    }
}

private struct KeyButtonStyle: ButtonStyle {
    let background: Color
    let foreground: Color

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .foregroundStyle(foreground)
            .background(background, in: .rect(cornerRadius: 10))
            .opacity(configuration.isPressed ? 0.6 : 1)
    }
}
