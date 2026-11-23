"""Tests for the feedback email draft, dialog, and Help menu entry."""

from __future__ import annotations

import os
from urllib.parse import parse_qs, urlsplit

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton

from plain_text_fin_calc.ui.gui import feedback
from plain_text_fin_calc.ui.gui.menus.menu_bar import MenuBarCallbacks, build_menu_bar


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def opened(monkeypatch) -> list[str]:
    urls: list[str] = []

    def open_url(url) -> bool:
        urls.append(url.toString())
        return True

    monkeypatch.setattr(QDesktopServices, "openUrl", open_url)
    return urls


def test_mailto_carries_subject_and_summary_only() -> None:
    """The draft holds a subject and the system summary, nothing else."""
    summary = feedback.format_system_summary(
        app_name="Fin Calc",
        version="0.1.0",
        windows_release="11",
        windows_build="10.0.26300",
        runtime="AMD64, Qt 6.11.0",
    )

    url = feedback.feedback_mailto(
        "Fin Calc", feedback.FeedbackKind.BUG_REPORT, summary
    )

    parts = urlsplit(url)
    query = parse_qs(parts.query)
    assert parts.scheme == "mailto"
    assert parts.path == feedback.FEEDBACK_ADDRESS
    assert query["subject"] == ["Fin Calc bug report (Windows)"]
    assert query["body"] == [
        "\r\n\r\nFin Calc 0.1.0\r\nWindows 11 (10.0.26300)\r\nAMD64, Qt 6.11.0"
    ]
    assert set(query) == {"subject", "body"}


def test_mailto_names_feature_requests_and_encodes_reserved_characters() -> None:
    url = feedback.feedback_mailto(
        "A&B ?=#", feedback.FeedbackKind.FEATURE_REQUEST, "x"
    )

    query = parse_qs(urlsplit(url).query)
    assert query["subject"] == ["A&B ?=# feature request (Windows)"]
    assert query["body"] == ["\r\n\r\nx"]


def test_version_comes_from_installed_metadata() -> None:
    assert feedback.app_version("fin-calc") == "0.1.0"
    assert feedback.app_version("no-such-distribution") == "unknown"


def test_bug_button_drafts_email_and_closes(opened) -> None:
    _app()
    dialog = feedback.FeedbackDialog("Fin Calc", "fin-calc")

    dialog.findChild(QPushButton, "feedbackReportBugButton").click()

    assert len(opened) == 1
    query = parse_qs(urlsplit(opened[0]).query)
    assert query["subject"] == ["Fin Calc bug report (Windows)"]
    assert query["body"][0].startswith("\r\n\r\nFin Calc 0.1.0\r\nWindows ")
    assert dialog.result() == feedback.FeedbackDialog.DialogCode.Accepted


def test_contact_button_opens_contact_form(opened) -> None:
    _app()
    dialog = feedback.FeedbackDialog("Fin Calc", "fin-calc")

    dialog.findChild(QPushButton, "feedbackContactFormButton").click()

    assert opened == [feedback.CONTACT_URL]
    assert dialog.result() == feedback.FeedbackDialog.DialogCode.Accepted


def test_missing_email_app_shows_alternative(monkeypatch) -> None:
    """Without an email app the dialog stays open and offers the form."""
    _app()
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: False)
    dialog = feedback.FeedbackDialog("Fin Calc", "fin-calc")

    dialog.findChild(QPushButton, "feedbackRequestFeatureButton").click()

    assert not dialog.error_label.isHidden()
    assert "Open Contact Form" in dialog.error_label.text()
    assert dialog.result() == feedback.FeedbackDialog.DialogCode.Rejected


def test_failed_contact_form_suggests_email(monkeypatch) -> None:
    """When the browser fails the dialog stays open and offers email."""
    _app()
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: False)
    dialog = feedback.FeedbackDialog("Fin Calc", "fin-calc")

    dialog.findChild(QPushButton, "feedbackContactFormButton").click()

    assert not dialog.error_label.isHidden()
    assert "Report a Bug" in dialog.error_label.text()
    assert dialog.result() == feedback.FeedbackDialog.DialogCode.Rejected


def test_help_menu_offers_feedback_before_about(monkeypatch) -> None:
    _app()
    shown: list[tuple[object, ...]] = []
    monkeypatch.setattr(
        feedback, "show_feedback_dialog", lambda *args: shown.append(args)
    )
    window = QMainWindow()
    parts = build_menu_bar(
        window,
        MenuBarCallbacks(
            export_history=lambda: None,
            clear_history=lambda: None,
            open_settings=lambda: None,
            show_about=lambda: None,
            show_shortcuts=lambda: None,
        ),
    )

    labels = [
        "-" if action.isSeparator() else action.text()
        for action in parts.help_menu.actions()
    ]
    assert labels == [
        "Keyboard Shortcuts",
        "Send &Feedback...",
        "-",
        "About",
    ]

    parts.feedback_action.trigger()

    assert shown == [(window, "Plain Text Fin Calc", "fin-calc")]
