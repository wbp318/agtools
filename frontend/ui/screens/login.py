"""
Login Screen

Handles user authentication with username/password.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QCheckBox, QSpacerItem,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.auth_api import get_auth_api, UserInfo, LoginResult
from config import get_settings


class LoginScreen(QWidget):
    """
    Login screen with username/password authentication.

    Signals:
        login_successful: Emitted when login succeeds, with UserInfo
        login_cancelled: Emitted when user cancels login
    """

    login_successful = pyqtSignal(object)  # UserInfo
    login_cancelled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = get_settings()
        self._auth_api = get_auth_api()
        self._setup_ui()

    def _setup_ui(self):
        """Set up the login UI."""
        self.setWindowTitle("AgTools - Login")
        self.setMinimumSize(400, 500)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # Add stretch at top
        main_layout.addStretch(1)

        # Logo/Title area
        title_frame = QFrame()
        title_layout = QVBoxLayout(title_frame)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # App title
        title_label = QLabel("AgTools")
        title_label.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2e7d32;")  # Agriculture green
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(title_label)

        # Subtitle
        subtitle_label = QLabel("Farm Operations Manager")
        subtitle_label.setFont(QFont("Arial", 14))
        subtitle_label.setStyleSheet("color: #666;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(subtitle_label)

        main_layout.addWidget(title_frame)

        # Spacer
        main_layout.addSpacing(30)

        # Login form
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(15)

        # Username field
        username_label = QLabel("Username")
        username_label.setStyleSheet("font-weight: bold; color: #333; border: none;")
        form_layout.addWidget(username_label)

        self._username_input = QLineEdit()
        self._username_input.setPlaceholderText("Enter your username")
        self._username_input.setMinimumHeight(40)
        self._username_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #2e7d32;
            }
        """)
        form_layout.addWidget(self._username_input)

        # Password field
        password_label = QLabel("Password")
        password_label.setStyleSheet("font-weight: bold; color: #333; border: none;")
        form_layout.addWidget(password_label)

        self._password_input = QLineEdit()
        self._password_input.setPlaceholderText("Enter your password")
        self._password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_input.setMinimumHeight(40)
        self._password_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #2e7d32;
            }
        """)
        form_layout.addWidget(self._password_input)

        # Remember me checkbox
        self._remember_checkbox = QCheckBox("Remember me")
        self._remember_checkbox.setStyleSheet("border: none; color: #666;")
        form_layout.addWidget(self._remember_checkbox)

        # Error message label (hidden initially)
        self._error_label = QLabel("")
        self._error_label.setStyleSheet("""
            color: #d32f2f;
            font-size: 13px;
            padding: 8px;
            background-color: #ffebee;
            border-radius: 4px;
            border: none;
        """)
        self._error_label.setVisible(False)
        self._error_label.setWordWrap(True)
        form_layout.addWidget(self._error_label)

        # Login button
        self._login_button = QPushButton("Sign In")
        self._login_button.setMinimumHeight(45)
        self._login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._login_button.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1b5e20;
            }
            QPushButton:pressed {
                background-color: #0d3d10;
            }
            QPushButton:disabled {
                background-color: #aaa;
            }
        """)
        self._login_button.clicked.connect(self._handle_login)
        form_layout.addWidget(self._login_button)

        main_layout.addWidget(form_frame)

        # Connection status
        self._status_label = QLabel("")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet("color: #666; font-size: 12px;")
        main_layout.addWidget(self._status_label)

        # Add stretch at bottom
        main_layout.addStretch(2)

        # Version label at bottom
        version_label = QLabel(f"Version {self._settings.app_version}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: #999; font-size: 11px;")
        main_layout.addWidget(version_label)

        # Connect enter key to login
        self._username_input.returnPressed.connect(self._focus_password)
        self._password_input.returnPressed.connect(self._handle_login)

        # Load saved username if remember me was checked
        self._load_remembered_user()

        # Check connection
        self._check_connection()

    def _focus_password(self):
        """Focus the password field."""
        self._password_input.setFocus()

    def _show_error(self, message: str):
        """Show error message."""
        self._error_label.setText(message)
        self._error_label.setVisible(True)

    def _hide_error(self):
        """Hide error message."""
        self._error_label.setVisible(False)

    def _check_connection(self):
        """Check API connection and update status."""
        from api.client import get_api_client
        client = get_api_client()

        if client.check_connection():
            self._status_label.setText("Connected to server")
            self._status_label.setStyleSheet("color: #2e7d32; font-size: 12px;")
        else:
            self._status_label.setText("Unable to connect to server")
            self._status_label.setStyleSheet("color: #d32f2f; font-size: 12px;")

    def _load_remembered_user(self):
        """Load remembered username if exists."""
        remembered_user = self._settings.get("remembered_user", "")
        if remembered_user:
            self._username_input.setText(remembered_user)
            self._remember_checkbox.setChecked(True)
            self._password_input.setFocus()
        else:
            self._username_input.setFocus()

    def _save_remembered_user(self, username: str):
        """Save username if remember me is checked."""
        if self._remember_checkbox.isChecked():
            self._settings.set("remembered_user", username)
        else:
            self._settings.set("remembered_user", "")
        self._settings.save()

    def _handle_login(self):
        """Handle login button click."""
        username = self._username_input.text().strip()
        password = self._password_input.text()

        # Validate inputs
        if not username:
            self._show_error("Please enter your username")
            self._username_input.setFocus()
            return

        if not password:
            self._show_error("Please enter your password")
            self._password_input.setFocus()
            return

        # Disable button during login
        self._login_button.setEnabled(False)
        self._login_button.setText("Signing in...")
        self._hide_error()

        try:
            # Attempt login
            result = self._auth_api.login(username, password)

            if result.success:
                # Save remembered user
                self._save_remembered_user(username)

                # Store tokens in settings
                if result.tokens:
                    self._settings.set("auth_token", result.tokens.access_token)
                    self._settings.set("refresh_token", result.tokens.refresh_token)
                    self._settings.save()

                # Emit success signal
                self.login_successful.emit(result.user)

            else:
                self._show_error(result.error or "Login failed")
                self._password_input.setFocus()
                self._password_input.selectAll()

        except Exception as e:
            self._show_error(f"Connection error: {str(e)}")

        finally:
            self._login_button.setEnabled(True)
            self._login_button.setText("Sign In")

    def clear_form(self):
        """Clear the login form."""
        if not self._remember_checkbox.isChecked():
            self._username_input.clear()
        self._password_input.clear()
        self._hide_error()

    def set_focus(self):
        """Set focus to appropriate field."""
        if self._username_input.text():
            self._password_input.setFocus()
        else:
            self._username_input.setFocus()
