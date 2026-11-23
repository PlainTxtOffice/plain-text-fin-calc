import Foundation

/// CSV export for calculator history.
enum HistoryExport {
    /// Format history as CSV text with a timestamp, expression, result,
    /// rpn_input header.
    ///
    /// The last column holds the RPN keystrokes of an entry made in RPN mode
    /// and is empty for algebraic entries. Matches Python's `csv.writer`
    /// output: CRLF line endings, and fields containing commas, quotes, or
    /// line breaks are quoted.
    static func formatCSV(_ history: History) -> String {
        var rows = [["timestamp", "expression", "result", "rpn_input"]]
        for entry in history.entries {
            rows.append([
                entry.timestamp.formatted(.iso8601),
                entry.expression,
                entry.result,
                entry.rpnInput ?? "",
            ])
        }
        return rows.map { row in
            row.map(quoteField).joined(separator: ",") + "\r\n"
        }.joined()
    }

    private static func quoteField(_ field: String) -> String {
        guard field.contains(where: { ",\"\r\n".contains($0) }) else {
            return field
        }
        return "\"" + field.replacingOccurrences(of: "\"", with: "\"\"") + "\""
    }
}
