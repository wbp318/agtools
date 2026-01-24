"""
Crew Management Screen

Admin screen for managing crews/teams and their members.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QDialog, QFormLayout,
    QMessageBox, QTextEdit, QListWidget, QListWidgetItem,
    QSplitter, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.crew_api import get_crew_api, CrewInfo, CrewMember
from api.user_api import get_user_api
from api.auth_api import UserInfo


class CreateCrewDialog(QDialog):
    """Dialog for creating a new crew."""

    def __init__(self, managers: list[UserInfo], parent=None):
        super().__init__(parent)
        self.managers = managers
        self.setWindowTitle("Create New Crew")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Required")
        form_layout.addRow("Crew Name:", self._name_input)

        self._description_input = QTextEdit()
        self._description_input.setMaximumHeight(80)
        self._description_input.setPlaceholderText("Optional description")
        form_layout.addRow("Description:", self._description_input)

        self._manager_combo = QComboBox()
        self._manager_combo.addItem("No Manager", None)
        for manager in self.managers:
            self._manager_combo.addItem(f"{manager.full_name} ({manager.username})", manager.id)
        form_layout.addRow("Manager:", self._manager_combo)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        create_btn = QPushButton("Create Crew")
        create_btn.setStyleSheet("""
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
        create_btn.clicked.connect(self._create_crew)
        button_layout.addWidget(create_btn)

        layout.addLayout(button_layout)

    def _create_crew(self):
        """Validate and create crew."""
        name = self._name_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation Error", "Crew name is required")
            return

        self.crew_data = {
            "name": name,
            "description": self._description_input.toPlainText().strip() or None,
            "manager_id": self._manager_combo.currentData()
        }
        self.accept()


class EditCrewDialog(QDialog):
    """Dialog for editing an existing crew."""

    def __init__(self, crew: CrewInfo, managers: list[UserInfo], parent=None):
        super().__init__(parent)
        self.crew = crew
        self.managers = managers
        self.setWindowTitle(f"Edit Crew: {crew.name}")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self._name_input = QLineEdit(self.crew.name)
        form_layout.addRow("Crew Name:", self._name_input)

        self._description_input = QTextEdit()
        self._description_input.setMaximumHeight(80)
        self._description_input.setPlainText(self.crew.description or "")
        form_layout.addRow("Description:", self._description_input)

        self._manager_combo = QComboBox()
        self._manager_combo.addItem("No Manager", None)
        for manager in self.managers:
            self._manager_combo.addItem(f"{manager.full_name} ({manager.username})", manager.id)
            if manager.id == self.crew.manager_id:
                self._manager_combo.setCurrentIndex(self._manager_combo.count() - 1)
        form_layout.addRow("Manager:", self._manager_combo)

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
        save_btn.clicked.connect(self._save_crew)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _save_crew(self):
        """Validate and save crew changes."""
        name = self._name_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation Error", "Crew name is required")
            return

        self.crew_data = {
            "name": name,
            "description": self._description_input.toPlainText().strip() or None,
            "manager_id": self._manager_combo.currentData()
        }
        self.accept()


class CrewManagementScreen(QWidget):
    """
    Crew management screen for administrators.

    Features:
    - List all crews
    - Create new crews
    - Edit existing crews
    - Manage crew members
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._crew_api = get_crew_api()
        self._user_api = get_user_api()
        self._crews: list[CrewInfo] = []
        self._selected_crew: CrewInfo = None
        self._crew_members: list[CrewMember] = []
        self._all_users: list[UserInfo] = []
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Set up the crew management UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Crew Management")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #2e7d32;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Add crew button
        add_btn = QPushButton("+ Add Crew")
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

        # Splitter for crews list and members
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side - Crews list
        crews_group = QGroupBox("Crews")
        crews_layout = QVBoxLayout(crews_group)

        self._crews_table = QTableWidget()
        self._crews_table.setColumnCount(4)
        self._crews_table.setHorizontalHeaderLabels(["Name", "Manager", "Members", "Actions"])
        self._crews_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._crews_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._crews_table.setColumnWidth(3, 120)
        self._crews_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._crews_table.setAlternatingRowColors(True)
        self._crews_table.itemSelectionChanged.connect(self._on_crew_selected)
        crews_layout.addWidget(self._crews_table)

        splitter.addWidget(crews_group)

        # Right side - Members
        members_group = QGroupBox("Crew Members")
        members_layout = QVBoxLayout(members_group)

        self._crew_name_label = QLabel("Select a crew to view members")
        self._crew_name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        members_layout.addWidget(self._crew_name_label)

        # Members list
        self._members_list = QListWidget()
        self._members_list.setStyleSheet("""
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e8f5e9;
                color: #2e7d32;
            }
        """)
        members_layout.addWidget(self._members_list)

        # Add/Remove member buttons
        member_buttons_layout = QHBoxLayout()

        self._add_member_combo = QComboBox()
        self._add_member_combo.setMinimumWidth(150)
        member_buttons_layout.addWidget(self._add_member_combo)

        add_member_btn = QPushButton("Add Member")
        add_member_btn.clicked.connect(self._add_member)
        add_member_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        member_buttons_layout.addWidget(add_member_btn)

        member_buttons_layout.addStretch()

        remove_member_btn = QPushButton("Remove Selected")
        remove_member_btn.clicked.connect(self._remove_member)
        remove_member_btn.setStyleSheet("""
            QPushButton {
                background-color: #f57c00;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ef6c00;
            }
        """)
        member_buttons_layout.addWidget(remove_member_btn)

        members_layout.addLayout(member_buttons_layout)

        splitter.addWidget(members_group)

        # Set initial sizes
        splitter.setSizes([400, 300])

        layout.addWidget(splitter)

        # Status bar
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #666;")
        layout.addWidget(self._status_label)

    def _load_data(self):
        """Load crews and users from API."""
        # Load crews
        crews, error = self._crew_api.list_crews()
        if error:
            self._status_label.setText(f"Error loading crews: {error}")
            self._status_label.setStyleSheet("color: #d32f2f;")
        else:
            self._crews = crews
            self._populate_crews_table()

        # Load users for member selection
        users, error = self._user_api.list_users(is_active=True)
        if not error:
            self._all_users = users
            self._update_member_combo()

        self._status_label.setText(f"{len(self._crews)} crews")
        self._status_label.setStyleSheet("color: #666;")

    def _populate_crews_table(self):
        """Populate the crews table."""
        self._crews_table.setRowCount(len(self._crews))

        for row, crew in enumerate(self._crews):
            # Name
            self._crews_table.setItem(row, 0, QTableWidgetItem(crew.name))

            # Manager
            manager_name = crew.manager_name or "No Manager"
            self._crews_table.setItem(row, 1, QTableWidgetItem(manager_name))

            # Members count
            self._crews_table.setItem(row, 2, QTableWidgetItem(str(crew.member_count)))

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
            edit_btn.clicked.connect(lambda checked, c=crew: self._show_edit_dialog(c))
            actions_layout.addWidget(edit_btn)

            self._crews_table.setCellWidget(row, 3, actions_widget)

    def _on_crew_selected(self):
        """Handle crew selection."""
        selected_rows = self._crews_table.selectionModel().selectedRows()
        if not selected_rows:
            self._selected_crew = None
            self._crew_name_label.setText("Select a crew to view members")
            self._members_list.clear()
            return

        row = selected_rows[0].row()
        self._selected_crew = self._crews[row]
        self._crew_name_label.setText(f"Members of: {self._selected_crew.name}")
        self._load_crew_members()

    def _load_crew_members(self):
        """Load members of the selected crew."""
        if not self._selected_crew:
            return

        members, error = self._crew_api.get_crew_members(self._selected_crew.id)
        if error:
            QMessageBox.warning(self, "Error", f"Failed to load members: {error}")
            return

        self._crew_members = members
        self._populate_members_list()
        self._update_member_combo()

    def _populate_members_list(self):
        """Populate the members list."""
        self._members_list.clear()

        for member in self._crew_members:
            item = QListWidgetItem(f"{member.full_name} ({member.username}) - {member.role.upper()}")
            item.setData(Qt.ItemDataRole.UserRole, member.user_id)
            self._members_list.addItem(item)

    def _update_member_combo(self):
        """Update the add member combo box with available users."""
        self._add_member_combo.clear()
        self._add_member_combo.addItem("Select user...", None)

        # Get IDs of current members
        current_member_ids = {m.user_id for m in self._crew_members}

        # Add users not already in the crew
        for user in self._all_users:
            if user.id not in current_member_ids:
                self._add_member_combo.addItem(f"{user.full_name} ({user.username})", user.id)

    def _add_member(self):
        """Add selected user to crew."""
        if not self._selected_crew:
            QMessageBox.warning(self, "Error", "Please select a crew first")
            return

        user_id = self._add_member_combo.currentData()
        if not user_id:
            QMessageBox.warning(self, "Error", "Please select a user to add")
            return

        success, error = self._crew_api.add_crew_member(self._selected_crew.id, user_id)
        if error:
            QMessageBox.critical(self, "Error", f"Failed to add member: {error}")
        else:
            self._load_crew_members()
            self._load_data()  # Refresh crew counts

    def _remove_member(self):
        """Remove selected member from crew."""
        if not self._selected_crew:
            return

        selected_item = self._members_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Error", "Please select a member to remove")
            return

        user_id = selected_item.data(Qt.ItemDataRole.UserRole)
        user_name = selected_item.text().split(" (")[0]

        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Remove {user_name} from {self._selected_crew.name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, error = self._crew_api.remove_crew_member(self._selected_crew.id, user_id)
            if error:
                QMessageBox.critical(self, "Error", f"Failed to remove member: {error}")
            else:
                self._load_crew_members()
                self._load_data()  # Refresh crew counts

    def _get_managers(self) -> list[UserInfo]:
        """Get list of users who can be managers (admin or manager role)."""
        return [u for u in self._all_users if u.role in ["admin", "manager"]]

    def _show_create_dialog(self):
        """Show create crew dialog."""
        dialog = CreateCrewDialog(self._get_managers(), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            crew, error = self._crew_api.create_crew(**dialog.crew_data)
            if error:
                QMessageBox.critical(self, "Error", f"Failed to create crew: {error}")
            else:
                QMessageBox.information(self, "Success", f"Crew '{crew.name}' created successfully")
                self._load_data()

    def _show_edit_dialog(self, crew: CrewInfo):
        """Show edit crew dialog."""
        dialog = EditCrewDialog(crew, self._get_managers(), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_crew, error = self._crew_api.update_crew(crew.id, **dialog.crew_data)
            if error:
                QMessageBox.critical(self, "Error", f"Failed to update crew: {error}")
            else:
                QMessageBox.information(self, "Success", "Crew updated successfully")
                self._load_data()

    def refresh(self):
        """Refresh the data."""
        self._load_data()
