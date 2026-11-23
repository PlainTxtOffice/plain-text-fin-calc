---
last_updated: 2026-11-22
version: 6.2.1
product_versions:
  windows: "0.1.0"
  ios: "1.0.0"
  android: "0.4.0"
generated_from: "dev-docs/specs/USER_MANUAL_SPEC.instructions.md"
---

# User Manual

## Overview

Plain Text Fin Calc is a calculator for exact decimal arithmetic. It adds,
subtracts, multiplies, divides, raises to powers, and takes base-10 logarithms
using decimal numbers, so `0.1 + 0.2` gives `0.3` rather than a binary rounding
error. Every successful calculation is saved to a scrolling list called the
tape, which you can reuse, clear, and export as a CSV file. The Windows
graphical app can also save the tape as plain text.

Plain Text Fin Calc is for anyone who wants predictable decimal results and a
running record of their calculations, such as when checking figures or totals.

<!-- Verified from: platform/windows/pyproject.toml [project.description] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/domains/calc/evaluator.py [evaluate] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/views/root_window.py [RootWindow] -->

Plain Text Fin Calc runs on three platforms. Each keeps its own saved history
and settings; nothing is synchronized between them. The Android app is in
Google Play review; the iOS app is in App Store review, and the Windows app is
in development. Plain Text Fin Calc is open source under the MIT License.

| Platform | Interfaces | Version | Status |
| --- | --- | --- | --- |
| Windows | Graphical window, terminal interface, and command line | 0.1.0 | In development |
| iOS (iPhone and iPad) | Touch app | 1.0.0 | In App Store review |
| Android | Touch app | 0.4.0 | In Google Play review |

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/cli/app.py [select_interface] -->
<!-- Verified from: platform/windows/pyproject.toml [project.version] -->
<!-- Verified from: platform/ios/FinCalc.xcodeproj/project.pbxproj [MARKETING_VERSION, TARGETED_DEVICE_FAMILY] -->
<!-- Verified from: platform/ios/FinCalc/Config/PathHandler.swift [PathHandler] -->
<!-- Verified from: platform/android/app/build.gradle.kts [versionName] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/application/CalculatorModel.kt [CalculatorModel] -->
<!-- Verified from: plaintxtoffice_manager/dev-docs/APPS.md [Store Status]; dev-docs/OPEN_ITEMS.md -->

## Installation and Setup

### Check System Requirements

| Platform | Requirement |
| --- | --- |
| Windows (in development) | Python 3.14 or newer. |
| iOS | iOS or iPadOS 26.4 or newer on an iPhone or iPad. |
| Android (in Google Play review) | Android 8.0 (API level 26) or newer. |

<!-- Verified from: platform/windows/pyproject.toml [requires-python] -->
<!-- Verified from: platform/ios/FinCalc.xcodeproj/project.pbxproj [IPHONEOS_DEPLOYMENT_TARGET, TARGETED_DEVICE_FAMILY] -->
<!-- Verified from: platform/android/app/build.gradle.kts [minSdk] -->

The Windows version also uses the PySide6 (6.7 or newer), Textual (6.6 or
newer), and Typer (0.21 or newer) packages.

<!-- Verified from: platform/windows/pyproject.toml [project.dependencies] -->

### Install Plain Text Fin Calc

#### Install on Windows

The Windows app is in development. It has no download or installer yet, so
it cannot be installed. The Windows sections of this manual describe the app
as it is being built, so that they are ready when it is released.

When the Windows app runs from its project folder, it keeps its saved data in
that folder. A packaged Windows program opens the graphical window when
started without options and stores its data in a different folder; see
[Data Files on Windows](#data-files-on-windows).

<!-- Verified from: plaintxtoffice_manager/dev-docs/APPS.md [Store Status] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/config/path_handler.py [DEV_ROOT, ROOT_DIR] -->

<!-- Verified from: platform/windows/main.py -->
<!-- Verified from: platform/windows/plain_text_fin_calc/config/path_handler.py [IS_COMPILED, USER_DATA_DIR] -->

#### Install on iOS and Android

The Android app is in Google Play review and is not yet available to
download. It requires Android 8.0 or later and requests no network or storage
permissions.

The iOS app is in App Store review and is not yet available to download.

On iOS, the app appears as **Fin Calc** on the Home Screen. On Android, it
appears as **Plain Text Fin Calc** in the app launcher. Its identifier is
`com.plaintxtoffice.fincalc` on both iOS and Android.

<!-- Verified from: platform/ios/FinCalc.xcodeproj/project.pbxproj [PRODUCT_BUNDLE_IDENTIFIER, INFOPLIST_KEY_CFBundleDisplayName] -->
<!-- Verified from: platform/android/app/build.gradle.kts [applicationId, minSdk] -->
<!-- Verified from: plaintxtoffice_manager/dev-docs/APPS.md [Store Status] -->
<!-- Verified from: platform/android/app/src/main/res/values/strings.xml [app_name] -->
<!-- Verified from: platform/android/app/src/main/AndroidManifest.xml -->

### Set Up Plain Text Fin Calc for First Use

No setup is required. On first start, Plain Text Fin Calc uses its default
settings: full precision, the Dark theme, and a limit of 1,000 saved history
entries. The first calculation or settings change creates the data files. To
change the defaults, see [Settings and Preferences](#settings-and-preferences).

<!-- Verified from: platform/windows/plain_text_fin_calc/config/settings.py [Settings] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/adapters/history_store.py [load_history, write_history] -->
<!-- Verified from: platform/ios/FinCalc/Config/Settings.swift [Settings] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/config/Settings.kt [Settings] -->

## Starting the Program

### Start Plain Text Fin Calc

#### Start on Windows

The Windows app is in development and has no released download. When it runs
from its project folder, run every command from the `platform/windows/`
folder.

| To open | Command |
| --- | --- |
| A menu that asks which interface to use | `.venv/Scripts/python.exe -m plain_text_fin_calc.main` |
| The graphical window | `.venv/Scripts/python.exe -m plain_text_fin_calc.main --gui` |
| The terminal interface | `.venv/Scripts/python.exe -m plain_text_fin_calc.main --tui` |
| The command-line help | `.venv/Scripts/python.exe -m plain_text_fin_calc.main --cli` |

You can use `.venv/Scripts/fin-calc.exe` in place of
`.venv/Scripts/python.exe -m plain_text_fin_calc.main` in any command, for
example `.venv/Scripts/fin-calc.exe --gui`.

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/cli/app.py [select_interface] -->
<!-- Verified from: platform/windows/pyproject.toml [project.scripts] -->

When you start without an option, Plain Text Fin Calc shows this menu:

```text
Choose an interface:
  1. GUI (python -m plain_text_fin_calc.main --gui)
  2. TUI (python -m plain_text_fin_calc.main --tui)
  3. CLI prompt (python -m plain_text_fin_calc.main --cli)
  q. Quit
Selection:
```

Type `1`, `2`, or `3` (or `gui`, `tui`, or `cli`) and press **Enter**. Type
`q` to leave without starting. Any other entry shows
`Enter 1, 2, 3, or q.` If input comes from a file or another program instead
of the keyboard, the menu is not shown; give an option or a command instead.

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/cli/launch.py [choose_interface] -->

What to expect on startup:

- **Graphical window**: a window titled **Plain Text Fin Calc** opens with your
  saved tape, an empty display, and the keypad.
- **Terminal interface**: the screen shows a **Plain Text Fin Calc** header,
  your saved tape, the prompt `Enter an expression and press Enter.`, and an
  entry field with the hint `Example: 0.1 + 0.2 or log(100)`.
- **Command line**: `--cli` opens a persistent `fin-calc>` prompt. Commands
  such as `calculate` print their output and return to the system shell. See
  [Use the Windows Command Line](#use-the-windows-command-line).

If the saved data folder cannot be used, Plain Text Fin Calc prints
`Unable to start calculator:` followed by the reason.

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/views/root_window.py [RootWindow.__init__] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/tui/app.py [CalculatorApp.compose] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/cli/app.py [select_interface] -->

A packaged Windows program opens the graphical window when started without
options. It accepts the same options and commands.

<!-- Verified from: platform/windows/main.py -->

#### Start on iOS and Android

Tap **Fin Calc** on the iOS Home Screen, or **Plain Text Fin Calc** in the
Android app launcher. The calculator opens with your saved tape, the display,
and the keypad. On iOS, an empty tape shows `Calculations appear here`. On
Android, it shows
`Results appear here.` and `Tap one to reuse it.`

On Android, the status line shows `Loading…` while saved data loads, and the
**⋮** menu does not open until it finishes. If the saved data cannot be read,
the status line shows
`Could not load saved history and settings. Defaults are in use.`

<!-- Verified from: platform/ios/FinCalc/FinCalcApp.swift [FinCalcApp] -->
<!-- Verified from: platform/ios/FinCalc/UI/Views/TapeView.swift [TapeView] -->
<!-- Verified from: platform/ios/FinCalc/UI/Views/DisplayView.swift [DisplayView] -->
<!-- Verified from: platform/android/app/src/main/AndroidManifest.xml -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/ui/CalculatorView.kt [CalculatorView.empty] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/application/CalculatorModel.kt [ScreenState, CalculatorModel.init] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/MainActivity.kt [showMenu] -->

### Quit Plain Text Fin Calc

- **Windows graphical window**: choose **File** > **Exit**, or close the
  window. Plain Text Fin Calc finishes saving history before it closes.
- **Windows terminal interface**: press **Ctrl+Q**.
- **Windows command line**: at `fin-calc>`, type `exit` or `quit`, press
  **Ctrl+C**, or end input (**Ctrl+Z**, then **Enter**). One-shot commands end
  on their own.
- **iOS and Android**: the app has no quit command. Leave it as you leave any
  app. Your history is already saved: iOS finishes saving when the app moves
  to the background, and Android saves each change as soon as it is made.

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/menus/menu_bar.py [build_menu_bar] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/views/root_window.py [RootWindow.closeEvent] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/tui/app.py [CalculatorApp.BINDINGS] -->
<!-- Verified from: platform/ios/FinCalc/FinCalcApp.swift [FinCalcApp.body] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/application/CalculatorSession.kt [commit] -->

## Getting Around

The touch apps and the Windows graphical window share the same layout:

- **Tape**: the list of saved calculations, each shown as
  `expression = result`, newest at the bottom. iOS and Android show the
  expression on one line and `= result` on the next, aligned to the right.
- **Display**: the expression you are entering, or the result after you
  evaluate. A status line under it shows errors.
- **Keypad**: number, operator, and action keys.

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/views/root_window.py [RootWindow.__init__] -->
<!-- Verified from: platform/ios/FinCalc/UI/Views/RootView.swift [RootView.body] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/ui/CalculatorView.kt [CalculatorView] -->

The keypad has these keys on every platform:

| Key | What it does |
| --- | --- |
| **0**–**9**, **.** | Enter a number. |
| **+**, **-**, **\***, **/**, **^** | Add, subtract, multiply, divide, or raise to a power. |
| **(**, **)** | Group part of an expression. |
| **log** | Start a base-10 logarithm, such as `log ( 100 )`. |
| **±** | Change the sign of the number being entered. |
| **C** | Clear the whole expression. History is not affected. |
| **←** (Windows) or **⌫** (iOS, Android) | Delete the last character. |
| **=** | Evaluate the expression and save it to the tape. |

The iOS and Android keys, display, and tape show **×** for multiply, **÷**
for divide, and **−** for subtract and for negative numbers.
Saved history and CSV exports keep `*`, `/`, and `-`.

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/views/keypad.py [BUTTON_LAYOUT] -->
<!-- Verified from: platform/ios/FinCalc/UI/Views/KeypadView.swift [KeypadView.rows, KeyLabels] -->
<!-- Verified from: platform/ios/FinCalc/UI/Views/TapeView.swift [TapeView.row] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/ui/KeypadView.kt [KeyLabels, KeypadView] -->

### Tour the Calculator

The graphical window and the touch apps differ in their menus and a few
layout details:

| Platform | Menus | Layout and feedback |
| --- | --- | --- |
| Windows graphical window | A menu bar with **File**, **Edit**, and **Help**. | Errors appear in red under the expression. Export and settings messages appear in the status bar at the bottom. You can type on the keyboard instead of clicking keys. |
| iOS | A **History** menu (clock icon) on the left of the top bar and a **More** menu (ellipsis icon) on the right. | In portrait, the keypad fills the lower half of the screen. In landscape, the tape moves to the left and the display and keypad to the right. Keys and errors give haptic feedback. If iOS closes the app in the background, the expression you were entering returns when you reopen it. |
| Android | A **⋮** button on the right of the top bar. | In landscape, the tape moves to the left and the display and keypad to the right. |

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/menus/menu_bar.py [build_menu_bar] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/views/display.py [DisplayView] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/views/root_window.py [RootWindow._on_export_history, RootWindow.keyPressEvent] -->
<!-- Verified from: platform/ios/FinCalc/UI/Views/RootView.swift [RootView.toolbarContent, RootView.body] -->
<!-- Verified from: platform/ios/FinCalc.xcodeproj/project.pbxproj [INFOPLIST_KEY_UISupportedInterfaceOrientations_iPhone, INFOPLIST_KEY_UISupportedInterfaceOrientations_iPad] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/MainActivity.kt [buildViews] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/ui/CalculatorView.kt [CalculatorView.init] -->

#### Tour the Windows Terminal Interface

The terminal interface has a header, a bordered tape, a result line, an entry
field, and a footer that includes **Quit** (**Ctrl+Q**) and **Clear input**
(**Esc**). You type whole expressions into the entry field. The tape is for
reading only.

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/tui/app.py [CalculatorApp] -->

#### Tour the Windows Command Line

Start with `--cli` to keep a `fin-calc>` prompt open for repeated calculations.
Type an expression without quotes and press **Enter**. Use `history` to show
saved calculations, `help` for instructions, and `exit` or `quit` to leave.

One-shot use has the form
`plain_text_fin_calc.main [OPTION] COMMAND [ARGUMENT]`. The commands are
`calculate` and `history`. Add `--help` after any command to see its help.

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/cli/app.py [app] -->

### Find Help

| Platform | Where to find help |
| --- | --- |
| Windows graphical window | **Help** > **Keyboard Shortcuts** lists keyboard keys. **Help** > **Send Feedback...** offers an email draft or the website contact form for bug reports and feature requests. **Help** > **About** shows the version. |
| Windows command line | Add `--help`, as in `.venv/Scripts/python.exe -m plain_text_fin_calc.main calculate --help`. |
| iOS | **More** > **Settings** > **About** shows the version and short tips. **More** > **Send Feedback** offers an email draft or the website contact form for bug reports and feature requests. **More** > **Privacy Policy** opens the privacy policy. |
| Android | **⋮** > **About** shows the version and short tips. **⋮** > **Send Feedback** offers an email draft or the website contact form for bug reports and feature requests. **⋮** > **Privacy Policy** opens the privacy policy. |

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/dialogs/help_dialogs.py [show_about, show_shortcuts] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/menus/menu_bar.py [build_menu_bar] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/cli/commands.py [calculate] -->
<!-- Verified from: platform/ios/FinCalc/UI/Views/SettingsView.swift [SettingsView.body] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/MainActivity.kt [showMenu] -->

## Everyday Tasks

### Enter and Evaluate an Expression

Expressions use numbers, `+`, `-`, `*`, `/`, `^`, parentheses, and `log( )`
for base-10 logarithms. Operators follow the usual order: parentheses and
`log` first, then a leading minus sign, then powers, then multiplication and
division, then addition and subtraction. Powers group from the right, so
`2 ^ 3 ^ 2` is `512`. A leading minus sign belongs to its number, so
`-2 ^ 2` is `4`.

<!-- Verified from: platform/windows/plain_text_fin_calc/domains/calc/evaluator.py [module docstring, _Parser] -->
<!-- Verified from: platform/ios/FinCalc/Domains/Calc/Evaluator.swift [Evaluator] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/domains/calc/Evaluator.kt [Evaluator] -->
<!-- Verified from: platform/android/app/src/test/resources/python-reference.json -->

Results that cannot be calculated show one of these messages:

| Message | Meaning |
| --- | --- |
| `Division by zero` | The expression divides by zero. |
| `Log undefined for non-positive values` | `log` was given zero or a negative number. |
| `Expected '(' after log` | `log` is not followed by an opening parenthesis. |
| `Mismatched parentheses` | An opening parenthesis has no matching closing one. |
| `Invalid exponentiation:` followed by the values | The power cannot be calculated, such as `0 ^ 0` or a fractional power of a negative number. |
| `Result out of range` | The result is too large or too small. See [Understand Precision and Limits](#understand-precision-and-limits). |
| `Unexpected end of expression` | The expression ends with an operator. |
| `Unexpected token after expression` | Something follows a complete expression, such as `2(3)` typed on Windows. |

An unmatched parenthesis inside `log` shows
`Mismatched parentheses in log` on Windows and iOS.

<!-- Verified from: platform/windows/plain_text_fin_calc/domains/calc/evaluator.py [_Parser] -->
<!-- Verified from: platform/ios/FinCalc/Domains/Calc/Evaluator.swift [Parser] -->
<!-- Verified from: platform/ios/FinCalc/Domains/Calc/DecimalMath.swift [power] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/domains/calc/Evaluator.kt [Parser] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/domains/calc/DecimalMath.kt [power] -->

When you build an expression with keys, Plain Text Fin Calc ignores keys that do
not fit at that point and shows `Invalid input:` followed by the key. For
example:

- A number cannot directly follow `)` or `log`, and `(` or `log` cannot
  directly follow a number. Type an operator between them.
- `)` is accepted only when an opening parenthesis is still open.
- A number can have only one decimal point. Starting a number with `.`
  enters `0.`.
- After an operator or `(`, the `-` key starts a negative number. Other
  operators after an operator are ignored.

<!-- Verified from: platform/windows/plain_text_fin_calc/domains/calc/expression.py [ExpressionBuilder] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/views/root_window.py [RootWindow._on_token] -->
<!-- Verified from: platform/ios/FinCalc/Domains/Calc/ExpressionBuilder.swift [ExpressionBuilder] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/domains/calc/ExpressionBuilder.kt [ExpressionBuilder] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/application/CalculatorSession.kt [press] -->

In the Windows graphical window and the iOS and Android apps:

1. Click or tap keypad keys. In the Windows window, or on iOS with a hardware
   keyboard, you can also type digits, `.`, `+`, `-`, `*`, `/`, `^`, `(`, and
   `)`, and press **L** to enter `log`.
1. Click or tap **=**. On a keyboard, press **Enter** on Windows or **Return**
   on iOS.

The display shows the result, and the calculation is added to the tape. On
iOS and Android, you can select and copy the display text. On iOS and Android,
the keypad stops accepting keys when the expression reaches 128 symbols or 2,048
characters.

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/views/keypad.py [KEY_MAP] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/views/root_window.py [RootWindow.keyPressEvent, RootWindow._on_evaluate] -->
<!-- Verified from: platform/ios/FinCalc/UI/Views/RootView.swift [RootView.pressHardwareKey] -->
<!-- Verified from: platform/ios/FinCalc/Application/CalculatorSession.swift [evaluate] -->
<!-- Verified from: platform/ios/FinCalc/UI/Views/DisplayView.swift [DisplayView] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/application/CalculatorSession.kt [press, calculate] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/ui/CalculatorView.kt [CalculatorView] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/domains/calc/ExpressionBuilder.kt [add] -->

#### Enter an Expression in the Windows Terminal Interface

1. Type the whole expression in the entry field, such as `0.1 + 0.2` or
   `log(100)`.
1. Press **Enter**.

The result line shows `Result:` and the answer, the tape updates, and the
entry field clears. If the expression is not valid, the result line shows
`Error:` and the reason, and your entry stays so you can correct it.

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/tui/app.py [CalculatorApp.on_input_submitted] -->

#### Enter an Expression on the Windows Command Line

From `platform/windows/`:

```powershell
.venv/Scripts/python.exe -m plain_text_fin_calc.main calculate "0.1 + 0.2"
```

Plain Text Fin Calc prints `0.3` and saves the calculation. Quote the
expression. If it starts with a minus sign, put `--` before it:

```powershell
.venv/Scripts/python.exe -m plain_text_fin_calc.main calculate -- "-2 ^ 2"
```

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/cli/commands.py [calculate] -->

Typed expressions in the terminal interface and on the command line follow
these rules:

- Numbers may use scientific notation, such as `1.5e3`.
- Spaces are optional between symbols, but a space never joins two numbers.
- The limit is 2,048 characters and 128 symbols.
- Any other character, such as `x` or `,`, shows
  `Invalid input at character` and its position.

<!-- Verified from: platform/windows/plain_text_fin_calc/domains/calc/parsing.py [parse_expression] -->

### Correct or Clear the Current Expression

These keys change only the expression you are entering. They never change the
saved tape.

| To | Windows graphical window | iOS | Android |
| --- | --- | --- | --- |
| Delete the last character | **←** or **Backspace** | **⌫**, or **Delete** on a hardware keyboard | **⌫** |
| Clear the whole expression | **C** or **Esc** | **C**, or **Esc** on a hardware keyboard | **C** |
| Change the sign of the current number | **±** | **±** | **±** |

Deleting removes one digit of a number, or the whole last operator,
parenthesis, or `log`. In the Windows terminal interface, edit the entry field
as usual, or press **Esc** to clear it.

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/views/root_window.py [RootWindow.keyPressEvent] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/domains/calc/expression.py [ExpressionBuilder.backspace, ExpressionBuilder.toggle_sign] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/tui/app.py [CalculatorApp.action_clear_input] -->
<!-- Verified from: platform/ios/FinCalc/UI/Views/RootView.swift [RootView.pressHardwareKey] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/domains/calc/ExpressionBuilder.kt [backspace, toggleSign] -->

### Continue From a Result

After you evaluate, the result stays in the display as the start of the next
expression. This applies to the Windows graphical window, iOS, and Android.

- Press an operator to continue from the result, such as `+ 5`.
- Press a digit, `.`, `(`, or **log** to start a new expression instead.

Continuing uses the result's full precision, even when the display rounds it.

<!-- Verified from: platform/windows/plain_text_fin_calc/domains/calc/expression.py [ExpressionBuilder.insert_result, ExpressionBuilder._continue_from_result] -->
<!-- Verified from: platform/ios/FinCalc/Domains/Calc/ExpressionBuilder.swift [continueFromResult] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/domains/calc/ExpressionBuilder.kt [add] -->

### Reuse a Result From the Tape

Click or tap a line on the tape to place its result into the current
expression with its full precision.

On Android and in the Windows graphical window, a reused result replaces the
current number or previous answer. For example, tapping `6` while entering
`2 * 9` changes the input to `2 * 6`. If the input is empty or ends with an
operator or `(`, the result is inserted there.

On iOS, reusing a result has no effect when the expression ends with a number.
You can also touch and hold a line, then choose **Use Result**, or choose
**Copy Result** to copy the full-precision result. The Windows terminal
interface and command line cannot reuse results.

<!-- Verified from: platform/windows/plain_text_fin_calc/domains/calc/expression.py [ExpressionBuilder.insert_result] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/views/tape.py [TapeView._on_item_clicked] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/tui/app.py [CalculatorApp.compose] -->
<!-- Verified from: platform/ios/FinCalc/Domains/Calc/ExpressionBuilder.swift [insertResult] -->
<!-- Verified from: platform/ios/FinCalc/UI/Views/TapeView.swift [TapeView.row] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/domains/calc/ExpressionBuilder.kt [insertResult] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/ui/TapeView.kt [Rows.onBindViewHolder] -->

### Review Saved History

The tape shows your saved calculations in every interface, oldest at the top.
Results on the tape follow the **Decimal places** setting. To list saved
history on the Windows command line, from `platform/windows/`:

```powershell
.venv/Scripts/python.exe -m plain_text_fin_calc.main history
```

Each line has the form `expression = result`. The command only reads the
history; it does not change it.

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/cli/commands.py [history] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/domains/calc/formatting.py [format_history_line] -->
<!-- Verified from: platform/ios/FinCalc/UI/Views/TapeView.swift [TapeView.row] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/ui/TapeView.kt [Rows.onBindViewHolder] -->

Plain Text Fin Calc keeps up to the history limit set in
[Settings and Preferences](#settings-and-preferences) and removes the oldest
calculations first when the limit is reached.

<!-- Verified from: platform/windows/plain_text_fin_calc/domains/calc/history.py [History.append] -->
<!-- Verified from: platform/ios/FinCalc/Domains/Calc/History.swift [History.append] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/domains/calc/History.kt [trimHistory] -->

### Clear Saved History

Clearing removes every saved calculation on that device. It cannot be undone,
so export the history first if you want to keep it.

1. Choose **Clear History**:
   - Windows graphical window: **File** > **Clear History**, or right-click
     the tape.
   - iOS: the **History** menu. It is unavailable when the tape is empty.
   - Android: **⋮**.
1. Confirm when asked. The confirming button is **Yes** on Windows,
   **Clear History** on iOS (in `Clear All History?`), and **Clear** on
   Android. To keep your history, choose **No** on Windows or **Cancel** on
   Android.

The Windows terminal interface and command line cannot clear history.

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/menus/menu_bar.py [build_menu_bar] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/views/tape.py [TapeView.contextMenuEvent] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/views/root_window.py [RootWindow._on_clear_history] -->
<!-- Verified from: platform/ios/FinCalc/Application/CalculatorSession.swift [clearHistory] -->
<!-- Verified from: platform/ios/FinCalc/UI/Views/RootView.swift [RootView.toolbarContent, RootView.body] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/application/CalculatorSession.kt [clearHistory] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/MainActivity.kt [showMenu] -->

### Understand Precision and Limits

Plain Text Fin Calc keeps 28 significant digits and rounds half to even. For
example, `1 / 3` gives `0.3333333333333333333333333333` on every platform. The
**Decimal places** setting only rounds what you see; saved and reused results
keep their full precision.

<!-- Verified from: platform/windows/plain_text_fin_calc/domains/calc/evaluator.py [evaluate] -->
<!-- Verified from: platform/ios/FinCalc/Domains/Calc/DecimalMath.swift [DecimalMath.precision, roundToPrecision] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/domains/calc/DecimalMath.kt [context] -->
<!-- Verified from: platform/android/app/src/test/resources/python-reference.json -->

The platforms differ in range and in how full-precision results look:

| Platform | Range of results | How full-precision results look |
| --- | --- | --- |
| Windows | Much wider than the mobile apps; for example, `10 ^ 1000000` is `Result out of range`. | Very small results can use scientific notation, such as `1E-7`. Some results keep trailing zeros, such as `2.000000000000000000000000000` for `log(100)`. |
| iOS | About 1E-128 to 1E165. | Plain digits. |
| Android | Powers of ten from -9,999 to 9,999. | Plain digits with trailing zeros removed, such as `1000` for `500 + 500`. Results beyond 28 digits from the decimal point use scientific notation. |

Logarithms and fractional powers are computed differently on each platform,
so their last digit can differ between platforms.

<!-- Verified from: platform/windows/plain_text_fin_calc/domains/calc/evaluator.py [evaluate] -->
<!-- Verified from: platform/ios/FinCalc/Domains/Calc/DecimalMath.swift [exp, log10] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/domains/calc/DecimalMath.kt [checked, ln, exp] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/application/CalculatorSession.kt [calculate] -->

## Settings and Preferences

All platforms have the same three settings. Changes take effect as soon as
you save them and are kept between runs.

| Setting | Default | Accepted values | How to change it |
| --- | --- | --- | --- |
| **Decimal places** | Full precision | **Full precision**, or 0 through 6 | Settings on each platform |
| **Theme** | Dark | **Dark** or **Light** | Settings on each platform |
| Maximum history entries | 1,000 | 1 through 10,000, or **Unlimited** | Settings on each platform |
| **Plain text export (.txt)** | Local date headings and 24-hour times to the minute | Choose a zone, date order, clock style, seconds, and UTC offsets | Windows graphical Settings |

<!-- Verified from: platform/windows/plain_text_fin_calc/config/settings.py [Settings] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/domains/calc/history.py [DEFAULT_HISTORY_CAP, MIN_HISTORY_CAP, MAX_HISTORY_CAP] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/domains/calc/formatting.py [MAX_DECIMAL_PLACES] -->
<!-- Verified from: platform/ios/FinCalc/Config/Settings.swift [Settings] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/config/Settings.kt [Settings] -->

- **Decimal places** rounds results on the display and tape. Rounding is half
  to even, so `1.245` shows as `1.24` and `1.255` as `1.26` at two places.
  Shorter results are padded with zeros. If rounding would need more than 28
  digits, the full result is shown.
- **Theme** switches between dark and light colors.
- Maximum history entries sets how many calculations are kept. Lowering it
  removes the oldest calculations right away.

<!-- Verified from: platform/windows/plain_text_fin_calc/domains/calc/formatting.py [format_result] -->
<!-- Verified from: platform/ios/FinCalc/Domains/Calc/Formatting.swift [formatResult] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/domains/calc/Formatting.kt [formatResult] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/views/root_window.py [RootWindow._apply_settings] -->
<!-- Verified from: platform/ios/FinCalc/Application/CalculatorSession.swift [applySettings] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/application/CalculatorSession.kt [updateSettings] -->

### Change Settings

1. Open the settings: **Edit** > **Settings...** in the Windows graphical
   window, **Settings** on iOS, or **⋮** > **Settings** on Android.
1. Choose **Decimal places** and **Theme**.
1. Turn on **Unlimited**, or turn it off and enter the maximum number of
   history entries.
1. On Windows, use **Plain text export (.txt)** to choose a time zone and format
   the tape's dates and times. The preview updates as you change the options.
1. Save your changes with **OK** on Windows or **Save** on iOS and Android, or
   choose **Cancel** to discard them.

The history fields are labeled differently on each platform:

| Platform | Unlimited switch | Limit field |
| --- | --- | --- |
| Windows | **Unlimited** | **Max history entries:** |
| iOS | **Unlimited**, under **History** | **Max entries** |
| Android | **Unlimited history** | **Maximum history entries (1–10,000)** |

What happens with an out-of-range limit or a failed save depends on the
platform:

| Platform | Limit outside 1 to 10,000 | Settings cannot be saved |
| --- | --- | --- |
| Windows | The field accepts only allowed values. | The status bar shows `Saving settings failed:` and the reason. The new settings apply until you close the window. |
| iOS | Changed to the nearest allowed value when you save. | The status line shows `Settings could not be saved`. |
| Android | The field shows `Enter a whole number from 1 to 10,000` and the dialog stays open. | The status line shows `Could not save. Your previous history is unchanged.` Your previous settings stay in effect. |

On Windows, the terminal interface and command line use the same settings and
read them each time they start. The `fin-calc>` prompt can also change them
with `config`; see [Use the Persistent Prompt](#use-the-persistent-prompt).
The terminal interface cannot edit settings. You can also edit the settings
file by hand; see [Edit the Windows Data Files](#edit-the-windows-data-files).

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/dialogs/settings_dialog.py [SettingsDialog] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/views/root_window.py [RootWindow._on_open_settings, RootWindow._apply_settings] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/application/session.py [load_session] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/tui/app.py [CalculatorApp.__init__] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/cli/repl.py [run_repl] -->
<!-- Verified from: platform/ios/FinCalc/UI/Views/SettingsView.swift [SettingsView.body, selectedSettings] -->
<!-- Verified from: platform/ios/FinCalc/Application/CalculatorSession.swift [applySettings] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/ui/SettingsDialog.kt [showSettings] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/application/CalculatorModel.kt [submit] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/application/CalculatorSession.kt [commit] -->

## Importing and Exporting

You can export your saved history as a CSV file on every platform. Plain Text
Fin Calc cannot import history or other files. Exports always contain
full-precision results, whatever the **Decimal places** setting.

<!-- Verified from: platform/windows/plain_text_fin_calc/adapters/history_export.py [write_history_csv] -->
<!-- Verified from: platform/ios/FinCalc/Adapters/HistoryExport.swift [formatCSV] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/adapters/HistoryExport.kt [write] -->

### Export History to CSV

1. Choose the export command for your platform (see the table below).
1. Choose where to save or send the file.
1. Confirm the save.

| Platform | Command | Where you choose the location | Suggested name |
| --- | --- | --- | --- |
| Windows graphical window | **File** > **Export History...** | The **Export History** dialog, starting in the `exports` folder; click **Save** | `history.csv` |
| iOS | **History** menu > **Export CSV** | The share sheet, which can also send the file | `history.csv` |
| Android | **⋮** > **Export History** | Android's file picker | `plain-text-fin-calc-history.csv` |

On Windows and Android, saving over an existing file replaces it, and the
status bar or status line reports the result. On Windows, a name without
`.csv` gets it added, and the message is `Exported history to` and the path,
or `Export failed:` and the reason. On Android, it is `History exported.` or
`Could not export history. Choose another location and try again.` On iOS,
**Export CSV** is unavailable when the tape is empty. The Windows terminal
interface and command line cannot export.

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/views/root_window.py [RootWindow._on_export_history] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/config/path_handler.py [EXPORTS_DIR] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/adapters/history_export.py [write_history_csv] -->
<!-- Verified from: platform/ios/FinCalc/UI/Views/RootView.swift [RootView.toolbarContent, HistoryCSV] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/MainActivity.kt [export, showMenu] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/application/CalculatorModel.kt [export] -->

### Read the Exported CSV File

The file is UTF-8 text with a header row and one row per calculation, oldest
first.

| Column | What it contains |
| --- | --- |
| `timestamp` | When the calculation was made, as an ISO 8601 date and time in UTC. |
| `expression` | The expression as shown on the tape. |
| `result` | The full-precision result. |

A field that contains a comma, quotation mark, or line break is enclosed in
quotation marks. Example from Windows:

```csv
timestamp,expression,result
2026-10-25T14:03:07.512345+00:00,0.1 + 0.2,0.3
2026-10-25T14:03:20.104211+00:00,1 / 3,0.3333333333333333333333333333
```

<!-- Verified from: platform/windows/plain_text_fin_calc/adapters/history_export.py [write_history_csv] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/views/root_window.py [RootWindow._on_evaluate] -->

The details differ by platform:

| Platform | Timestamp example | Line endings |
| --- | --- | --- |
| Windows | `2026-10-25T14:03:07.512345+00:00` | CRLF |
| iOS | `2026-10-25T14:03:07Z` | CRLF |
| Android | `2026-10-25T14:03:07.512Z` (fraction length varies) | LF |

<!-- Verified from: platform/windows/plain_text_fin_calc/adapters/history_export.py [write_history_csv] -->
<!-- Verified from: platform/ios/FinCalc/Adapters/HistoryExport.swift [formatCSV] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/adapters/HistoryExport.kt [write] -->

### Export a Plain Text Tape on Windows

1. In the graphical window, choose **File** > **Export History...**.
1. Select **Plain Text Tape (*.txt)** as the file type, choose a name and
   location, and click **Save**.

The file contains the entire tape, oldest first. To change its layout, open
**Edit** > **Settings...** and find **Plain text export (.txt)**.
The preview shows up to five entries from your tape. Click **OK** to use
these choices for future text exports, including after restarting the app.

| Option | Effect |
| --- | --- |
| **Group by date** | Add a heading when the date changes in your selected time zone. |
| **Show time for each calculation** | Add a time before each expression. Clear this and **Group by date** to export just the calculations. |
| **Time zone** | Use **Computer local time**, **UTC**, or a named zone such as **America/New_York**. The zone applies to dates as well as times. |
| **Date format** | Choose year-month-day, month/day/year, or day/month/year for headings. |
| **Time format** | Choose a 24-hour clock or a 12-hour clock with AM/PM. |
| **Include seconds** | Show the seconds recorded for each calculation. |
| **Include UTC offset** | Append the offset at the time of the calculation, such as `UTC-04:00`. This distinguishes repeated times when daylight saving time ends. |

By default, the tape uses your computer's local zone, year-month-day headings,
and 24-hour times to the minute:

```text
2026-11-22
09:14  12 * 85 = 1020
09:15  1020 * 0.05 = 51
```

Results use full saved precision. Exporting an empty tape creates an empty file.

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/views/root_window.py [RootWindow._on_export_history] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/dialogs/text_export.py [TextExportSettings] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/domains/calc/text_tape.py [format_text_tape] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/adapters/history_export.py [write_history_text] -->

## Commands and Shortcuts

### Use the Windows Command Line

Run from `platform/windows/` as
`.venv/Scripts/python.exe -m plain_text_fin_calc.main` or
`.venv/Scripts/fin-calc.exe`, followed by one of these:

| Command or option | Accepted values | What it does |
| --- | --- | --- |
| (none) | None | Shows the interface menu. |
| `--gui` | None | Opens the graphical window. |
| `--tui` | None | Opens the terminal interface. |
| `--cli` | None, or a command | Alone, opens the persistent calculator prompt. With a command, runs it once. |
| `calculate EXPRESSION` | A quoted expression | Prints the result, rounded to **Decimal places**, and saves it to history. |
| `history` | None | Prints saved history without changing it. |
| `--help` | None | Shows help for Plain Text Fin Calc or for the command it follows. |
| `--` | Placed before an expression | Lets an expression start with a minus sign. |

Use only one of `--gui`, `--tui`, and `--cli`, and do not combine `--gui` or
`--tui` with a command. A command ends with status 0 on success and 1 when the
expression is invalid or history cannot be saved or read; it prints `Error:`
and the reason. Incorrect options end with status 2.

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/cli/app.py [select_interface, run_app] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/cli/commands.py [calculate, history] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/application/session.py [CalculatorSession.calculate] -->

#### Use the Persistent Prompt

Start it from `platform/windows/`:

```powershell
.venv/Scripts/python.exe -m plain_text_fin_calc.main --cli
```

Enter expressions directly, without quotes or the `calculate` command:

```text
fin-calc> 125 * 1.08
135
fin-calc> 135 / 12
11.25
fin-calc> history
125 * 1.08 = 135
135 / 12 = 11.25
fin-calc> exit
```

The example assumes empty history and full-precision display. Each successful
calculation is saved immediately. Results and `history` use the display
settings; saved results retain full precision. Negative
expressions need no `--` prefix here.

Type `config` to show current settings and allowed values. To change a setting:

```text
fin-calc> config decimal_places 4
fin-calc> config decimal_places full
fin-calc> config max_history_entries 500
fin-calc> config max_history_entries unlimited
fin-calc> config theme light
```

Decimal places accepts 0 through 6 or `full`. It changes displayed results
and history immediately, while calculations and saved results keep full
precision. History limits accept 1 through 10,000 or `unlimited` and take
effect on the next calculation or restart. A limit that would discard older
entries asks for confirmation; pressing **Enter** keeps the previous setting.
Theme accepts `dark` or `light` and affects the graphical interface, not the
console window. Restart another running interface to load changed settings.
Changes persist automatically; invalid values or failed saves leave the active
settings unchanged. `config` is a prompt command, not a one-shot CLI command.

Use `help` to see supported syntax and commands. Blank lines are ignored.
Invalid expressions and failed saves print `Error:` and keep the prompt open so
you can try again. Type `exit` or `quit`, press **Ctrl+C**, or end input to
leave with status 0. On Windows, **Ctrl+Z** followed by **Enter** ends input.
Redirected input is read one line at a time until it ends; use the one-shot
`calculate` command when a script needs a nonzero status for a failed
calculation.

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/cli/repl.py [run_repl, _read_expressions] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/cli/commands.py [show_history] -->

### Use Menu Commands

Menu commands have no keyboard shortcuts. A dash means the platform does not
have the command.

| What it does | Windows graphical window | iOS | Android |
| --- | --- | --- | --- |
| Save history to a CSV file | **File** > **Export History...** | **History** > **Export CSV** | **⋮** > **Export History** |
| Remove all saved history after confirmation | **File** > **Clear History**, or right-click the tape | **History** > **Clear History** | **⋮** > **Clear History** |
| Open the settings | **Edit** > **Settings...** | **More** > **Settings** | **⋮** > **Settings** |
| Show the version | **Help** > **About** | **More** > **Settings** > **About**, which also shows short tips | **⋮** > **About**, which also shows short tips |
| List keyboard keys | **Help** > **Keyboard Shortcuts** | — | — |
| Send a bug report or feature request | **Help** > **Send Feedback...** | **More** > **Send Feedback** | **⋮** > **Send Feedback** |
| Open the privacy policy | — | **More** > **Privacy Policy** | **⋮** > **Privacy Policy** |
| Place a tape result in the expression | Click the line | Tap the line, or touch and hold it and choose **Use Result** | Tap the line |
| Copy a full-precision tape result | — | Touch and hold the line and choose **Copy Result** | — |
| Close the program | **File** > **Exit** | — | — |

**Send Feedback** asks how you want to send a bug report or feature request.
**Email** opens your email app with a message to
`support@plaintxtoffice.com`, or shows the address if no email app is
available. The subject is `Plain Text Fin Calc feedback (Android)` or
`Plain Text Fin Calc feedback (iOS)`. The message ends with the app version,
iOS or Android version, and device model, which you can delete before sending.
**Contact form** opens `https://plaintxtoffice.com/contact/` in a browser, or
shows the address if no browser is available.
On Windows, **Help** > **Send Feedback...** opens a dialog with **Report a
Bug**, **Request a Feature**, and **Open Contact Form**. **Report a Bug** and
**Request a Feature** open your email app with a message to
`support@plaintxtoffice.com`. The subject is
`Plain Text Fin Calc bug report (Windows)` or
`Plain Text Fin Calc feature request (Windows)`. The message ends with the app
version, Windows version and build, processor type, and Qt version, which you
can delete before sending. **Open Contact Form** opens
`https://plaintxtoffice.com/contact/` in your browser. If no email app or
browser opens, the dialog stays open and suggests the other option. Nothing is
sent unless you send it.
**Privacy Policy** opens `https://plaintxtoffice.com/privacy-policy/` in a
browser, or shows the address if no browser is available. On Windows, press
**Alt+F**, **Alt+E**, or **Alt+H** to open the **File**, **Edit**, or **Help**
menu.

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/menus/menu_bar.py [build_menu_bar] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/views/tape.py [TapeView.contextMenuEvent, TapeView._on_item_clicked] -->
<!-- Verified from: platform/ios/FinCalc/UI/Views/RootView.swift [RootView.toolbarContent] -->
<!-- Verified from: platform/ios/FinCalc/UI/Views/SettingsView.swift [SettingsView.body] -->
<!-- Verified from: platform/ios/FinCalc/UI/Views/TapeView.swift [TapeView.row] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/feedback.py [FeedbackDialog, feedback_subject, system_summary] -->
<!-- Verified from: platform/ios/FinCalc/UI/Links.swift [Feedback.subject, Feedback.details] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/MainActivity.kt [showMenu] -->

### Use Keyboard Shortcuts

The Windows graphical window and iOS with a hardware keyboard share these
keys:

| Key | What it does |
| --- | --- |
| **0**–**9**, **.**, **+**, **-**, **\***, **/**, **^**, **(**, **)** | Enters that key. |
| **L** | Enters `log`. |
| **Enter** or **Return** (Windows), **Return** (iOS) | Evaluates the expression. |
| **Esc** | Clears the expression. |
| **Backspace** (Windows), **Delete** (iOS) | Deletes the last character. |

In the Windows terminal interface, **Enter** calculates and saves the entry,
**Esc** clears the entry field, and **Ctrl+Q** quits. The **±** key has no
keyboard shortcut. Plain Text Fin Calc for Android has no keyboard shortcuts.

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/views/root_window.py [RootWindow.keyPressEvent] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/views/keypad.py [KEY_MAP] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/dialogs/help_dialogs.py [SHORTCUTS_TEXT] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/tui/app.py [CalculatorApp.BINDINGS, CalculatorApp.on_input_submitted] -->
<!-- Verified from: platform/ios/FinCalc/UI/Views/RootView.swift [RootView.pressHardwareKey] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/MainActivity.kt -->

## Your Data Files

Plain Text Fin Calc saves your history and settings automatically. Each platform
keeps its own files, and the location cannot be changed.

### Find Your Data Files

| Platform | Where history and settings are saved | Edit by hand |
| --- | --- | --- |
| Windows | `data/history.json` and `data/settings.json` in the data folder below | Yes; see [Edit the Windows Data Files](#edit-the-windows-data-files) |
| iOS | `history.json` and `settings.json` in a `FinCalc` folder in the app's private storage, not shown in the Files app | No |
| Android | One private file, `calculator.json` | No |

On iOS and Android, use [Export History to CSV](#export-history-to-csv) to keep
a copy of your history. On Android, uninstalling the app or clearing its data
removes your history and settings, and Android backup and device transfer are
turned off for this app.

<!-- Verified from: platform/ios/FinCalc/Config/PathHandler.swift [PathHandler] -->
<!-- Verified from: platform/ios/FinCalc.xcodeproj/project.pbxproj -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/application/CalculatorModel.kt [CalculatorModel.init] -->
<!-- Verified from: platform/android/app/src/main/AndroidManifest.xml [android:allowBackup] -->
<!-- Verified from: platform/android/app/src/main/res/xml/data_extraction_rules.xml -->

#### Data Files on Windows

| File or folder | Purpose |
| --- | --- |
| `data/history.json` | Saved history. |
| `data/settings.json` | Saved settings. |
| `exports/` | Suggested folder for CSV and plain text exports. |
| `logs/` | Log files for troubleshooting. |

These are inside a data folder that depends on how you run Plain Text Fin Calc:

| How you run Plain Text Fin Calc | Data folder |
| --- | --- |
| From the project folder | `platform/windows/` |
| Packaged program | `%LOCALAPPDATA%/fin-calc/` |
| Packaged program set up as portable | `fin-calc-data/` next to the program, or `%LOCALAPPDATA%/fin-calc/` if that folder cannot be written |

Builds before 2026-10-28 used `Fin Calc/` and `Fin Calc-data/`. The program
renames an old folder to the new name on first launch when the new folder does
not exist yet.

The graphical window, terminal interface, and command line share the same
files.

<!-- Verified from: platform/windows/plain_text_fin_calc/config/path_handler.py [ROOT_DIR, DATA_DIR, HISTORY_FILE, SETTINGS_FILE, EXPORTS_DIR, LOGS_DIR, USER_DATA_DIR] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/config/storage.py [select_storage] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/application/session.py [load_session] -->

### Edit the Windows Data Files

You can edit the Windows data files in a text editor. Close every Plain Text Fin
Calc window first, because Plain Text Fin Calc rewrites the files as you use it,
and keep a copy in case of a mistake. If a file cannot be read, Plain Text Fin
Calc starts with empty history or default settings and overwrites the file at
the next save.

<!-- Verified from: platform/windows/plain_text_fin_calc/adapters/history_store.py [load_history, write_history] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/adapters/settings_store.py [load_settings, write_settings] -->

`settings.json` is a JSON object:

```json
{
  "decimal_places": null,
  "theme": "dark",
  "max_history_entries": 1000,
  "text_tape": {
    "date_headings": true,
    "entry_times": true,
    "time_zone": "local",
    "date_format": "YYYY-MM-DD",
    "twelve_hour": false,
    "seconds": false,
    "utc_offset": false
  }
}
```

| Field | Required | What to enter |
| --- | --- | --- |
| `decimal_places` | No | `null` for full precision, or a whole number from 0 to 6. Larger numbers are treated as 6; other values mean full precision. |
| `theme` | No | `"dark"` or `"light"`. Other values mean dark. |
| `max_history_entries` | No | `null` for unlimited, or a whole number from 1 to 10,000. Larger numbers are treated as 10,000; a missing or other value means 1,000. |
| `text_tape` | No | The example shows the defaults. Use `local`, `UTC`, or a named time zone. Supported date formats are `YYYY-MM-DD`, `MM/DD/YYYY`, and `DD/MM/YYYY`. Each missing or invalid option uses its own default. |

<!-- Verified from: platform/windows/plain_text_fin_calc/adapters/settings_store.py [load_settings, _read_optional_bounded_int, _read_history_cap, _read_theme] -->

`history.json` is a JSON list with one object per calculation, oldest first:

```json
[
  {
    "expression": "0.1 + 0.2",
    "result": "0.3",
    "timestamp": "2026-10-25T14:03:07.512345+00:00"
  }
]
```

| Field | Required | What to enter |
| --- | --- | --- |
| `expression` | Yes | The expression text shown on the tape. |
| `result` | Yes | The result as text. |
| `timestamp` | Yes | An ISO 8601 date and time. |

If any entry is missing a field or has an unreadable timestamp, Plain Text Fin
Calc ignores the whole file and starts with empty history.

<!-- Verified from: platform/windows/plain_text_fin_calc/adapters/history_store.py [_load_entries, write_history] -->

### Find Windows Log Files

Plain Text Fin Calc for Windows writes a log to the `logs/` folder in its data
folder. The log file is named after the data folder, such as `windows.log` when
running from the project folder. Each log file is limited to about 1 MB, and up
to three older copies are kept. The iOS and Android apps do not create log files
you can open.

<!-- Verified from: platform/windows/plain_text_fin_calc/config/logging/log_config.py [configure_logging, MAX_LOG_BYTES, LOG_BACKUP_COUNT] -->
<!-- Verified from: platform/ios/FinCalc/Adapters/HistoryStore.swift [HistoryStore.logger] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/application/CalculatorModel.kt [CalculatorModel] -->

## Troubleshooting

| Symptom | Likely Cause | Resolution |
| --- | --- | --- |
| Windows prints `Choose --gui, --tui, --cli, or a command; use --help for usage.` | Input does not come from the keyboard, so the interface menu cannot be shown. | Add `--gui`, `--tui`, `--cli`, or a command. |
| Windows prints `Use only one of --gui, --tui, or --cli.` | More than one interface option was given. | Give only one. |
| Windows prints `GUI/TUI launch flags cannot be combined with CLI commands.` | `--gui` or `--tui` was used with `calculate` or `history`. | Remove the option, or use `--cli`. |
| Windows prints `Unable to start calculator:` | The data folder cannot be created or written. | Make sure the data folder in [Data Files on Windows](#data-files-on-windows) is writable. |
| An expression starting with `-` is treated as an option on the Windows command line | The minus sign looks like an option. | Put `--` before the expression, as in `calculate -- "-2 ^ 2"`. |
| `Invalid input at character` appears | A typed expression contains an unsupported character, such as `x` or `,`. | Use only numbers, `+`, `-`, `*`, `/`, `^`, parentheses, and `log`. |
| `Invalid input:` and a key appear | The key does not fit at that point in the expression. | See [Enter and Evaluate an Expression](#enter-and-evaluate-an-expression). |
| `Result out of range` appears | The result is too large or too small for the platform. | See [Understand Precision and Limits](#understand-precision-and-limits). |
| Saved history is empty after starting | The history file could not be read. | On Windows, check `data/history.json` against [Edit the Windows Data Files](#edit-the-windows-data-files) before your next calculation overwrites it. |
| Settings returned to their defaults | The settings file was missing or had invalid values. | Choose your settings again. |
| Android shows `Could not load saved history and settings. Defaults are in use.` | The saved file could not be read. | Choose your settings again. Saved history could not be recovered by the app. |
| Android shows `Could not save. Your previous history is unchanged.` | The device could not save the change. | Free up storage and try again. |
| Android shows `Could not export history. Choose another location and try again.` | The chosen location cannot be written. | Choose another folder or storage provider. |
| iOS shows `History could not be saved` or `Settings could not be saved` | The device could not save the change. | Free up storage and try again. |
| Windows status bar shows `Export failed:` | The chosen location cannot be written. | Choose a writable folder. |
| Windows status bar shows `Saving history failed:` | The history file could not be written. | Free up storage or check that the data folder is writable, then make another calculation. |
| iOS **Export CSV** or **Clear History** is unavailable | The tape is empty. | Make a calculation first. |
| The Android **⋮** menu does not open | Saved data is still loading. | Wait until `Loading…` disappears. |
| Older calculations disappeared | The history limit was reached or lowered. | Raise the maximum history entries or choose **Unlimited**. |

<!-- Verified from: platform/windows/plain_text_fin_calc/ui/cli/launch.py [choose_interface] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/cli/app.py [select_interface] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/cli/commands.py [calculate] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/domains/calc/parsing.py [parse_expression] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/adapters/history_store.py [load_history] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/adapters/settings_store.py [load_settings] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/views/root_window.py [RootWindow._on_export_history] -->
<!-- Verified from: platform/ios/FinCalc/Application/CalculatorSession.swift [writeHistory, applySettings] -->
<!-- Verified from: platform/ios/FinCalc/UI/Views/RootView.swift [RootView.toolbarContent] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/application/CalculatorModel.kt [CalculatorModel.init, submit] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/application/CalculatorSession.kt [calculate] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/domains/calc/Formatting.kt [formatResult] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/MainActivity.kt [showMenu] -->

## FAQ

### Why does 0.1 + 0.2 give exactly 0.3?

Plain Text Fin Calc calculates with decimal numbers rather than binary floating
point, so decimal fractions are exact.

<!-- Verified from: platform/windows/plain_text_fin_calc/domains/calc/evaluator.py [evaluate] -->
<!-- Verified from: platform/android/app/src/test/resources/python-reference.json -->

### Why does -2 ^ 2 give 4?

A leading minus sign belongs to its number, so `-2 ^ 2` means `(-2) ^ 2`. To
get `-4`, enter `0 - 2 ^ 2`.

<!-- Verified from: platform/windows/plain_text_fin_calc/domains/calc/evaluator.py [module docstring] -->

### Does the Decimal places setting change my saved results?

No. It only rounds what you see. Saved, reused, copied, and exported results
keep their full precision.

<!-- Verified from: platform/windows/plain_text_fin_calc/domains/calc/formatting.py [format_result] -->
<!-- Verified from: platform/ios/FinCalc/UI/Views/TapeView.swift [TapeView.row] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/domains/calc/Formatting.kt [formatResult] -->

### Is my history shared between devices or platforms?

No. Each device keeps its own history and settings. Export a CSV file to move
a record of your calculations elsewhere.

<!-- Verified from: platform/windows/plain_text_fin_calc/config/path_handler.py [HISTORY_FILE] -->
<!-- Verified from: platform/ios/FinCalc/Config/PathHandler.swift [PathHandler] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/application/CalculatorModel.kt [CalculatorModel.init] -->

### Can I undo Clear History?

No. Export your history first if you might need it.

<!-- Verified from: platform/windows/plain_text_fin_calc/domains/calc/history.py [History.clear_all] -->

### Can I change settings from the Windows terminal interface or command line?

From the `fin-calc>` prompt, yes: use `config`, as described in
[Use the Persistent Prompt](#use-the-persistent-prompt). The terminal
interface and one-shot commands cannot change settings; use **Edit** >
**Settings...** in the graphical window, or edit `settings.json` while Fin
Calc is closed. The terminal interface and command line use the new settings
the next time they start.

<!-- Verified from: platform/windows/plain_text_fin_calc/application/session.py [load_session] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/cli/repl.py [run_repl] -->

### Why does the same logarithm differ in its last digit on another platform?

Each platform computes logarithms and fractional powers its own way, so the
28th digit can differ.

<!-- Verified from: platform/ios/FinCalc/Domains/Calc/DecimalMath.swift [DecimalMath] -->
<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/domains/calc/DecimalMath.kt [ln, exp] -->

## Feedback

Send bug reports and feature requests to
[support@plaintxtoffice.com](mailto:support@plaintxtoffice.com) or through the
[contact page](https://plaintxtoffice.com/contact/). Each app also has a
**Send Feedback** screen that prepares an email or opens the contact page:

| Platform | How to open feedback |
| --- | --- |
| Android (in Google Play review) | Choose **⋮** > **Send Feedback**. |
| iOS (in App Store review) | Choose **More** > **Send Feedback**. |
| Windows (in development) | In the graphical window, choose **Help** > **Send Feedback...**. The terminal interface and command line have no feedback screen. |

See [Use Menu Commands](#use-menu-commands) for what the prepared email
contains.

<!-- Verified from: platform/android/app/src/main/java/com/plaintxtoffice/fincalc/ui/Links.kt [FEEDBACK_EMAIL, CONTACT_URL] -->
<!-- Verified from: platform/ios/FinCalc/UI/Links.swift [Links.feedbackEmail, Links.contact] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/gui/feedback.py [FEEDBACK_ADDRESS, CONTACT_URL] -->

## Glossary

- **CSV**: comma-separated values, a text file format that spreadsheet
  programs can open.
- **Decimal places**: the number of digits shown after the decimal point.
- **Expression**: the calculation you are entering, such as `2 + 3`.
- **Full precision**: showing a result with all of its calculated digits.
- **Graphical window**: the Windows interface with menus, a tape, and a
  clickable keypad.
- **History entry**: one saved calculation, with its expression, result, and
  time.
- **History limit**: the maximum number of calculations Plain Text Fin Calc
  keeps.
- **Rounding half to even**: rounding a value exactly halfway between two
  choices to the one with an even last digit.
- **Scientific notation**: writing a number as digits and a power of ten,
  such as `1E+3` for 1,000 or `1E-7` for 0.0000001.
- **Significant digits**: the digits of a number from its first nonzero
  digit.
- **Tape**: the list of saved calculations.
- **Terminal interface**: the Windows interface that runs inside a terminal
  window.

<!-- Verified from: platform/windows/plain_text_fin_calc/domains/calc/history.py [HistoryEntry] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/domains/calc/formatting.py [format_result] -->
<!-- Verified from: platform/windows/plain_text_fin_calc/ui/tui/app.py [CalculatorApp] -->
