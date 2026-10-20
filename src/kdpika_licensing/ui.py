"""Optional reusable PyQt6 activation dialog."""

from __future__ import annotations

from typing import Any

from .client import LicenseClient
from .models import LicenseResult


def show_activation_dialog(
    client: LicenseClient, email_required: bool = False, parent: Any = None
) -> LicenseResult:
    """Show the optional blocking PyQt6 activation dialog on the GUI thread.

    Args:
        client: Persistent configured LicenseClient; use Sandbox for development.
        email_required: Require a nonempty email field in the dialog. Actual
            email/key matching is enforced by the server's product policy.
        parent: Optional Qt parent widget; no PyQt import is needed until use.

    Returns:
        Verified activation result, refusal or local ACTIVATION_CANCELLED result.
        Callers must require valid and signature_valid before protected work.

    Raises:
        RuntimeError: The qt optional dependency is not installed.

    Examples:
        Run the tested examples/pyqt_activation.py script in a desktop session.
        Network work blocks the dialog; this is not an asynchronous GUI framework.
    """
    try:
        from PyQt6.QtWidgets import (
            QApplication,
            QCheckBox,
            QDialog,
            QDialogButtonBox,
            QFormLayout,
            QLabel,
            QLineEdit,
            QMessageBox,
            QVBoxLayout,
        )
    except ImportError as error:
        raise RuntimeError("Install the SDK with the 'qt' extra to use the activation dialog.") from error

    application = QApplication.instance()
    owns_application = application is None
    if application is None:
        application = QApplication([])

    dialog = QDialog(parent)
    dialog.setWindowTitle("Activate license")
    dialog.setMinimumWidth(440)
    layout = QVBoxLayout(dialog)
    heading = QLabel("Enter your license information")
    heading.setStyleSheet("font-size:18px;font-weight:700")
    layout.addWidget(heading)
    form = QFormLayout()
    key = QLineEdit()
    key.setEchoMode(QLineEdit.EchoMode.Password)
    key.setPlaceholderText("APP-XXXX-XXXX-XXXX-XXXX")
    email = QLineEdit()
    email.setPlaceholderText("customer@example.com")
    reveal = QCheckBox("Show license key")
    reveal.toggled.connect(
        lambda checked: key.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)
    )
    form.addRow("License key", key)
    form.addRow("Customer email", email)
    form.addRow("", reveal)
    layout.addLayout(form)
    status = QLabel("Activation uses a random installation ID. A device name and platform are also sent.")
    status.setWordWrap(True)
    layout.addWidget(status)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
    buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Activate")
    layout.addWidget(buttons)
    result: LicenseResult | None = None

    def activate() -> None:
        nonlocal result
        if not key.text().strip() or (email_required and not email.text().strip()):
            QMessageBox.warning(
                dialog, "Missing information", "Enter the license key and required customer email."
            )
            return
        buttons.setEnabled(False)
        status.setText("Contacting the licensing service…")
        QApplication.processEvents()
        result = client.activate(key.text(), email.text() or None)
        buttons.setEnabled(True)
        if result.valid and result.signature_valid:
            dialog.accept()
        else:
            status.setText(result.message or "Activation failed.")

    buttons.accepted.connect(activate)
    buttons.rejected.connect(dialog.reject)
    dialog.exec()
    final = result or LicenseResult(
        False,
        "local",
        error_code="ACTIVATION_CANCELLED",
        message="Activation was cancelled.",
        storage_security=client.storage_security,
    )
    if owns_application:
        application.quit()
    return final
