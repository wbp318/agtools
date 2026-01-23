"""
Email Notification Service
Sends alerts for maintenance, inventory, spray windows, and more.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    import aiosmtplib
    SMTP_AVAILABLE = True
except ImportError:
    SMTP_AVAILABLE = False


class NotificationType(str, Enum):
    MAINTENANCE_DUE = "maintenance_due"
    MAINTENANCE_OVERDUE = "maintenance_overdue"
    LOW_STOCK = "low_stock"
    EXPIRING_SOON = "expiring_soon"
    SPRAY_WINDOW = "spray_window"
    TASK_ASSIGNED = "task_assigned"
    TASK_DUE = "task_due"
    TASK_OVERDUE = "task_overdue"
    DAILY_DIGEST = "daily_digest"
    WEEKLY_SUMMARY = "weekly_summary"


class NotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class EmailConfig:
    """SMTP configuration"""
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    from_email: str = os.getenv("FROM_EMAIL", "agtools@example.com")
    from_name: str = os.getenv("FROM_NAME", "AgTools Notifications")
    use_tls: bool = True


@dataclass
class Notification:
    """A notification to be sent"""
    notification_type: NotificationType
    priority: NotificationPriority
    subject: str
    body_text: str
    body_html: Optional[str] = None
    recipients: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class EmailNotificationService:
    """Service for sending email notifications"""

    def __init__(self, config: Optional[EmailConfig] = None):
        self.config = config or EmailConfig()
        self._notification_queue: List[Notification] = []
        self._templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        """Load email templates for each notification type"""
        return {
            NotificationType.MAINTENANCE_DUE: {
                "subject": "[AgTools] Maintenance Due: {equipment_name}",
                "body": """
Equipment Maintenance Reminder

Equipment: {equipment_name}
Type: {maintenance_type}
Due Date: {due_date}
Current Hours: {current_hours}
Next Service Hours: {next_service_hours}

Please schedule maintenance soon to avoid equipment downtime.

---
AgTools Farm Management System
                """,
                "html": """
<h2 style="color: #1a5f2a;">Equipment Maintenance Reminder</h2>
<table style="border-collapse: collapse; width: 100%;">
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Equipment:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{equipment_name}</td></tr>
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Type:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{maintenance_type}</td></tr>
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Due Date:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{due_date}</td></tr>
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Current Hours:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{current_hours}</td></tr>
</table>
<p style="margin-top: 20px;">Please schedule maintenance soon to avoid equipment downtime.</p>
<hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
<p style="color: #666; font-size: 12px;">AgTools Farm Management System</p>
                """
            },
            NotificationType.MAINTENANCE_OVERDUE: {
                "subject": "[URGENT] Maintenance Overdue: {equipment_name}",
                "body": """
⚠️ MAINTENANCE OVERDUE

Equipment: {equipment_name}
Type: {maintenance_type}
Was Due: {due_date}
Days Overdue: {days_overdue}

This equipment is overdue for service. Please address immediately.

---
AgTools Farm Management System
                """,
                "html": """
<h2 style="color: #c0392b;">⚠️ MAINTENANCE OVERDUE</h2>
<table style="border-collapse: collapse; width: 100%;">
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Equipment:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{equipment_name}</td></tr>
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Type:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{maintenance_type}</td></tr>
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Was Due:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd; color: #c0392b;">{due_date}</td></tr>
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Days Overdue:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd; color: #c0392b; font-weight: bold;">{days_overdue}</td></tr>
</table>
<p style="margin-top: 20px; color: #c0392b;"><strong>This equipment is overdue for service. Please address immediately.</strong></p>
                """
            },
            NotificationType.LOW_STOCK: {
                "subject": "[AgTools] Low Stock Alert: {item_name}",
                "body": """
Low Stock Alert

Item: {item_name}
Category: {category}
Current Quantity: {current_qty} {unit}
Reorder Point: {reorder_point} {unit}

Please reorder soon to avoid running out.

---
AgTools Farm Management System
                """,
                "html": """
<h2 style="color: #e67e22;">Low Stock Alert</h2>
<table style="border-collapse: collapse; width: 100%;">
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Item:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{item_name}</td></tr>
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Category:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{category}</td></tr>
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Current Quantity:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd; color: #e67e22;">{current_qty} {unit}</td></tr>
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Reorder Point:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{reorder_point} {unit}</td></tr>
</table>
<p style="margin-top: 20px;">Please reorder soon to avoid running out.</p>
                """
            },
            NotificationType.EXPIRING_SOON: {
                "subject": "[AgTools] Expiring Soon: {item_name}",
                "body": """
Product Expiration Warning

Item: {item_name}
Category: {category}
Quantity: {quantity} {unit}
Expiration Date: {expiration_date}
Days Until Expiration: {days_until}

Please use or dispose of this product before it expires.

---
AgTools Farm Management System
                """,
                "html": """
<h2 style="color: #e67e22;">Product Expiration Warning</h2>
<table style="border-collapse: collapse; width: 100%;">
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Item:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{item_name}</td></tr>
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Quantity:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{quantity} {unit}</td></tr>
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Expiration:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd; color: #e67e22;">{expiration_date}</td></tr>
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Days Left:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{days_until}</td></tr>
</table>
                """
            },
            NotificationType.SPRAY_WINDOW: {
                "subject": "[AgTools] Optimal Spray Window: {field_name}",
                "body": """
Optimal Spray Window Detected

Field: {field_name}
Target: {target_pest}
Product: {product_name}

Weather Conditions:
- Temperature: {temperature}°F
- Wind: {wind_speed} mph
- Humidity: {humidity}%
- Rain Forecast: {rain_forecast}

Optimal Window: {window_start} to {window_end}

This is a good time to spray based on current weather conditions.

---
AgTools Farm Management System
                """,
                "html": """
<h2 style="color: #27ae60;">Optimal Spray Window Detected</h2>
<table style="border-collapse: collapse; width: 100%;">
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Field:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{field_name}</td></tr>
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Target:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{target_pest}</td></tr>
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Product:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{product_name}</td></tr>
</table>
<h3 style="color: #1a5f2a; margin-top: 20px;">Weather Conditions</h3>
<table style="border-collapse: collapse; width: 100%;">
    <tr><td style="padding: 8px;">Temperature: {temperature}°F</td><td style="padding: 8px;">Wind: {wind_speed} mph</td></tr>
    <tr><td style="padding: 8px;">Humidity: {humidity}%</td><td style="padding: 8px;">Rain: {rain_forecast}</td></tr>
</table>
<p style="margin-top: 20px; padding: 15px; background: #eafaf1; border-left: 4px solid #27ae60;">
    <strong>Optimal Window:</strong> {window_start} to {window_end}
</p>
                """
            },
            NotificationType.TASK_ASSIGNED: {
                "subject": "[AgTools] New Task Assigned: {task_title}",
                "body": """
New Task Assigned

Task: {task_title}
Priority: {priority}
Due Date: {due_date}
Assigned By: {assigned_by}

Description:
{description}

---
AgTools Farm Management System
                """,
                "html": """
<h2 style="color: #1a5f2a;">New Task Assigned</h2>
<table style="border-collapse: collapse; width: 100%;">
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Task:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{task_title}</td></tr>
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Priority:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{priority}</td></tr>
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Due Date:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{due_date}</td></tr>
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Assigned By:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{assigned_by}</td></tr>
</table>
<h3 style="margin-top: 20px;">Description</h3>
<p>{description}</p>
                """
            },
            NotificationType.TASK_OVERDUE: {
                "subject": "[OVERDUE] Task Past Due: {task_title}",
                "body": """
⚠️ TASK OVERDUE

Task: {task_title}
Was Due: {due_date}
Days Overdue: {days_overdue}
Assigned To: {assigned_to}

Please complete this task as soon as possible.

---
AgTools Farm Management System
                """,
                "html": """
<h2 style="color: #c0392b;">⚠️ TASK OVERDUE</h2>
<table style="border-collapse: collapse; width: 100%;">
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Task:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{task_title}</td></tr>
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Was Due:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd; color: #c0392b;">{due_date}</td></tr>
    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Days Overdue:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd; color: #c0392b; font-weight: bold;">{days_overdue}</td></tr>
</table>
<p style="margin-top: 20px; color: #c0392b;"><strong>Please complete this task as soon as possible.</strong></p>
                """
            },
            NotificationType.DAILY_DIGEST: {
                "subject": "[AgTools] Daily Digest - {date}",
                "body": """
Daily Farm Digest - {date}

SUMMARY
-------
Tasks Due Today: {tasks_due}
Maintenance Alerts: {maintenance_alerts}
Low Stock Items: {low_stock_count}
Expiring Soon: {expiring_count}

{details}

---
AgTools Farm Management System
                """,
                "html": """
<h2 style="color: #1a5f2a;">Daily Farm Digest - {date}</h2>
<div style="display: flex; gap: 20px; margin: 20px 0;">
    <div style="padding: 15px; background: #f8f9fa; border-radius: 8px; text-align: center;">
        <div style="font-size: 24px; font-weight: bold; color: #1a5f2a;">{tasks_due}</div>
        <div style="color: #666;">Tasks Due</div>
    </div>
    <div style="padding: 15px; background: #f8f9fa; border-radius: 8px; text-align: center;">
        <div style="font-size: 24px; font-weight: bold; color: #e67e22;">{maintenance_alerts}</div>
        <div style="color: #666;">Maintenance</div>
    </div>
    <div style="padding: 15px; background: #f8f9fa; border-radius: 8px; text-align: center;">
        <div style="font-size: 24px; font-weight: bold; color: #c0392b;">{low_stock_count}</div>
        <div style="color: #666;">Low Stock</div>
    </div>
</div>
{details}
                """
            },
        }

    def _format_template(self, template: str, data: Dict[str, Any]) -> str:
        """Format a template string with data"""
        try:
            return template.format(**data)
        except KeyError as e:
            # Return template with missing key noted
            return template.replace("{" + str(e).strip("'") + "}", "[MISSING]")

    def create_notification(
        self,
        notification_type: NotificationType,
        recipients: List[str],
        data: Dict[str, Any],
        priority: NotificationPriority = NotificationPriority.NORMAL
    ) -> Notification:
        """Create a notification from template"""
        template = self._templates.get(notification_type, {})

        subject = self._format_template(
            template.get("subject", f"[AgTools] {notification_type.value}"),
            data
        )
        body_text = self._format_template(
            template.get("body", str(data)),
            data
        )
        body_html = self._format_template(
            template.get("html", ""),
            data
        ) if template.get("html") else None

        return Notification(
            notification_type=notification_type,
            priority=priority,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            recipients=recipients,
            data=data
        )

    async def send_notification(self, notification: Notification) -> Dict[str, Any]:
        """Send a notification via email"""
        if not SMTP_AVAILABLE:
            return {
                "status": "error",
                "message": "aiosmtplib not available. Install with: pip install aiosmtplib"
            }

        if not self.config.smtp_user or not self.config.smtp_password:
            return {
                "status": "error",
                "message": "SMTP credentials not configured. Set SMTP_USER and SMTP_PASSWORD environment variables."
            }

        results = []
        for recipient in notification.recipients:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = notification.subject
                msg["From"] = f"{self.config.from_name} <{self.config.from_email}>"
                msg["To"] = recipient

                # Add text part
                msg.attach(MIMEText(notification.body_text, "plain"))

                # Add HTML part if available
                if notification.body_html:
                    html_body = f"""
                    <html>
                    <head>
                        <style>
                            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                            table {{ border-collapse: collapse; width: 100%; max-width: 600px; }}
                            td {{ padding: 8px; }}
                        </style>
                    </head>
                    <body>
                        {notification.body_html}
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                        <p style="color: #666; font-size: 12px;">AgTools Farm Management System</p>
                    </body>
                    </html>
                    """
                    msg.attach(MIMEText(html_body, "html"))

                # Send email
                await aiosmtplib.send(
                    msg,
                    hostname=self.config.smtp_host,
                    port=self.config.smtp_port,
                    username=self.config.smtp_user,
                    password=self.config.smtp_password,
                    start_tls=self.config.use_tls
                )

                results.append({"recipient": recipient, "status": "sent"})

            except Exception as e:
                results.append({"recipient": recipient, "status": "failed", "error": str(e)})

        success_count = sum(1 for r in results if r["status"] == "sent")
        return {
            "status": "success" if success_count == len(notification.recipients) else "partial",
            "sent": success_count,
            "failed": len(notification.recipients) - success_count,
            "results": results
        }

    def queue_notification(self, notification: Notification):
        """Add notification to queue for batch sending"""
        self._notification_queue.append(notification)

    async def send_queued_notifications(self) -> Dict[str, Any]:
        """Send all queued notifications"""
        results = []
        while self._notification_queue:
            notification = self._notification_queue.pop(0)
            result = await self.send_notification(notification)
            results.append({
                "type": notification.notification_type.value,
                "subject": notification.subject,
                "result": result
            })

        return {
            "notifications_sent": len(results),
            "results": results
        }

    # Convenience methods for common notifications

    async def send_maintenance_alert(
        self,
        recipients: List[str],
        equipment_name: str,
        maintenance_type: str,
        due_date: str,
        current_hours: float = 0,
        next_service_hours: float = 0,
        is_overdue: bool = False,
        days_overdue: int = 0
    ) -> Dict[str, Any]:
        """Send maintenance due/overdue alert"""
        notification_type = NotificationType.MAINTENANCE_OVERDUE if is_overdue else NotificationType.MAINTENANCE_DUE
        priority = NotificationPriority.URGENT if is_overdue else NotificationPriority.HIGH

        notification = self.create_notification(
            notification_type=notification_type,
            recipients=recipients,
            priority=priority,
            data={
                "equipment_name": equipment_name,
                "maintenance_type": maintenance_type,
                "due_date": due_date,
                "current_hours": current_hours,
                "next_service_hours": next_service_hours,
                "days_overdue": days_overdue
            }
        )

        return await self.send_notification(notification)

    async def send_low_stock_alert(
        self,
        recipients: List[str],
        item_name: str,
        category: str,
        current_qty: float,
        reorder_point: float,
        unit: str = ""
    ) -> Dict[str, Any]:
        """Send low stock alert"""
        notification = self.create_notification(
            notification_type=NotificationType.LOW_STOCK,
            recipients=recipients,
            priority=NotificationPriority.HIGH,
            data={
                "item_name": item_name,
                "category": category,
                "current_qty": current_qty,
                "reorder_point": reorder_point,
                "unit": unit
            }
        )

        return await self.send_notification(notification)

    async def send_expiring_alert(
        self,
        recipients: List[str],
        item_name: str,
        category: str,
        quantity: float,
        unit: str,
        expiration_date: str,
        days_until: int
    ) -> Dict[str, Any]:
        """Send expiring soon alert"""
        priority = NotificationPriority.URGENT if days_until <= 7 else NotificationPriority.HIGH

        notification = self.create_notification(
            notification_type=NotificationType.EXPIRING_SOON,
            recipients=recipients,
            priority=priority,
            data={
                "item_name": item_name,
                "category": category,
                "quantity": quantity,
                "unit": unit,
                "expiration_date": expiration_date,
                "days_until": days_until
            }
        )

        return await self.send_notification(notification)

    async def send_spray_window_alert(
        self,
        recipients: List[str],
        field_name: str,
        target_pest: str,
        product_name: str,
        temperature: float,
        wind_speed: float,
        humidity: float,
        rain_forecast: str,
        window_start: str,
        window_end: str
    ) -> Dict[str, Any]:
        """Send optimal spray window alert"""
        notification = self.create_notification(
            notification_type=NotificationType.SPRAY_WINDOW,
            recipients=recipients,
            priority=NotificationPriority.HIGH,
            data={
                "field_name": field_name,
                "target_pest": target_pest,
                "product_name": product_name,
                "temperature": temperature,
                "wind_speed": wind_speed,
                "humidity": humidity,
                "rain_forecast": rain_forecast,
                "window_start": window_start,
                "window_end": window_end
            }
        )

        return await self.send_notification(notification)

    async def send_task_assigned_alert(
        self,
        recipients: List[str],
        task_title: str,
        priority: str,
        due_date: str,
        assigned_by: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """Send task assigned notification"""
        notification = self.create_notification(
            notification_type=NotificationType.TASK_ASSIGNED,
            recipients=recipients,
            priority=NotificationPriority.NORMAL,
            data={
                "task_title": task_title,
                "priority": priority,
                "due_date": due_date,
                "assigned_by": assigned_by,
                "description": description or "No description provided."
            }
        )

        return await self.send_notification(notification)

    async def send_daily_digest(
        self,
        recipients: List[str],
        tasks_due: int,
        maintenance_alerts: int,
        low_stock_count: int,
        expiring_count: int,
        details: str = ""
    ) -> Dict[str, Any]:
        """Send daily digest email"""
        notification = self.create_notification(
            notification_type=NotificationType.DAILY_DIGEST,
            recipients=recipients,
            priority=NotificationPriority.LOW,
            data={
                "date": datetime.now().strftime("%B %d, %Y"),
                "tasks_due": tasks_due,
                "maintenance_alerts": maintenance_alerts,
                "low_stock_count": low_stock_count,
                "expiring_count": expiring_count,
                "details": details
            }
        )

        return await self.send_notification(notification)

    def get_notification_types(self) -> List[Dict[str, str]]:
        """Get list of available notification types"""
        return [
            {"type": t.value, "name": t.name.replace("_", " ").title()}
            for t in NotificationType
        ]


# Singleton instance
_email_service: Optional[EmailNotificationService] = None


def get_email_notification_service() -> EmailNotificationService:
    """Get singleton email notification service instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailNotificationService()
    return _email_service
