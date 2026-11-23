import Foundation
import os

/// JSON file persistence for calculator history.
///
/// Uses the same layout as the Windows app: a list of objects with
/// `expression`, `result`, and ISO 8601 `timestamp` fields. Entries made in
/// RPN mode also carry an `rpn_input` string with their keystrokes.
enum HistoryStore {
    private static let logger = Logger(
        subsystem: "com.plaintxtoffice.fincalc",
        category: "HistoryStore",
    )

    /// Load history entries from a JSON file.
    ///
    /// - Returns: Loaded history, or an empty History if the file is
    ///   missing or corrupt.
    static func loadHistory(from url: URL) -> History {
        guard FileManager.default.fileExists(atPath: url.path) else {
            return History()
        }
        do {
            let raw = try Data(contentsOf: url)
            if String(decoding: raw, as: UTF8.self)
                .trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            {
                return History()
            }
            let records = try JSONDecoder().decode(
                [HistoryRecord].self,
                from: raw,
            )
            return History(entries: try records.map { try $0.toEntry() })
        } catch {
            logger.error(
                "Failed to load history from \(url.path): \(error)",
            )
            return History()
        }
    }

    /// Write all history entries to a JSON file.
    ///
    /// - Throws: Write failures, after logging them, so callers can report
    ///   unsaved results.
    static func writeHistory(_ history: History, to url: URL) throws {
        do {
            try FileManager.default.createDirectory(
                at: url.deletingLastPathComponent(),
                withIntermediateDirectories: true,
            )
            let encoder = JSONEncoder()
            encoder.outputFormatting = [
                .prettyPrinted, .sortedKeys, .withoutEscapingSlashes,
            ]
            let records = history.entries.map(HistoryRecord.init)
            try encoder.encode(records).write(to: url, options: .atomic)
        } catch {
            logger.error("Failed to write history to \(url.path): \(error)")
            throw error
        }
    }
}

/// The JSON shape of one history entry.
private struct HistoryRecord: Codable {
    let expression: String
    let result: String
    let timestamp: String
    /// Written only for RPN entries, so algebraic entries keep their shape.
    let rpnInput: String?

    private enum CodingKeys: String, CodingKey {
        case expression
        case result
        case timestamp
        case rpnInput = "rpn_input"
    }

    init(_ entry: HistoryEntry) {
        expression = entry.expression
        result = entry.result
        timestamp = Date.ISO8601FormatStyle(includingFractionalSeconds: true)
            .format(entry.timestamp)
        rpnInput = Self.nonEmpty(entry.rpnInput)
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        expression = try container.decode(String.self, forKey: .expression)
        result = try container.decode(String.self, forKey: .result)
        timestamp = try container.decode(String.self, forKey: .timestamp)
        // A missing, null, empty, or mistyped value means an algebraic
        // entry; it never makes the file unreadable.
        rpnInput = Self.nonEmpty(
            try? container.decode(String.self, forKey: .rpnInput),
        )
    }

    func toEntry() throws -> HistoryEntry {
        HistoryEntry(
            expression: expression,
            result: result,
            timestamp: try Self.parseTimestamp(timestamp),
            rpnInput: rpnInput,
        )
    }

    private static func nonEmpty(_ text: String?) -> String? {
        guard let text, !text.isEmpty else { return nil }
        return text
    }

    /// Accept timestamps with or without fractional seconds.
    private static func parseTimestamp(_ text: String) throws -> Date {
        let withFraction = Date.ISO8601FormatStyle(
            includingFractionalSeconds: true,
        )
        if let date = try? withFraction.parse(text) {
            return date
        }
        return try Date.ISO8601FormatStyle().parse(text)
    }
}
