"""Expression display, RPN Y register line, and status line widget."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from plain_text_fin_calc.ui.gui.views.theme import get_theme

if TYPE_CHECKING:
    from plain_text_fin_calc.ui.gui.views.theme import ThemeColors


class DisplayView(QWidget):
    """Shows the current expression and a status/error line.

    In RPN mode the expression line is the X register and a smaller Y
    register line is shown above it; the Y line is hidden in algebraic mode.

    Parameters
    ----------
    parent : QWidget | None
        Parent widget.

    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the display view widget."""
        super().__init__(parent)
        self._rpn_mode = False

        self._y_label = QLabel("Y:")
        self._y_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        self._y_label.setVisible(False)

        self._expression_label = QLabel("")
        self._expression_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        self._expression_label.setMinimumHeight(40)

        self._status_label = QLabel("")
        self._status_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )

        self.restyle(get_theme("dark"))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._y_label)
        layout.addWidget(self._expression_label)
        layout.addWidget(self._status_label)

    def set_rpn_mode(self, enabled: bool) -> None:  # noqa: FBT001
        """Show or hide the Y register line and name the registers.

        Leaving RPN mode clears the Y line and the accessible names, so the
        algebraic layout is as it was.
        """
        self._rpn_mode = enabled
        self._y_label.setVisible(enabled)
        self.set_y(None)
        self._name_x_register()

    def set_expression(self, text: str) -> None:
        """Update the expression display text (the X register in RPN mode)."""
        self._expression_label.setText(text)
        self._name_x_register()

    def set_y(self, value: str | None) -> None:
        """Update the Y register line with a display value, or none.

        The line reads ``Y: <value>``, or ``Y:`` alone when the register is
        empty.
        """
        self._y_label.setText("Y:" if value is None else f"Y: {value}")
        self._y_label.setAccessibleName(
            f"Y register, {'empty' if value is None else value}"
            if self._rpn_mode
            else "",
        )

    def set_status(self, text: str) -> None:
        """Update the status/error display text."""
        self._status_label.setText(text)

    def clear_status(self) -> None:
        """Clear the status line."""
        self._status_label.setText("")

    def restyle(self, colors: ThemeColors) -> None:
        """Apply theme colors to the register and status labels."""
        self._y_label.setStyleSheet(
            "font-size: 14px; padding: 2px 4px;"
            f" background: {colors.display_bg};"
            f" color: {colors.placeholder_text};",
        )
        self._expression_label.setStyleSheet(
            "font-size: 24px; padding: 4px;"
            f" background: {colors.display_bg}; color: {colors.display_fg};",
        )
        self._status_label.setStyleSheet(
            f"font-size: 14px; padding: 2px; color: {colors.error_fg};",
        )

    def _name_x_register(self) -> None:
        """Give the expression line its X register name in RPN mode only."""
        text = self._expression_label.text()
        self._expression_label.setAccessibleName(
            f"X register, {text or 'empty'}" if self._rpn_mode else "",
        )
