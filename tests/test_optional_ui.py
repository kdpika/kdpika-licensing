"""Optional Qt behavior with widget doubles; not a native GUI acceptance test."""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from kdpika_licensing import LicenseResult
from kdpika_licensing.ui import show_activation_dialog


def test_missing_qt_does_not_change_base_install(monkeypatch):
    monkeypatch.setitem(sys.modules, "PyQt6", None)
    with pytest.raises(RuntimeError, match="qt"):
        show_activation_dialog(MagicMock())


@pytest.mark.parametrize("valid,signed", [(True, True), (True, False), (False, True)])
def test_optional_dialog_only_accepts_verified_valid_decision(monkeypatch, valid, signed):
    application = MagicMock()
    app_class = MagicMock()
    app_class.instance.return_value = None
    app_class.return_value = application
    dialog = MagicMock()
    key, email = MagicMock(), MagicMock()
    key.text.return_value = "SYNTHETIC-NOT-A-REAL-KEY"
    email.text.return_value = "tester@example.invalid"
    line_class = MagicMock(side_effect=[key, email])
    line_class.EchoMode = SimpleNamespace(Password=1, Normal=0)
    button = MagicMock()
    button_class = MagicMock(return_value=button)
    button_class.StandardButton = SimpleNamespace(Cancel=1, Ok=2)
    callbacks = []
    button.accepted.connect.side_effect = callbacks.append
    dialog.exec.side_effect = lambda: callbacks[0]()
    module = SimpleNamespace(
        QApplication=app_class,
        QDialog=MagicMock(return_value=dialog),
        QLineEdit=line_class,
        QDialogButtonBox=button_class,
        QCheckBox=MagicMock(),
        QFormLayout=MagicMock(),
        QLabel=MagicMock(),
        QMessageBox=MagicMock(),
        QVBoxLayout=MagicMock(),
    )
    monkeypatch.setitem(sys.modules, "PyQt6", SimpleNamespace())
    monkeypatch.setitem(sys.modules, "PyQt6.QtWidgets", module)
    client = MagicMock()
    client.storage_security = "permission-protected-file"
    client.activate.return_value = LicenseResult(valid, "online", signature_valid=signed)
    result = show_activation_dialog(client, email_required=True)
    assert result.valid is valid
    assert dialog.accept.call_count == int(valid and signed)
    assert application.quit.call_count == 1
