# Plain Text Fin Calc for Windows

This directory is the Python project root. It contains `pyproject.toml`, the
`plain_text_fin_calc/` package, Windows tests, and the local `.venv/`
environment.

See the [product overview](../../README.md) and
[user manual](../../docs/USER_MANUAL.md) for application behavior. Shared
documentation and assets remain at repository level.

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
[support@plaintxtoffice.com](mailto:support@plaintxtoffice.com) or through the
[contact form](https://plaintxtoffice.com/contact/), or choose **Help** >
**Send Feedback...** in the app.
