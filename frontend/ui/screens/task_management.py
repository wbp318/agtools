"""
Task Management Screen

Screen for managing farm tasks - create, edit, update status, and track progress.
AgTools v2.5.0 Phase 2
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QDialog, QFormLayout,
    QMessageBox, QCheckBox, QTextEdit, QDateEdit
)
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QFont, QColor

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.task_api import get_task_api, TaskInfo
from api.user_api import get_user_api
from api.crew_api import get_crew_api
from api.auth_api import UserInfo


# Status colors
STATUS_COLORS = {
    "todo": "#9e9e9e",       # Gray
    "in_progress": "#1976d2", # Blue
    "completed": "#2e7d32",   # Green
    "cancelled": "#f57c00"    # Orange
}

# Priority colors
PRIORITY_COLORS = {
    "low": "#9e9e9e",      # Gray
    "medium": "#1976d2",   # Blue
    "high": "#f57c00",     # Orange
    "urgent": "#d32f2f"    # Red
}


class CreateTaskDialog(QDialog):
    """Dialog for creating a new task."""

    def __init__(self, users: list = None, crews: list = None, current_user: UserInfo = None, parent=None):
        super().__init__(parent)
        self.users = users or []
        self.crews = crews or []
        self.current_user = current_user
        self.setWindowTitle("Create New Task")
        self.setMinimumWidth(450)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Title
        self._title_input = QLineEdit()
        self._title_input.setPlaceholderText("Required")
        form_layout.addRow("Title:", self._title_input)

        # Description
        self._desc_input = QTextEdit()
        self._desc_input.setMaximumHeight(80)
        self._desc_input.setPlaceholderText("Optional description...")
        form_layout.addRow("Description:", self._desc_input)

        # Priority
        self._priority_combo = QComboBox()
        self._priority_combo.addItems(["low", "medium", "high", "urgent"])
        self._priority_combo.setCurrentText("medium")
        form_layout.addRow("Priority:", self._priority_combo)

        # Assign to user
        self._user_combo = QComboBox()
        self._user_combo.addItem("Unassigned", None)
        for user in self.users:
            display_name = f"{user.first_name or ''} {user.last_name or ''} ({user.username})".strip()
            self._user_combo.addItem(display_name, user.id)
        form_layout.addRow("Assign to User:", self._user_combo)

        # Assign to crew
        self._crew_combo = QComboBox()
        self._crew_combo.addItem("No Crew", None)
        for crew in self.crews:
            self._crew_combo.addItem(crew.name, crew.id)
        form_layout.addRow("Assign to Crew:", self._crew_combo)

        # Due date
        self._due_date_check = QCheckBox("Set due date")
        self._due_date_edit = QDateEdit()
        self._due_date_edit.setCalendarPopup(True)
        self._due_date_edit.setDate(QDate.currentDate().addDays(7))
        self._due_date_edit.setEnabled(False)
        self._due_date_check.toggled.connect(self._due_date_edit.setEnabled)

        due_layout = QHBoxLayout()
        due_layout.addWidget(self._due_date_check)
        due_layout.addWidget(self._due_date_edit)
        due_layout.addStretch()
        form_layout.addRow("Due Date:", due_layout)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        create_btn = QPushButton("Create Task")
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
        create_btn.clicked.connect(self._create_task)
        button_layout.addWidget(create_btn)

        layout.addLayout(button_layout)

    def _create_task(self):
        """Validate and prepare task data."""
        title = self._title_input.text().strip()

        if not title:
            QMessageBox.warning(self, "Validation Error", "Title is required")
            return

        self.task_data = {
            "title": title,
            "description": self._desc_input.toPlainText().strip() or None,
            "priority": self._priority_combo.currentText(),
            "assigned_to_user_id": self._user_combo.currentData(),
            "assigned_to_crew_id": self._crew_combo.currentData(),
            "due_date": self._due_date_edit.date().toString("yyyy-MM-dd") if self._due_date_check.isChecked() else None
        }
        self.accept()


class EditTaskDialog(QDialog):
    """Dialog for editing an existing task."""

    def __init__(self, task: TaskInfo, users: list = None, crews: list = None, parent=None):
        super().__init__(parent)
        self.task = task
        self.users = users or []
        self.crews = crews or []
        self.setWindowTitle(f"Edit Task: {task.title[:30]}...")
        self.setMinimumWidth(450)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # Title
        self._title_input = QLineEdit(self.task.title)
        form_layout.addRow("Title:", self._title_input)

        # Description
        self._desc_input = QTextEdit()
        self._desc_input.setMaximumHeight(80)
        self._desc_input.setText(self.task.description or "")
        form_layout.addRow("Description:", self._desc_input)

        # Status
        self._status_combo = QComboBox()
        self._status_combo.addItems(["todo", "in_progress", "completed", "cancelled"])
        self._status_combo.setCurrentText(self.task.status)
        form_layout.addRow("Status:", self._status_combo)

        # Priority
        self._priority_combo = QComboBox()
        self._priority_combo.addItems(["low", "medium", "high", "urgent"])
        self._priority_combo.setCurrentText(self.task.priority)
        form_layout.addRow("Priority:", self._priority_combo)

        # Assign to user
        self._user_combo = QComboBox()
        self._user_combo.addItem("Unassigned", None)
        selected_user_idx = 0
        for idx, user in enumerate(self.users):
            display_name = f"{user.first_name or ''} {user.last_name or ''} ({user.username})".strip()
            self._user_combo.addItem(display_name, user.id)
            if user.id == self.task.assigned_to_user_id:
                selected_user_idx = idx + 1
        self._user_combo.setCurrentIndex(selected_user_idx)
        form_layout.addRow("Assign to User:", self._user_combo)

        # Assign to crew
        self._crew_combo = QComboBox()
        self._crew_combo.addItem("No Crew", None)
        selected_crew_idx = 0
        for idx, crew in enumerate(self.crews):
            self._crew_combo.addItem(crew.name, crew.id)
            if crew.id == self.task.assigned_to_crew_id:
                selected_crew_idx = idx + 1
        self._crew_combo.setCurrentIndex(selected_crew_idx)
        form_layout.addRow("Assign to Crew:", self._crew_combo)

        # Due date
        self._due_date_check = QCheckBox("Set due date")
        self._due_date_edit = QDateEdit()
        self._due_date_edit.setCalendarPopup(True)

        if self.task.due_date:
            self._due_date_check.setChecked(True)
            try:
                # Parse date string
                date_str = self.task.due_date.split("T")[0]
                parts = date_str.split("-")
                self._due_date_edit.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))
            except (ValueError, IndexError):
                self._due_date_edit.setDate(QDate.currentDate())
        else:
            self._due_date_edit.setDate(QDate.currentDate().addDays(7))
            self._due_date_edit.setEnabled(False)

        self._due_date_check.toggled.connect(self._due_date_edit.setEnabled)

        due_layout = QHBoxLayout()
        due_layout.addWidget(self._due_date_check)
        due_layout.addWidget(self._due_date_edit)
        due_layout.addStretch()
        form_layout.addRow("Due Date:", due_layout)

        layout.addLayout(form_layout)

        # Info section
        info_label = QLabel(f"Created by: {self.task.created_by_user_name} on {self.task.created_at[:10] if self.task.created_at else 'Unknown'}")
        info_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(info_label)

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
        save_btn.clicked.connect(self._save_task)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _save_task(self):
        """Validate and prepare task update data."""
        title = self._title_input.text().strip()

        if not title:
            QMessageBox.warning(self, "Validation Error", "Title is required")
            return

        self.task_data = {
            "title": title,
            "description": self._desc_input.toPlainText().strip() or None,
            "status": self._status_combo.currentText(),
            "priority": self._priority_combo.currentText(),
            "assigned_to_user_id": self._user_combo.currentData() or 0,
            "assigned_to_crew_id": self._crew_combo.currentData() or 0,
            "due_date": self._due_date_edit.date().toString("yyyy-MM-dd") if self._due_date_check.isChecked() else None
        }
        self.accept()


class TaskManagementScreen(QWidget):
    """
    Task management screen for Farm Operations Manager.

    Features:
    - List tasks with filters (status, priority, my tasks)
    - Create new tasks
    - Edit existing tasks
    - Change task status
    - Delete tasks (manager/admin only)
    """

    def __init__(self, current_user: UserInfo = None, parent=None):
        super().__init__(parent)
        self._current_user = current_user
        self._task_api = get_task_api()
        self._user_api = get_user_api()
        self._crew_api = get_crew_api()
        self._tasks: list[TaskInfo] = []
        self._users = []
        self._crews = []
        self._setup_ui()
        self._load_data()

    def set_current_user(self, user: UserInfo):
        """Set the current user after login."""
        self._current_user = user
        self._load_data()

    def _setup_ui(self):
        """Set up the task management UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Task Management")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #2e7d32;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Add task button
        add_btn = QPushButton("+ New Task")
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

        # Status filter
        filter_layout.addWidget(QLabel("Status:"))
        self._status_filter = QComboBox()
        self._status_filter.addItems(["All", "todo", "in_progress", "completed", "cancelled"])
        self._status_filter.currentIndexChanged.connect(self._load_tasks)
        filter_layout.addWidget(self._status_filter)

        # Priority filter
        filter_layout.addWidget(QLabel("Priority:"))
        self._priority_filter = QComboBox()
        self._priority_filter.addItems(["All", "low", "medium", "high", "urgent"])
        self._priority_filter.currentIndexChanged.connect(self._load_tasks)
        filter_layout.addWidget(self._priority_filter)

        # My tasks checkbox
        self._my_tasks_check = QCheckBox("My Tasks Only")
        self._my_tasks_check.toggled.connect(self._load_tasks)
        filter_layout.addWidget(self._my_tasks_check)

        filter_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_tasks)
        filter_layout.addWidget(refresh_btn)

        layout.addLayout(filter_layout)

        # Tasks table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "Title", "Status", "Priority", "Assigned To", "Due Date", "Created", "Actions"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(6, 200)
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

    def _load_data(self):
        """Load users, crews, and tasks."""
        # Load users for assignment dropdown
        try:
            self._users, _ = self._user_api.list_users(is_active=True)
        except Exception:
            self._users = []

        # Load crews for assignment dropdown
        try:
            self._crews, _ = self._crew_api.list_crews()
        except Exception:
            self._crews = []

        # Load tasks
        self._load_tasks()

    def _load_tasks(self):
        """Load tasks from API with current filters."""
        status = None
        status_filter = self._status_filter.currentText()
        if status_filter != "All":
            status = status_filter

        priority = None
        priority_filter = self._priority_filter.currentText()
        if priority_filter != "All":
            priority = priority_filter

        my_tasks = self._my_tasks_check.isChecked()

        tasks, error = self._task_api.list_tasks(
            status=status,
            priority=priority,
            my_tasks=my_tasks
        )

        if error:
            self._status_label.setText(f"Error loading tasks: {error}")
            self._status_label.setStyleSheet("color: #d32f2f;")
            return

        self._tasks = tasks
        self._populate_table()
        self._status_label.setText(f"{len(tasks)} tasks found")
        self._status_label.setStyleSheet("color: #666;")

    def _populate_table(self):
        """Populate the table with task data."""
        self._table.setRowCount(len(self._tasks))

        for row, task in enumerate(self._tasks):
            # Title (bold if overdue)
            title_item = QTableWidgetItem(task.title)
            if task.is_overdue:
                font = title_item.font()
                font.setBold(True)
                title_item.setFont(font)
                title_item.setForeground(QColor("#d32f2f"))
            self._table.setItem(row, 0, title_item)

            # Status (color-coded)
            status_item = QTableWidgetItem(task.status_display)
            status_item.setForeground(QColor(STATUS_COLORS.get(task.status, "#666")))
            self._table.setItem(row, 1, status_item)

            # Priority (color-coded)
            priority_item = QTableWidgetItem(task.priority_display)
            priority_item.setForeground(QColor(PRIORITY_COLORS.get(task.priority, "#666")))
            self._table.setItem(row, 2, priority_item)

            # Assigned To
            self._table.setItem(row, 3, QTableWidgetItem(task.assigned_to_display))

            # Due Date (red if overdue)
            due_item = QTableWidgetItem(task.due_date[:10] if task.due_date else "-")
            if task.is_overdue:
                due_item.setForeground(QColor("#d32f2f"))
            self._table.setItem(row, 4, due_item)

            # Created
            created = task.created_at[:10] if task.created_at else "-"
            self._table.setItem(row, 5, QTableWidgetItem(created))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)

            # Edit button
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
            edit_btn.clicked.connect(lambda checked, t=task: self._show_edit_dialog(t))
            actions_layout.addWidget(edit_btn)

            # Quick status buttons
            if task.status == "todo":
                start_btn = QPushButton("Start")
                start_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2e7d32;
                        color: white;
                        padding: 4px 8px;
                        border: none;
                        border-radius: 3px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #1b5e20;
                    }
                """)
                start_btn.clicked.connect(lambda checked, t=task: self._change_status(t, "in_progress"))
                actions_layout.addWidget(start_btn)

            elif task.status == "in_progress":
                complete_btn = QPushButton("Complete")
                complete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2e7d32;
                        color: white;
                        padding: 4px 8px;
                        border: none;
                        border-radius: 3px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #1b5e20;
                    }
                """)
                complete_btn.clicked.connect(lambda checked, t=task: self._change_status(t, "completed"))
                actions_layout.addWidget(complete_btn)

            # Delete button (manager/admin only)
            if self._current_user and self._current_user.role in ("admin", "manager"):
                delete_btn = QPushButton("Delete")
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #d32f2f;
                        color: white;
                        padding: 4px 8px;
                        border: none;
                        border-radius: 3px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #b71c1c;
                    }
                """)
                delete_btn.clicked.connect(lambda checked, t=task: self._delete_task(t))
                actions_layout.addWidget(delete_btn)

            self._table.setCellWidget(row, 6, actions_widget)

    def _show_create_dialog(self):
        """Show create task dialog."""
        dialog = CreateTaskDialog(
            users=self._users,
            crews=self._crews,
            current_user=self._current_user,
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            task, error = self._task_api.create_task(**dialog.task_data)
            if error:
                QMessageBox.critical(self, "Error", f"Failed to create task: {error}")
            else:
                QMessageBox.information(self, "Success", f"Task '{task.title}' created successfully")
                self._load_tasks()

    def _show_edit_dialog(self, task: TaskInfo):
        """Show edit task dialog."""
        dialog = EditTaskDialog(
            task=task,
            users=self._users,
            crews=self._crews,
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_task, error = self._task_api.update_task(task.id, **dialog.task_data)
            if error:
                QMessageBox.critical(self, "Error", f"Failed to update task: {error}")
            else:
                QMessageBox.information(self, "Success", "Task updated successfully")
                self._load_tasks()

    def _change_status(self, task: TaskInfo, new_status: str):
        """Change task status."""
        updated_task, error = self._task_api.change_status(task.id, new_status)
        if error:
            QMessageBox.critical(self, "Error", f"Failed to change status: {error}")
        else:
            self._load_tasks()

    def _delete_task(self, task: TaskInfo):
        """Delete a task."""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete task '{task.title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, error = self._task_api.delete_task(task.id)
            if error:
                QMessageBox.critical(self, "Error", f"Failed to delete task: {error}")
            else:
                QMessageBox.information(self, "Success", "Task deleted successfully")
                self._load_tasks()

    def refresh(self):
        """Refresh the task list."""
        self._load_data()
