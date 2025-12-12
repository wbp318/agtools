"""
User Management Screen

Admin screen for managing users - create, edit, deactivate users.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QDialog, QFormLayout,
    QMessageBox, QCheckBox, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.user_api import get_user_api, UserAPI
from api.auth_api import UserInfo


class CreateUserDialog(QDialog):
    """Dialog for creating a new user."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New User")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self._username_input = QLineEdit()
        self._username_input.setPlaceholderText("Required")
        form_layout.addRow("Username:", self._username_input)

        self._email_input = QLineEdit()
        self._email_input.setPlaceholderText("Required")
        form_layout.addRow("Email:", self._email_input)

        self._password_input = QLineEdit()
        self._password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_input.setPlaceholderText("Min 8 characters")
        form_layout.addRow("Password:", self._password_input)

        self._first_name_input = QLineEdit()
        form_layout.addRow("First Name:", self._first_name_input)

        self._last_name_input = QLineEdit()
        form_layout.addRow("Last Name:", self._last_name_input)

        self._phone_input = QLineEdit()
        form_layout.addRow("Phone:", self._phone_input)

        self._role_combo = QComboBox()
        self._role_combo.addItems(["crew", "manager", "admin"])
        form_layout.addRow("Role:", self._role_combo)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        self._create_btn = QPushButton("Create User")
        self._create_btn.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1b5e20;
            }
        """)
        self._create_btn.clicked.connect(self._create_user)
        button_layout.addWidget(self._create_btn)

        layout.addLayout(button_layout)

    def _create_user(self):
        """Validate and create user."""
        username = self._username_input.text().strip()
        email = self._email_input.text().strip()
        password = self._password_input.text()

        if not username:
            QMessageBox.warning(self, "Validation Error", "Username is required")
            return
        if not email:
            QMessageBox.warning(self, "Validation Error", "Email is required")
            return
        if len(password) < 8:
            QMessageBox.warning(self, "Validation Error", "Password must be at least 8 characters")
            return

        self.user_data = {
            "username": username,
            "email": email,
            "password": password,
            "first_name": self._first_name_input.text().strip() or None,
            "last_name": self._last_name_input.text().strip() or None,
            "phone": self._phone_input.text().strip() or None,
            "role": self._role_combo.currentText()
        }
        self.accept()


class EditUserDialog(QDialog):
    """Dialog for editing an existing user."""

    def __init__(self, user: UserInfo, parent=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle(f"Edit User: {user.username}")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Username (read-only)
        username_label = QLabel(self.user.username)
        username_label.setStyleSheet("font-weight: bold;")
        form_layout.addRow("Username:", username_label)

        self._email_input = QLineEdit(self.user.email)
        form_layout.addRow("Email:", self._email_input)

        self._first_name_input = QLineEdit(self.user.first_name or "")
        form_layout.addRow("First Name:", self._first_name_input)

        self._last_name_input = QLineEdit(self.user.last_name or "")
        form_layout.addRow("Last Name:", self._last_name_input)

        self._phone_input = QLineEdit(self.user.phone or "")
        form_layout.addRow("Phone:", self._phone_input)

        self._role_combo = QComboBox()
        self._role_combo.addItems(["crew", "manager", "admin"])
        self._role_combo.setCurrentText(self.user.role)
        form_layout.addRow("Role:", self._role_combo)

        self._active_checkbox = QCheckBox("Active")
        self._active_checkbox.setChecked(self.user.is_active)
        form_layout.addRow("Status:", self._active_checkbox)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Changes")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1b5e20;
            }
        """)
        save_btn.clicked.connect(self._save_user)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _save_user(self):
        """Validate and save user changes."""
        email = self._email_input.text().strip()

        if not email:
            QMessageBox.warning(self, "Validation Error", "Email is required")
            return

        self.user_data = {
            "email": email,
            "first_name": self._first_name_input.text().strip() or None,
            "last_name": self._last_name_input.text().strip() or None,
            "phone": self._phone_input.text().strip() or None,
            "role": self._role_combo.currentText(),
            "is_active": self._active_checkbox.isChecked()
        }
        self.accept()


class UserManagementScreen(QWidget):
    """
    User management screen for administrators.

    Features:
    - List all users with filtering
    - Create new users
    - Edit existing users
    - Deactivate/reactivate users
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._user_api = get_user_api()
        self._users: list[UserInfo] = []
        self._setup_ui()
        self._load_users()

    def _setup_ui(self):
        """Set up the user management UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("User Management")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #2e7d32;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Add user button
        add_btn = QPushButton("+ Add User")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1b5e20;
            }
        """)
        add_btn.clicked.connect(self._show_create_dialog)
        header_layout.addWidget(add_btn)

        layout.addLayout(header_layout)

        # Filters
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Filter by Role:"))
        self._role_filter = QComboBox()
        self._role_filter.addItems(["All Roles", "admin", "manager", "crew"])
        self._role_filter.currentIndexChanged.connect(self._load_users)
        filter_layout.addWidget(self._role_filter)

        filter_layout.addWidget(QLabel("Status:"))
        self._status_filter = QComboBox()
        self._status_filter.addItems(["All", "Active", "Inactive"])
        self._status_filter.currentIndexChanged.connect(self._load_users)
        filter_layout.addWidget(self._status_filter)

        filter_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_users)
        filter_layout.addWidget(refresh_btn)

        layout.addLayout(filter_layout)

        # Users table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "Username", "Name", "Email", "Role", "Status", "Last Login", "Actions"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(6, 150)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #ddd;
                font-weight: bold;
            }
        """)
        layout.addWidget(self._table)

        # Status bar
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #666;")
        layout.addWidget(self._status_label)

    def _load_users(self):
        """Load users from API with current filters."""
        role = None
        role_filter = self._role_filter.currentText()
        if role_filter != "All Roles":
            role = role_filter

        is_active = None
        status_filter = self._status_filter.currentText()
        if status_filter == "Active":
            is_active = True
        elif status_filter == "Inactive":
            is_active = False

        users, error = self._user_api.list_users(role=role, is_active=is_active)

        if error:
            self._status_label.setText(f"Error loading users: {error}")
            self._status_label.setStyleSheet("color: #d32f2f;")
            return

        self._users = users
        self._populate_table()
        self._status_label.setText(f"{len(users)} users found")
        self._status_label.setStyleSheet("color: #666;")

    def _populate_table(self):
        """Populate the table with user data."""
        self._table.setRowCount(len(self._users))

        for row, user in enumerate(self._users):
            # Username
            self._table.setItem(row, 0, QTableWidgetItem(user.username))

            # Name
            self._table.setItem(row, 1, QTableWidgetItem(user.full_name))

            # Email
            self._table.setItem(row, 2, QTableWidgetItem(user.email))

            # Role
            role_item = QTableWidgetItem(user.role.upper())
            if user.role == "admin":
                role_item.setForeground(QColor("#d32f2f"))
            elif user.role == "manager":
                role_item.setForeground(QColor("#1976d2"))
            self._table.setItem(row, 3, role_item)

            # Status
            status_item = QTableWidgetItem("Active" if user.is_active else "Inactive")
            status_item.setForeground(QColor("#2e7d32") if user.is_active else QColor("#666"))
            self._table.setItem(row, 4, status_item)

            # Last Login
            last_login = user.last_login[:10] if user.last_login else "Never"
            self._table.setItem(row, 5, QTableWidgetItem(last_login))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)

            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1976d2;
                    color: white;
                    padding: 4px 8px;
                    border: none;
                    border-radius: 3px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #1565c0;
                }
            """)
            edit_btn.clicked.connect(lambda checked, u=user: self._show_edit_dialog(u))
            actions_layout.addWidget(edit_btn)

            if user.is_active:
                deactivate_btn = QPushButton("Deactivate")
                deactivate_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f57c00;
                        color: white;
                        padding: 4px 8px;
                        border: none;
                        border-radius: 3px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #ef6c00;
                    }
                """)
                deactivate_btn.clicked.connect(lambda checked, u=user: self._deactivate_user(u))
                actions_layout.addWidget(deactivate_btn)

            self._table.setCellWidget(row, 6, actions_widget)

    def _show_create_dialog(self):
        """Show create user dialog."""
        dialog = CreateUserDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            user, error = self._user_api.create_user(**dialog.user_data)
            if error:
                QMessageBox.critical(self, "Error", f"Failed to create user: {error}")
            else:
                QMessageBox.information(self, "Success", f"User '{user.username}' created successfully")
                self._load_users()

    def _show_edit_dialog(self, user: UserInfo):
        """Show edit user dialog."""
        dialog = EditUserDialog(user, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_user, error = self._user_api.update_user(user.id, **dialog.user_data)
            if error:
                QMessageBox.critical(self, "Error", f"Failed to update user: {error}")
            else:
                QMessageBox.information(self, "Success", "User updated successfully")
                self._load_users()

    def _deactivate_user(self, user: UserInfo):
        """Deactivate a user."""
        reply = QMessageBox.question(
            self,
            "Confirm Deactivation",
            f"Are you sure you want to deactivate user '{user.username}'?\n\nThey will no longer be able to log in.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, error = self._user_api.deactivate_user(user.id)
            if error:
                QMessageBox.critical(self, "Error", f"Failed to deactivate user: {error}")
            else:
                QMessageBox.information(self, "Success", f"User '{user.username}' has been deactivated")
                self._load_users()

    def refresh(self):
        """Refresh the user list."""
        self._load_users()
