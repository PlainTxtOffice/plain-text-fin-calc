import CoreTransferable
import SwiftUI
import UniformTypeIdentifiers

/// Main calculator screen assembling tape, display, and keypad.
struct RootView: View {
    let session: CalculatorSession

    @State private var isShowingSettings = false
    @State private var isConfirmingClear = false
    @State private var isChoosingFeedback = false
    @State private var isShowingNoMail = false
    // Unfinished input survives the system ending the app in the background.
    @SceneStorage("input.tokens") private var savedTokens = ""
    @SceneStorage("input.resultPending") private var savedResultPending = false
    @Environment(\.openURL) private var openURL
    @FocusState private var hasKeyboardFocus: Bool

    var body: some View {
        let colors = ThemeColors.colors(for: session.settings.theme)
        NavigationStack {
            GeometryReader { proxy in
                let tape = TapeView(
                    entries: session.history.entries,
                    colors: colors,
                    formatResult: session.formatResult,
                    onSelect: session.insertResult,
                )
                let display = DisplayView(
                    expression: session.displayText,
                    status: session.statusText,
                    colors: colors,
                )
                if proxy.size.width > proxy.size.height {
                    // Landscape: tape on the left, display and keypad right.
                    HStack(spacing: 10) {
                        tape.frame(width: (proxy.size.width - 10) / 2.3)
                        VStack(spacing: 10) {
                            display
                            KeypadView(colors: colors, onKey: press)
                        }
                    }
                } else {
                    VStack(spacing: 10) {
                        tape
                        display
                        KeypadView(colors: colors, onKey: press)
                            .frame(height: proxy.size.height * 0.5)
                    }
                }
            }
            .padding(.horizontal, 12)
            .padding(.bottom, 8)
            .background(colors.window)
            .navigationTitle("Plain Text Fin Calc")
            .navigationBarTitleDisplayMode(.inline)
            .toolbarBackground(colors.window, for: .navigationBar)
            .toolbar { toolbarContent }
        }
        .preferredColorScheme(colors.colorScheme)
        .tint(colors.highlight)
        .sensoryFeedback(.error, trigger: session.statusText) { _, status in
            !status.isEmpty
        }
        .confirmationDialog(
            "Clear All History?",
            isPresented: $isConfirmingClear,
            titleVisibility: .visible,
        ) {
            Button("Clear History", role: .destructive) {
                session.clearHistory()
            }
        } message: {
            Text("This removes every saved calculation from the tape.")
        }
        .confirmationDialog(
            "Send Feedback",
            isPresented: $isChoosingFeedback,
            titleVisibility: .visible,
        ) {
            Button("Email") { emailFeedback() }
            Button("Contact Form") { openURL(Links.contact) }
        } message: {
            Text(
                "Send a bug report or feature request by email or with "
                    + "the contact form on our website.",
            )
        }
        .alert("Send Feedback", isPresented: $isShowingNoMail) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(
                "No email app is available. Send bug reports and feature "
                    + "requests to\n\(Links.feedbackEmail)",
            )
        }
        .sheet(isPresented: $isShowingSettings) {
            SettingsView(settings: session.settings) { settings in
                session.applySettings(settings)
            }
        }
        // Hardware keyboards (iPad, simulator) type straight into the keypad.
        .focusable()
        .focused($hasKeyboardFocus)
        .focusEffectDisabled()
        .onKeyPress(phases: .down, action: pressHardwareKey)
        .onAppear {
            hasKeyboardFocus = true
            restoreSavedInput()
        }
        .onChange(of: session.inputTokens) { _, tokens in
            savedTokens = tokens.joined(separator: " ")
        }
        .onChange(of: session.hasPendingResult) { _, pending in
            savedResultPending = pending
        }
    }

    @ToolbarContentBuilder
    private var toolbarContent: some ToolbarContent {
        ToolbarItem(placement: .topBarLeading) {
            Menu("History", systemImage: "clock.arrow.circlepath") {
                ShareLink(
                    item: HistoryCSV(
                        text: HistoryExport.formatCSV(session.history),
                    ),
                    preview: SharePreview("Plain Text Fin Calc history"),
                ) {
                    Label("Export CSV", systemImage: "square.and.arrow.up")
                }
                .disabled(session.history.entries.isEmpty)
                Button(
                    "Clear History",
                    systemImage: "trash",
                    role: .destructive,
                ) {
                    isConfirmingClear = true
                }
                .disabled(session.history.entries.isEmpty)
            }
        }
        ToolbarItem(placement: .topBarTrailing) {
            Menu("More", systemImage: "ellipsis.circle") {
                Button("Settings", systemImage: "gearshape") {
                    isShowingSettings = true
                }
                Button("Send Feedback", systemImage: "envelope") {
                    isChoosingFeedback = true
                }
                Button("Privacy Policy", systemImage: "hand.raised") {
                    openURL(Links.privacyPolicy)
                }
            }
        }
    }

    /// Open an email draft, or show the address when no mail app can.
    private func emailFeedback() {
        guard let url = Feedback.emailURLForThisDevice() else {
            isShowingNoMail = true
            return
        }
        openURL(url) { accepted in
            if !accepted { isShowingNoMail = true }
        }
    }

    private func restoreSavedInput() {
        guard session.inputTokens.isEmpty, !savedTokens.isEmpty else { return }
        session.restoreInput(
            tokens: savedTokens.split(separator: " ").map(String.init),
            resultPending: savedResultPending,
        )
    }

    private func press(_ key: KeypadKey) {
        switch key {
        case .symbol(let symbol): session.addSymbol(symbol)
        case .evaluate: session.evaluate()
        case .clear: session.clear()
        case .backspace: session.backspace()
        case .toggleSign: session.toggleSign()
        }
    }

    private func pressHardwareKey(_ keyPress: KeyPress) -> KeyPress.Result {
        switch keyPress.key {
        case .return:
            session.evaluate()
        case .escape:
            session.clear()
        case .delete:
            session.backspace()
        default:
            let character = keyPress.characters
            if character.lowercased() == "l" {
                session.addSymbol("log")
            } else if "0123456789.+-*/^()".contains(character),
                      character.count == 1
            {
                session.addSymbol(character)
            } else {
                return .ignored
            }
        }
        return .handled
    }
}

/// History exported as a shareable CSV file.
private struct HistoryCSV: Transferable {
    let text: String

    static var transferRepresentation: some TransferRepresentation {
        DataRepresentation(exportedContentType: .commaSeparatedText) {
            Data($0.text.utf8)
        }
        .suggestedFileName("history.csv")
    }
}
