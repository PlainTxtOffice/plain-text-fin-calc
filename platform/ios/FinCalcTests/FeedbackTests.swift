import Foundation
import Testing

@testable import FinCalc

@Suite("Feedback email")
struct FeedbackTests {
    @Test func detailsNameAppSystemAndDevice() {
        #expect(
            Feedback.details(
                version: "0.2.0",
                systemName: "iOS",
                systemVersion: "26.4",
                device: "iPhone (iPhone17,3)",
            ) == "\n\n---\nPlain Text Fin Calc 0.2.0\niOS 26.4\niPhone (iPhone17,3)",
        )
    }

    @Test func emailDraftIsAddressedToSupport() throws {
        let url = try #require(
            Feedback.emailURL(details: "\n\n---\nFin Calc"),
        )
        #expect(url.scheme == "mailto")
        let components = try #require(
            URLComponents(url: url, resolvingAgainstBaseURL: false),
        )
        #expect(components.path == "feedback@plaintxtoffice.com")
        #expect(components.queryItems == [
            URLQueryItem(name: "subject", value: "Plain Text Fin Calc feedback (iOS)"),
            URLQueryItem(name: "body", value: "\n\n---\nFin Calc"),
        ])
    }
}
