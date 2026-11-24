# Plain Text Fin Calc for Windows

This directory is the Python project root. It contains `pyproject.toml`, the
`plain_text_fin_calc/` package, Windows tests, and the local `.venv/`
environment.

See the [product overview](../../README.md) and
[user manual](../../docs/USER_MANUAL.md) for application behavior. Shared
documentation and assets remain at repository level.

## RPN input mode

RPN (reverse Polish notation) is an optional input mode, in development and
not in a released build. **Algebraic** stays the default. It is saved as
`"input_mode": "algebraic"` or `"rpn"` in `data/settings.json`.

- Graphical window: choose **Edit** > **Settings...** and set **Input mode**
  to **RPN (reverse Polish notation)**. The **(**, **)**, and **=** keys
  become **x↔y**, **DROP**, and **ENTER**, and a **Y:** line appears above
  the display. On the keyboard, **Enter** is **ENTER**, **S** swaps, **D**
  drops, **L** is **log**, **Esc** is **C**, and **Backspace** deletes a
  digit.
- Persistent prompt (`--cli`): type `config input_mode rpn` or
  `config input_mode algebraic`. In RPN mode the prompt is `fin-calc rpn>`
  and each line is a list of numbers, operators (`+ - * / ^`), and the words
  `enter`, `swap`, `drop`, `chs`, `log`, and `clear`, separated by spaces,
  such as `3 4 +`. The stack is printed after each line.
- One-shot command: `calculate --rpn "3 4 +"` runs one line on an empty
  stack and prints the last number, whatever the saved input mode.
- Terminal interface (`--tui`): reads the input mode when it starts and takes
  the same lines as the prompt. It cannot change the setting.

The stack holds four levels and is kept in memory only. Each RPN calculation
is saved to history as its equivalent algebraic expression and result, with
the keys in an optional `rpn_input` field. CSV exports carry them in a fourth
`rpn_input` column, empty for algebraic entries, and plain text exports add an
`RPN input:` line under each RPN calculation. The
[user manual](../../docs/USER_MANUAL.md#calculate-in-rpn-mode) has the full
rules and messages.

## Development

Run from this directory with Python 3.14 or newer.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install --upgrade "pip>=25.1"
.venv/Scripts/python.exe -m pip install --editable ".[dev]"
.venv/Scripts/python.exe -m plain_text_fin_calc.main
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m mypy plain_text_fin_calc
```

For Markdown checks, run `platform/windows/.venv/Scripts/rumdl.exe check` from
the repository root; configuration lives in `.rumdl.toml` there.

The local [LICENSE](LICENSE) is a distribution copy of the
[repository license](../../LICENSE). Keep them identical when changing
licensing.

## Build the portable executable

With the project installed in `.venv` and the Microsoft Visual C++ build
tools installed, run these commands from `platform/windows/`.

```powershell
.venv/Scripts/python.exe -m pip install "nuitka==4.2.2" zstandard
./scripts/nuitka/onefile.ps1
```

The script writes `build/onefile/Plain Text Fin Calc.exe`. Copy that file
to run the calculator on another Windows machine. On first use, the app
creates `fin-calc-data/` beside the executable if the folder is writable.

## Feedback

Send bug reports and feature requests to
[feedback@plaintxtoffice.com](mailto:feedback@plaintxtoffice.com) or through the
[contact form](https://plaintxtoffice.com/contact/), or choose **Help** >
**Send Feedback...** in the app.
