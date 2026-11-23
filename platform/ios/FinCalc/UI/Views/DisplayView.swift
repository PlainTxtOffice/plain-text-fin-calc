import SwiftUI

/// Shows the current expression and a status or error line.
///
/// In RPN mode the expression line is the X register and a smaller Y
/// register line sits above it.
struct DisplayView: View {
    let expression: String
    /// The Y register value in RPN mode, empty when it holds none; nil in
    /// algebraic mode, where the line is not shown.
    var yRegister: String? = nil
    let status: String
    let colors: ThemeColors

    var body: some View {
        VStack(alignment: .trailing, spacing: 4) {
            if let yRegister {
                Text(Self.yLine(yRegister))
                    .font(.system(size: 16, design: .rounded))
                    .monospacedDigit()
                    .foregroundStyle(colors.placeholderText)
                    .lineLimit(1)
                    .minimumScaleFactor(0.4)
                    .truncationMode(.head)
            }
            Text(expression.isEmpty ? "0" : KeyLabels.format(expression))
                .font(.system(size: 40, weight: .light, design: .rounded))
                .monospacedDigit()
                .foregroundStyle(
                    expression.isEmpty ? colors.placeholderText
                        : colors.displayText,
                )
                .lineLimit(1)
                .minimumScaleFactor(0.4)
                .truncationMode(.head)
                .textSelection(.enabled)
            Text(status)
                .font(.footnote)
                .foregroundStyle(colors.errorText)
                .lineLimit(2)
                .frame(minHeight: 18)
        }
        .frame(maxWidth: .infinity, alignment: .trailing)
        .padding(.horizontal, 14)
        .padding(.vertical, 8)
        .background(colors.displayBackground, in: .rect(cornerRadius: 12))
        .accessibilityElement(children: .combine)
        .accessibilityLabel(
            Self.accessibilityText(
                expression: expression,
                yRegister: yRegister,
                status: status,
            ),
        )
    }

    /// The Y register line: "Y: 3", or "Y:" when the register is empty.
    static func yLine(_ value: String) -> String {
        value.isEmpty ? "Y:" : "Y: \(KeyLabels.format(value))"
    }

    /// The spoken summary of the display. RPN mode names both registers.
    static func accessibilityText(
        expression: String,
        yRegister: String?,
        status: String,
    ) -> String {
        guard let yRegister else {
            return status.isEmpty ? expression : "\(expression). \(status)"
        }
        let x = expression.isEmpty ? "0" : expression
        let y = yRegister.isEmpty ? "empty" : yRegister
        let registers = "X \(x). Y \(y)."
        return status.isEmpty ? registers : "\(registers) \(status)"
    }
}
