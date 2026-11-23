"""Edit the saved plain text tape layout in Windows Settings."""

from __future__ import annotations

from typing import TYPE_CHECKING
from zoneinfo import available_timezones

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
)

from plain_text_fin_calc.domains.calc.text_tape import (
    DATE_PATTERNS,
    TextTapeFormat,
    format_text_tape,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from plain_text_fin_calc.domains.calc.history import HistoryEntry

_PREVIEW_ENTRIES = 5


class TextExportSettings(QGroupBox):
    """Preview the first few calculations using the selected tape format."""

    def __init__(
        self,
        options: TextTapeFormat,
        entries: Sequence[HistoryEntry],
    ) -> None:
        """Build the preview from the same entries and formatter as the file."""
        super().__init__("Plain text export (.txt)")
        self._entries = entries[:_PREVIEW_ENTRIES]
        self._dates = QCheckBox("Group by date")
        self._dates.setChecked(options.date_headings)
        self._times = QCheckBox("Show time for each calculation")
        self._times.setChecked(options.entry_times)
        self._preview = QPlainTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setAccessibleName("Tape preview")
        self._preview.setPlaceholderText("History is empty.")
        layout = QVBoxLayout(self)
        layout.addWidget(self._dates)
        layout.addWidget(self._times)
        layout.addLayout(self._time_controls(options))
        self._dates.toggled.connect(self._update_preview)
        self._times.toggled.connect(self._update_preview)
        label = "Preview"
        if len(entries) > _PREVIEW_ENTRIES:
            label = f"Preview (first {_PREVIEW_ENTRIES} calculations)"
        layout.addWidget(QLabel(label))
        layout.addWidget(self._preview)
        self._update_preview()

    def _time_controls(self, options: TextTapeFormat) -> QFormLayout:
        self._zone = QComboBox()
        self._zone.addItem("Computer local time", "local")
        self._zone.addItem("UTC", "UTC")
        for name in sorted(available_timezones() - {"UTC"}):
            self._zone.addItem(name, name)
        self._zone.setCurrentIndex(self._zone.findData(options.time_zone))
        self._date_format = QComboBox()
        self._date_format.addItems(list(DATE_PATTERNS))
        self._date_format.setCurrentText(options.date_format)
        self._clock = QComboBox()
        self._clock.addItem("24-hour", userData=False)
        self._clock.addItem("12-hour (AM/PM)", userData=True)
        self._clock.setCurrentIndex(self._clock.findData(options.twelve_hour))
        self._seconds = QCheckBox("Include seconds")
        self._seconds.setChecked(options.seconds)
        self._offset = QCheckBox("Include UTC offset")
        self._offset.setChecked(options.utc_offset)
        form = QFormLayout()
        form.addRow("Time zone", self._zone)
        form.addRow("Date format", self._date_format)
        form.addRow("Time format", self._clock)
        form.addRow("", self._seconds)
        form.addRow("", self._offset)
        for combo in (self._zone, self._date_format, self._clock):
            combo.currentIndexChanged.connect(self._update_preview)
        for checkbox in (self._seconds, self._offset):
            checkbox.toggled.connect(self._update_preview)
        return form

    def selected_format(self) -> TextTapeFormat:
        """Return the layout selected for subsequent exports."""
        return TextTapeFormat(
            date_headings=self._dates.isChecked(),
            entry_times=self._times.isChecked(),
            time_zone=self._zone.currentData(),
            date_format=self._date_format.currentText(),
            twelve_hour=self._clock.currentData(),
            seconds=self._seconds.isChecked(),
            utc_offset=self._offset.isChecked(),
        )

    def _update_preview(self) -> None:
        options = self.selected_format()
        self._zone.setEnabled(options.date_headings or options.entry_times)
        self._date_format.setEnabled(options.date_headings)
        for control in (self._clock, self._seconds, self._offset):
            control.setEnabled(options.entry_times)
        self._preview.setPlainText(
            format_text_tape(self._entries, options),
        )
