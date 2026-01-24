"""
AgTools Common UI Widgets

Reusable UI components for loading states, validation, and feedback.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QProgressBar, QDialog,
    QLineEdit, QSpinBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.styles import COLORS


class LoadingOverlay(QWidget):
    """
    Semi-transparent overlay with loading indicator.

    Usage:
        overlay = LoadingOverlay(parent_widget)
        overlay.show_loading("Processing...")
        # ... do work ...
        overlay.hide_loading()
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.hide()

    def _setup_ui(self) -> None:
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.85);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Container for loading content
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 24px;
            }}
        """)
        container.setFixedSize(250, 120)

        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Spinner (using progress bar as fallback)
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # Indeterminate
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(6)
        self._progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: {COLORS['border']};
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['primary']};
                border-radius: 3px;
            }}
        """)
        container_layout.addWidget(self._progress)

        # Message
        self._message = QLabel("Loading...")
        self._message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._message.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-top: 12px;")
        container_layout.addWidget(self._message)

        layout.addWidget(container)

    def show_loading(self, message: str = "Loading...") -> None:
        """Show the loading overlay with a message."""
        self._message.setText(message)
        self.resize(self.parent().size())
        self.raise_()
        self.show()
        QApplication.processEvents()

    def hide_loading(self) -> None:
        """Hide the loading overlay."""
        self.hide()

    def resizeEvent(self, event) -> None:
        """Keep overlay sized to parent."""
        if self.parent():
            self.resize(self.parent().size())
        super().resizeEvent(event)


class LoadingButton(QPushButton):
    """
    Button that shows loading state when clicked.

    Usage:
        btn = LoadingButton("Submit")
        btn.start_loading()
        # ... do work ...
        btn.stop_loading()
    """

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._original_text = text
        self._is_loading = False

    def start_loading(self, text: str = None) -> None:
        """Start loading state."""
        self._is_loading = True
        self.setEnabled(False)
        self.setText(text or "Loading...")
        QApplication.processEvents()

    def stop_loading(self) -> None:
        """Stop loading state."""
        self._is_loading = False
        self.setEnabled(True)
        self.setText(self._original_text)

    @property
    def is_loading(self) -> bool:
        return self._is_loading


class StatusMessage(QFrame):
    """
    Inline status message widget for showing success/error/info feedback.

    Usage:
        msg = StatusMessage()
        parent_layout.addWidget(msg)
        msg.show_success("Data saved!")
        msg.show_error("Failed to save")
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer()
        self._timer.timeout.connect(self.hide_message)
        self._setup_ui()
        self.hide()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        self._icon = QLabel()
        layout.addWidget(self._icon)

        self._text = QLabel()
        self._text.setWordWrap(True)
        layout.addWidget(self._text, 1)

        self._close_btn = QPushButton("×")
        self._close_btn.setFixedSize(20, 20)
        self._close_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                font-size: 16pt;
                padding: 0;
            }
            QPushButton:hover {
                background-color: rgba(0,0,0,0.1);
                border-radius: 10px;
            }
        """)
        self._close_btn.clicked.connect(self.hide_message)
        layout.addWidget(self._close_btn)

        self.setStyleSheet("""
            QFrame {
                border-radius: 6px;
                margin: 4px 0;
            }
        """)

    def show_success(self, message: str, auto_hide: int = 5000) -> None:
        """Show success message."""
        self._show_message(message, "success", auto_hide)

    def show_error(self, message: str, auto_hide: int = 0) -> None:
        """Show error message (doesn't auto-hide by default)."""
        self._show_message(message, "error", auto_hide)

    def show_warning(self, message: str, auto_hide: int = 5000) -> None:
        """Show warning message."""
        self._show_message(message, "warning", auto_hide)

    def show_info(self, message: str, auto_hide: int = 5000) -> None:
        """Show info message."""
        self._show_message(message, "info", auto_hide)

    def _show_message(self, message: str, msg_type: str, auto_hide: int) -> None:
        """Internal method to show a message."""
        self._timer.stop()

        icons = {
            "success": "✓",
            "error": "✕",
            "warning": "⚠",
            "info": "ℹ"
        }
        colors = {
            "success": (COLORS['success'], COLORS['success_light']),
            "error": (COLORS['error'], COLORS['error_light']),
            "warning": (COLORS['warning'], COLORS['warning_light']),
            "info": (COLORS['info'], COLORS['info_light'])
        }

        fg, bg = colors.get(msg_type, colors['info'])

        self._icon.setText(icons.get(msg_type, "ℹ"))
        self._icon.setStyleSheet(f"color: {fg}; font-size: 14pt;")
        self._text.setText(message)
        self._text.setStyleSheet(f"color: {COLORS['text_primary']};")

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {fg};
                border-radius: 6px;
                margin: 4px 0;
            }}
        """)

        self.show()

        if auto_hide > 0:
            self._timer.start(auto_hide)

    def hide_message(self) -> None:
        """Hide the message."""
        self._timer.stop()
        self.hide()


class ValidatedLineEdit(QLineEdit):
    """
    Line edit with built-in validation feedback.

    Usage:
        edit = ValidatedLineEdit()
        edit.set_validator(lambda x: len(x) >= 3, "Must be at least 3 characters")
        if edit.is_valid():
            value = edit.text()
    """

    validation_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._validator_func = None
        self._error_message = ""
        self._is_valid = True
        self._error_label = None

        self.textChanged.connect(self._validate)

    def set_validator(self, validator_func, error_message: str = "Invalid input") -> None:
        """
        Set a validation function.

        Args:
            validator_func: Function that takes text and returns bool
            error_message: Message to show when validation fails
        """
        self._validator_func = validator_func
        self._error_message = error_message
        self._validate()

    def set_error_label(self, label: QLabel) -> None:
        """Set an external label to show error messages."""
        self._error_label = label

    def _validate(self) -> None:
        """Run validation and update visual state."""
        if self._validator_func is None:
            self._is_valid = True
        else:
            self._is_valid = self._validator_func(self.text())

        if self._is_valid:
            self.setStyleSheet(f"""
                QLineEdit {{
                    border: 1px solid {COLORS['border']};
                    border-radius: 4px;
                    padding: 6px;
                }}
                QLineEdit:focus {{
                    border-color: {COLORS['primary']};
                }}
            """)
            if self._error_label:
                self._error_label.hide()
        else:
            self.setStyleSheet(f"""
                QLineEdit {{
                    border: 1px solid {COLORS['error']};
                    border-radius: 4px;
                    padding: 6px;
                    background-color: {COLORS['error_light']};
                }}
            """)
            if self._error_label:
                self._error_label.setText(self._error_message)
                self._error_label.setStyleSheet(f"color: {COLORS['error']}; font-size: 9pt;")
                self._error_label.show()

        self.validation_changed.emit(self._is_valid)

    def is_valid(self) -> bool:
        """Check if current value is valid."""
        return self._is_valid


class ValidatedSpinBox(QSpinBox):
    """Spin box with validation styling."""

    validation_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._min_warning = None
        self._max_warning = None
        self.valueChanged.connect(self._check_warnings)

    def set_warning_range(self, min_val: int = None, max_val: int = None) -> None:
        """Set warning thresholds (different from hard min/max)."""
        self._min_warning = min_val
        self._max_warning = max_val
        self._check_warnings()

    def _check_warnings(self) -> None:
        """Check if value is in warning range."""
        value = self.value()
        in_warning = False

        if self._min_warning is not None and value < self._min_warning:
            in_warning = True
        if self._max_warning is not None and value > self._max_warning:
            in_warning = True

        if in_warning:
            self.setStyleSheet(f"""
                QSpinBox {{
                    border: 1px solid {COLORS['warning']};
                    background-color: {COLORS['warning_light']};
                }}
            """)
        else:
            self.setStyleSheet("")


class ConfirmDialog(QDialog):
    """
    Confirmation dialog with customizable buttons.

    Usage:
        if ConfirmDialog.ask(self, "Delete item?", "This cannot be undone."):
            delete_item()
    """

    def __init__(self, title: str, message: str, parent=None,
                 confirm_text: str = "Confirm", cancel_text: str = "Cancel",
                 danger: bool = False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self._result = False
        self._setup_ui(message, confirm_text, cancel_text, danger)

    def _setup_ui(self, message: str, confirm_text: str, cancel_text: str, danger: bool) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Message
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton(cancel_text)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        confirm_btn = QPushButton(confirm_text)
        if danger:
            confirm_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['error']};
                    color: white;
                }}
                QPushButton:hover {{
                    background-color: #B71C1C;
                }}
            """)
        else:
            confirm_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['primary']};
                    color: white;
                }}
            """)
        confirm_btn.clicked.connect(self.accept)
        btn_layout.addWidget(confirm_btn)

        layout.addLayout(btn_layout)

        self.setMinimumWidth(350)

    @staticmethod
    def ask(parent, title: str, message: str, danger: bool = False) -> bool:
        """Static method to show dialog and get result."""
        dialog = ConfirmDialog(title, message, parent, danger=danger)
        return dialog.exec() == QDialog.DialogCode.Accepted


class ToastNotification(QFrame):
    """
    Toast-style notification that appears briefly.

    Usage:
        ToastNotification.show_toast(parent, "Item saved!", "success")
    """

    _active_toasts = []

    def __init__(self, message: str, toast_type: str = "info", parent=None):
        super().__init__(parent)
        self._setup_ui(message, toast_type)

        # Position at top right of parent
        if parent:
            y_offset = 60 + len(ToastNotification._active_toasts) * 60
            self.move(parent.width() - self.width() - 20, y_offset)

        ToastNotification._active_toasts.append(self)

        # Auto-hide after 3 seconds
        QTimer.singleShot(3000, self._hide_toast)

    def _setup_ui(self, message: str, toast_type: str) -> None:
        self.setFixedSize(300, 50)

        colors = {
            "success": (COLORS['success'], COLORS['success_light']),
            "error": (COLORS['error'], COLORS['error_light']),
            "warning": (COLORS['warning'], COLORS['warning_light']),
            "info": (COLORS['info'], COLORS['info_light'])
        }
        fg, bg = colors.get(toast_type, colors['info'])

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {fg};
                border-radius: 6px;
            }}
        """)

        layout = QHBoxLayout(self)

        icons = {"success": "✓", "error": "✕", "warning": "⚠", "info": "ℹ"}
        icon = QLabel(icons.get(toast_type, "ℹ"))
        icon.setStyleSheet(f"color: {fg}; font-size: 16pt;")
        layout.addWidget(icon)

        text = QLabel(message)
        text.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(text, 1)

        self.show()
        self.raise_()

    def _hide_toast(self) -> None:
        """Hide and cleanup toast."""
        if self in ToastNotification._active_toasts:
            ToastNotification._active_toasts.remove(self)
        self.hide()
        self.deleteLater()

    @staticmethod
    def show_toast(parent, message: str, toast_type: str = "info") -> None:
        """Static method to show a toast notification."""
        ToastNotification(message, toast_type, parent)
