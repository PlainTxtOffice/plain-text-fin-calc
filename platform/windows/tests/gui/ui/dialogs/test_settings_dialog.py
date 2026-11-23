"""Tests for the Settings dialog."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from plain_text_fin_calc.config.settings import Settings
from plain_text_fin_calc.ui.gui.dialogs.settings_dialog import SettingsDialog


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_dialog_reflects_current_settings():
    _app()
    dialog = SettingsDialog(
        Settings(decimal_places=2, theme="light", max_history_entries=100),
    )

    assert dialog._precision_combo.currentData() == 2
    assert dialog._theme_combo.currentData() == "light"
    assert not dialog._unlimited_check.isChecked()
    assert dialog._cap_spin.value() == 100


def test_dialog_reflects_defaults():
    _app()
    dialog = SettingsDialog(Settings())

    assert dialog._precision_combo.currentData() is None
    assert dialog._theme_combo.currentData() == "dark"
    assert not dialog._unlimited_check.isChecked()
    assert dialog._cap_spin.value() == 1000


def test_dialog_reflects_unlimited():
    _app()
    dialog = SettingsDialog(Settings(max_history_entries=None))

    assert dialog._unlimited_check.isChecked()
    assert not dialog._cap_spin.isEnabled()


def test_selected_settings_returns_edited_values():
    _app()
    dialog = SettingsDialog(Settings())

    dialog._precision_combo.setCurrentIndex(
        dialog._precision_combo.findData(3),
    )
    dialog._theme_combo.setCurrentIndex(dialog._theme_combo.findData("light"))
    dialog._unlimited_check.setChecked(False)
    dialog._cap_spin.setValue(50)

    selected = dialog.selected_settings()
    assert selected == Settings(
        decimal_places=3,
        theme="light",
        max_history_entries=50,
    )


def test_unlimited_checkbox_toggles_spinbox():
    _app()
    dialog = SettingsDialog(Settings(max_history_entries=10))

    assert dialog._cap_spin.isEnabled()
    dialog._unlimited_check.setChecked(True)
    assert not dialog._cap_spin.isEnabled()
    assert dialog.selected_settings().max_history_entries is None


def test_dialog_preselects_input_mode():
    _app()
    assert SettingsDialog(Settings())._input_mode_combo.currentData() == (
        "algebraic"
    )
    dialog = SettingsDialog(Settings(input_mode="rpn"))
    combo = dialog._input_mode_combo
    assert combo.currentData() == "rpn"
    assert combo.currentText() == "RPN (reverse Polish notation)"
    assert [combo.itemText(i) for i in range(combo.count())] == [
        "Algebraic", "RPN (reverse Polish notation)",
    ]


def test_selected_settings_carries_input_mode_with_other_fields():
    _app()
    dialog = SettingsDialog(Settings(decimal_places=2, input_mode="rpn"))
    assert dialog.selected_settings() == Settings(
        decimal_places=2, input_mode="rpn"
    )
    combo = dialog._input_mode_combo
    combo.setCurrentIndex(combo.findData("algebraic"))
    assert dialog.selected_settings() == Settings(decimal_places=2)
    combo.setCurrentIndex(combo.findData("rpn"))
    assert dialog.selected_settings().input_mode == "rpn"


def test_input_mode_row_and_explanation_text():
    from PySide6.QtWidgets import QFormLayout, QLabel

    _app()
    dialog = SettingsDialog(Settings())
    form = dialog.findChild(QFormLayout)

    def row_label(row: int) -> str:
        # A row added with an empty label has no label widget.
        label = form.itemAt(row, QFormLayout.ItemRole.LabelRole)
        return label.widget().text() if label is not None else ""

    def row_field(row: int):
        return form.itemAt(row, QFormLayout.ItemRole.FieldRole).widget()

    labels = [row_label(row) for row in range(form.rowCount())]
    assert labels[:4] == ["Decimal places:", "Input mode:", "", "Theme:"]
    assert row_field(1) is dialog._input_mode_combo
    assert row_field(2) is dialog._input_mode_note
    assert dialog._input_mode_note.wordWrap()
    assert dialog._input_mode_note.text() == (
        "In RPN mode, numbers go onto a stack with ENTER and each operator "
        "uses the last two numbers. Changing the input mode clears the number "
        "being entered and the stack. History is kept."
    )
    assert dialog._input_mode_note in dialog.findChildren(QLabel)
