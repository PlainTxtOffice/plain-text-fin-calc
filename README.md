<!-- last_updated: 2026-11-23 -->
<!-- Authoring guidance: dev-docs/specs/README_SPEC.instructions.md -->
<!-- rumdl-disable MD033 MD041 -->
<p align="center">
  <img src="assets/icons/icon-github-readme.svg" alt="Plain Text Fin Calc app icon" width="96">
</p>

<h1 align="center">Plain Text Fin Calc</h1>

<p align="center">
  A decimal calculator for everyday figures and financial calculations, with a saved calculation tape.
</p>

<p align="center">
  <a href="https://play.google.com/store/apps/details?id=com.plaintxtoffice.fincalc"><img src="https://img.shields.io/badge/release-Google%20Play-blue" alt="Android release: Google Play"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-informational" alt="License: MIT"></a>
  <a href="#download"><img src="https://img.shields.io/badge/platform-Android-informational" alt="Platform: Android; see download availability"></a>
</p>

<p align="center">
  <a href="#download">Download</a> ·
  <a href="docs/USER_MANUAL.md">User manual</a>
</p>
<!-- rumdl-enable MD033 MD041 -->

---

## About

Plain Text Fin Calc helps you check figures, review how you reached a total,
and reuse earlier results without retyping them. It is available for Android on
Google Play. The iPhone and iPad app is in App Store review, and the Windows app
is in development. Your calculation history and settings stay on each device
between sessions; they do not sync across devices. Plain Text Fin Calc is open
source under the MIT License.

## Features

- Calculate with decimals, parentheses, powers, and base-10 logarithms. Decimal
  arithmetic gives `0.1 + 0.2 = 0.3`.
- Review saved calculations and reuse their full-precision results in the
  graphical apps: on Android today, and on iPhone and iPad (in App Store
  review) and Windows (in development).
- Export the calculation tape as CSV from the Android app. The iPhone and iPad
  app (in App Store review) and the Windows graphical app (in development)
  also export CSV, and the Windows graphical app can save a plain text tape
  with your choice of time zone, date and time formats, seconds, and UTC
  offsets.
- Choose light or dark appearance and full precision or 0–6 displayed decimal
  places. Display rounding leaves saved results unchanged.
- Use an optional RPN (reverse Polish notation) input mode in the Android app
  (version 0.5.0 and later); it is in development for iPhone, iPad, and
  Windows. RPN mode has a four-level stack and **ENTER**, **x↔y**, and
  **DROP** keys. Results
  match algebraic entry, each calculation goes on the tape as its equivalent
  expression, and CSV exports add the keys pressed in an `rpn_input` column.
  On Windows, the terminal interface and command line take RPN as typed lines
  such as `3 4 +`, and the plain text tape lists the keys on an `RPN input:`
  line under each RPN calculation.
- Use a graphical window, a terminal interface, or a command-line calculator on
  Windows (in development).
- Send a bug report or feature request from the Android app with
  **Send Feedback**, from the iPhone and iPad app (in App Store review) with
  **Send Feedback**, or from the Windows app (in development) with **Help** >
  **Send Feedback...**.

## What's New

Plain Text Fin Calc is the new name for Fin Calc. Compared with Fin Calc 0.3.1
on Google Play:

- The source code is open under the MIT License.
- Android: the same calculator and saved tape, now named Plain Text Fin Calc.
- iPhone and iPad (in App Store review): a new app with the same decimal
  calculator, a saved tape, CSV export through the share sheet, and
  **Copy Result** on any saved calculation.
- Windows (in development): save the tape as plain text, choosing the time
  zone, date and time formats, whether to show seconds, and UTC offsets.

## App Screenshot

### Windows GUI

<!-- rumdl-disable MD033 -->
<a href="platform/windows/assets/screenshots/windows-calculator.png">
  <img src="platform/windows/assets/screenshots/windows-calculator.png"
       alt="Plain Text Fin Calc for Windows, showing saved calculations and a numeric keypad"
       width="440">
</a>
<!-- rumdl-enable MD033 -->

Windows graphical app; the download below is for Android.

### Android

<!-- rumdl-disable MD033 -->
<a href="platform/android/assets/screenshots/android-calculator.png">
  <img src="platform/android/assets/screenshots/android-calculator.png"
       alt="Plain Text Fin Calc for Android in the light theme, showing saved calculations"
       width="280">
</a>
<!-- rumdl-enable MD033 -->

Calculator view from an earlier Android release, under the app's former name.

<!-- Add an actual iOS capture when one is available. -->

## Download

| Platform | Download | Notes |
| --- | --- | --- |
| Android | [Google Play](https://play.google.com/store/apps/details?id=com.plaintxtoffice.fincalc) | Android 8.0 or newer. |

The iPhone and iPad app is in App Store review and is not yet available. The
Windows app is in development, and no download is provided yet.

## User Manual

See the [User Manual](docs/USER_MANUAL.md) for installation, setup, usage, and
troubleshooting.

## Feedback

Bug reports and feature requests are welcome. Email
[support@plaintxtoffice.com](mailto:support@plaintxtoffice.com) or use the
[contact form](https://plaintxtoffice.com/contact/) on plaintxtoffice.com. In
the Android app, choose **Send Feedback** in the **⋮** menu. The iPhone and iPad
app, in App Store review, has it in the **More** menu, and the Windows app, in
development, has **Help** > **Send Feedback...**.

## License

Plain Text Fin Calc is open source under the [MIT License](LICENSE). Copyright
2026 Plain Text Office LLC.
