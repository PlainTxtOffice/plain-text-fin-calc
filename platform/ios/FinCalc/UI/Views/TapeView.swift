import SwiftUI
import UIKit

/// Scrollable tape of past calculations; tapping one reuses its result.
struct TapeView: View {
    let entries: [HistoryEntry]
    let colors: ThemeColors
    let formatResult: (String) -> String
    let onSelect: (String) -> Void

    var body: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .trailing, spacing: 0) {
                    ForEach(Array(entries.enumerated()), id: \.offset) {
                        index, entry in
                        row(for: entry).id(index)
                        // Lines between rows only, not under the newest.
                        if index < entries.count - 1 {
                            Divider().overlay(
                                colors.placeholderText.opacity(0.2),
                            )
                        }
                    }
                }
                .padding(.vertical, 6)
            }
            .defaultScrollAnchor(.bottom)
            .onChange(of: entries.count) { _, count in
                guard count > 0 else { return }
                withAnimation(.easeOut(duration: 0.3)) {
                    proxy.scrollTo(count - 1, anchor: .bottom)
                }
            }
        }
        .overlay {
            if entries.isEmpty {
                Text("Calculations appear here")
                    .font(.callout)
                    .foregroundStyle(colors.placeholderText)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(colors.tapeBackground, in: .rect(cornerRadius: 12))
    }

    /// Right-aligned like an adding-machine tape, so the digits of results
    /// line up down the column.
    private func row(for entry: HistoryEntry) -> some View {
        let expression = KeyLabels.format(entry.expression)
        let result = KeyLabels.format(formatResult(entry.result))
        return Button {
            onSelect(entry.result)
        } label: {
            VStack(alignment: .trailing, spacing: 2) {
                Text(expression)
                    .font(.system(size: 14, design: .rounded))
                    .foregroundStyle(colors.placeholderText)
                Text("= \(result)")
                    .font(.system(size: 20, design: .rounded))
                    .foregroundStyle(colors.tapeText)
            }
            .monospacedDigit()
            .multilineTextAlignment(.trailing)
            .frame(maxWidth: .infinity, alignment: .trailing)
            .padding(.horizontal, 14)
            .padding(.vertical, 8)
            .contentShape(.rect)
        }
        .buttonStyle(.plain)
        .accessibilityElement(children: .ignore)
        .accessibilityAddTraits(.isButton)
        .accessibilityLabel("\(entry.expression) equals \(entry.result)")
        .accessibilityHint("Inserts this result into the expression")
        .contextMenu {
            Button("Use Result", systemImage: "arrow.down.to.line") {
                onSelect(entry.result)
            }
            Button("Copy Result", systemImage: "doc.on.doc") {
                UIPasteboard.general.string = entry.result
            }
        }
    }
}
