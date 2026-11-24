import Foundation
import UIKit

/// Web and email destinations shared with the Android app.
enum Links {
    static let privacyPolicy = URL(
        string: "https://plaintxtoffice.com/privacy-policy/",
    )!
    static let contact = URL(string: "https://plaintxtoffice.com/contact/")!
    /// Bug reports and feature requests.
    static let feedbackEmail = "feedback@plaintxtoffice.com"
}

/// Builds the feedback email draft; the sender can see and delete all of it.
enum Feedback {
    /// Lines under the writer's message that tell support which app
    /// version, system version, and device a report is about.
    static func details(
        version: String,
        systemName: String,
        systemVersion: String,
        device: String,
    ) -> String {
        "\n\n---\nPlain Text Fin Calc \(version)\n\(systemName) \(systemVersion)\n\(device)"
    }

    /// Subject shared with the other Plain Text Office apps. The app has one
    /// feedback button, so it names no kind; the version is in the details.
    static let subject = "Plain Text Fin Calc feedback (iOS)"

    /// A `mailto:` link that opens a draft addressed to support.
    static func emailURL(details: String) -> URL? {
        var components = URLComponents()
        components.scheme = "mailto"
        components.path = Links.feedbackEmail
        components.queryItems = [
            URLQueryItem(name: "subject", value: subject),
            URLQueryItem(name: "body", value: details),
        ]
        return components.url
    }

    /// The draft link for this app and device.
    @MainActor
    static func emailURLForThisDevice() -> URL? {
        let version = AppInfo.version
        return emailURL(
            details: details(
                version: version,
                systemName: UIDevice.current.systemName,
                systemVersion: UIDevice.current.systemVersion,
                device: hardwareModel(),
            ),
        )
    }

    /// Hardware identifier such as `iPhone17,3`, after the device family.
    @MainActor
    private static func hardwareModel() -> String {
        var system = utsname()
        uname(&system)
        let machine = withUnsafeBytes(of: &system.machine) { bytes in
            String(decoding: bytes.prefix { $0 != 0 }, as: UTF8.self)
        }
        return "\(UIDevice.current.model) (\(machine))"
    }
}

/// Facts about the running app bundle.
enum AppInfo {
    static var version: String {
        Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString")
            as? String ?? "unknown"
    }
}
