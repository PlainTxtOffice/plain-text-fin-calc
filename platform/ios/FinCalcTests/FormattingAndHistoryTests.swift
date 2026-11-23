import Foundation
import Testing

@testable import FinCalc

@Suite("Result formatting")
struct FormattingTests {
    @Test(arguments: [
        ("3.14159", nil, "3.14159"),
        ("3.14159", 2, "3.14"),
        ("2.5", 0, "2"),
        ("3.5", 0, "4"),
        ("2.345", 2, "2.34"),
        ("2", 2, "2.00"),
        ("7.9", 0, "8"),
        ("-1.5", 3, "-1.500"),
        ("oops", 2, "oops"),
        ("1E+100", 2, "1E+100"),
    ] as [(String, Int?, String)])
    func formatResult(value: String, places: Int?, expected: String) {
        #expect(
            Formatting.formatResult(value, decimalPlaces: places) == expected,
        )
    }
}

@Suite("History")
struct HistoryTests {
    private func entry(_ number: Int) -> HistoryEntry {
        HistoryEntry(
            expression: "\(number) + 0",
            result: "\(number)",
            timestamp: Date(timeIntervalSince1970: Double(number)),
        )
    }

    @Test func appendKeepsOrder() {
        var history = History()
        history.append(entry(1))
        history.append(entry(2))
        #expect(history.entries.map(\.result) == ["1", "2"])
    }

    @Test func appendDropsOldestOverCap() {
        var history = History(maxEntries: 2)
        (1...3).forEach { history.append(entry($0)) }
        #expect(history.entries.map(\.result) == ["2", "3"])
    }

    @Test func trimSetsNewCap() {
        var history = History(entries: (1...5).map(entry))
        history.trim(to: 3)
        #expect(history.entries.map(\.result) == ["3", "4", "5"])
        #expect(history.maxEntries == 3)
    }

    @Test func trimToNilKeepsEverything() {
        var history = History(entries: (1...5).map(entry), maxEntries: 5)
        history.trim(to: nil)
        history.append(entry(6))
        #expect(history.entries.count == 6)
    }

    @Test func clearAllEmpties() {
        var history = History(entries: (1...3).map(entry))
        history.clearAll()
        #expect(history.entries.isEmpty)
    }

    @Test func csvExportQuotesAndUsesCRLF() {
        let history = History(entries: [
            HistoryEntry(
                expression: "1 + 1",
                result: "2",
                timestamp: Date(timeIntervalSince1970: 0),
            ),
            HistoryEntry(
                expression: "say \"hi\", ok",
                result: "3",
                timestamp: Date(timeIntervalSince1970: 0),
            ),
        ])
        #expect(HistoryExport.formatCSV(history) == """
            timestamp,expression,result,rpn_input\r
            1970-01-01T00:00:00Z,1 + 1,2,\r
            1970-01-01T00:00:00Z,"say ""hi"", ok",3,\r

            """)
    }

    @Test func csvExportHasRPNInputColumn() throws {
        let style = Date.ISO8601FormatStyle()
        let history = History(entries: [
            HistoryEntry(
                expression: "1 / 3",
                result: "0.3333333333333333333333333333",
                timestamp: try style.parse("2026-11-23T12:00:00Z"),
            ),
            HistoryEntry(
                expression: "3 + 4",
                result: "7",
                timestamp: try style.parse("2026-11-23T12:00:05Z"),
                rpnInput: "3 ENTER 4 +",
            ),
        ])
        // The algebraic row ends with an empty last field.
        #expect(
            HistoryExport.formatCSV(history)
                == "timestamp,expression,result,rpn_input\r\n"
                + "2026-11-23T12:00:00Z,1 / 3,"
                + "0.3333333333333333333333333333,\r\n"
                + "2026-11-23T12:00:05Z,3 + 4,7,3 ENTER 4 +\r\n",
        )
    }

    @Test func csvExportQuotesRPNInput() {
        let history = History(entries: [
            HistoryEntry(
                expression: "1 + 1",
                result: "2",
                timestamp: Date(timeIntervalSince1970: 0),
                rpnInput: "1, \"ENTER\" +",
            ),
        ])
        #expect(
            HistoryExport.formatCSV(history)
                == "timestamp,expression,result,rpn_input\r\n"
                + "1970-01-01T00:00:00Z,1 + 1,2,\"1, \"\"ENTER\"\" +\"\r\n",
        )
    }
}
