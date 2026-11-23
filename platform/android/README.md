# Plain Text Fin Calc for Android

Native Kotlin calculator with decimal arithmetic, reusable calculation history,
light/dark themes, display precision settings, and CSV export.

## Build and run

Open this directory in Android Studio. Install Android SDK Platform 37 and let
Gradle sync. Select the **app** configuration and an Android 8.0 (API 26) or
newer device or emulator, then click Run.

The project uses Android Gradle Plugin 9.5.1 and the included Gradle 9.9.1
wrapper. Gradle runs on the JDK 25 toolchain pinned in
`gradle/gradle-daemon-jvm.properties` and downloads it on first use when no
matching JDK is installed. Set `ANDROID_HOME` to your SDK directory, or let
Android Studio create an ignored `local.properties` with `sdk.dir`. Python is
not required.

Open `platform/android/` itself rather than the repository root. Android
Studio's `.idea/` directories and `*.iml` files are ignored local IDE state; do
not move them between project roots. The Gradle project files and wrapper are
shared.

From this directory in PowerShell:

```powershell
.\gradlew.bat testDebugUnitTest lintDebug assembleDebug
.\gradlew.bat installDebug
```

The debug APK is `app/build/outputs/apk/debug/app-debug.apk`.

## Using the calculator

Enter an expression with the keypad and tap **=**. Tap a saved result to reuse
its full precision. **C** clears input; **⌫** deletes the last character.
Use **log**, parentheses, and a positive value for base-10 logarithms.

The **⋮** menu contains Settings, Export History, Clear History, Send
Feedback, Privacy Policy, and About. Send Feedback offers two choices for bug
reports and feature requests: Email drafts a message to
`support@plaintxtoffice.com`, ending with the app version, Android version, and
device model, and Contact form opens `https://plaintxtoffice.com/contact/` in a
browser. Privacy
Policy opens the Plain Text Office privacy policy in a browser.
Settings provide full precision or 0–6 decimal places, light/dark appearance,
and a history limit of 1–10,000 entries or Unlimited. Export opens Android's
document picker and writes UTF-8 CSV with `timestamp,expression,result` columns.

History and settings are saved in app-private `calculator.json`. Uninstalling or
clearing app data removes them; export anything you want to retain first. The
app requests no network or storage permissions and disables Android backup.
Each platform keeps its own history; there is no cross-device synchronization.

## Arithmetic and validation

The engine uses `BigDecimal`, 28 significant digits, and half-even rounding.
Display rounding does not change stored results. Unary minus binds more tightly
than powers, and powers associate to the right, matching the Windows engine.

Inputs are limited to 128 tokens and 2,048 characters. The mobile engine bounds
decimal exponents to ±9,999 to keep calculations
responsive. These limits are narrower than Python Decimal's range. Logarithms
and fractional powers use decimal series with guard digits; their final digit
can differ from the Windows implementation.

Unit tests cover calculation errors, history reuse, settings, failed saves,
restart persistence, CSV escaping, and 59 reference calculations generated from
`platform/windows/plain_text_fin_calc/domains/calc/evaluator.py`. The reference
values live in `app/src/test/resources/python-reference.json`.

## Release preparation

Google Play listing images and guidance are in
[store assets](assets/store/README.md).

The application ID is `com.plaintxtoffice.fincalc`; the current version is
`0.4.0` with version code `6`. It compiles against API 37 and targets API 36.

```powershell
.\gradlew.bat bundleRelease
```

This creates a bundle named after the app and version, such as
`app/build/outputs/bundle/release/plain-text-fin-calc-0.4.0-6-release.aab`.
Gradle signs it when `keystore.properties` exists in `platform/android/`; copy
`keystore.properties.example` to create it and fill in your upload key. Without
that file the bundle is **unsigned**. Keep the key and passwords outside version
control. Increment the version code before subsequent Play releases. This
project does not include store submission credentials or upload automation.

## Source layout

- `domains/calc/`: decimal arithmetic, expression input, history, formatting.
- `config/`: settings values.
- `adapters/`: JSON persistence and CSV output.
- `application/`: calculator sessions and background Android lifecycle state.
- `ui/`: keypad, tape, settings, and visual presentation.
- `MainActivity.kt`: activity lifecycle and document picker integration.

## Feedback

Send bug reports and feature requests with **⋮** > **Send Feedback** in the
app, by email to
[support@plaintxtoffice.com](mailto:support@plaintxtoffice.com), or through the
[contact form](https://plaintxtoffice.com/contact/).

## License

Plain Text Fin Calc is open source under the repository's
[MIT License](../../LICENSE). Copyright 2026 Plain Text Office LLC.
