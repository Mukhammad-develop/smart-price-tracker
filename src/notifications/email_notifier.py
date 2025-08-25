import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List
import logging

from .base_notifier import BaseNotifier, NotificationType, NotificationPriority

logger = logging.getLogger(__name__)

class EmailNotifier(BaseNotifier):
    """Email notification service using SMTP"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.smtp_server = config.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = config.get('smtp_port', 587)
        self.email_address = config.get('email_address')
        self.email_password = config.get('email_password')
        self.recipient_emails = config.get('recipient_emails', [])
        
        # If recipient_emails is a string, convert to list
        if isinstance(self.recipient_emails, str):
            self.recipient_emails = [email.strip() for email in self.recipient_emails.split(',')]
        
        # Use sender email as recipient if no recipients specified
        if not self.recipient_emails and self.email_address:
            self.recipient_emails = [self.email_address]
    
    def is_configured(self) -> bool:
        """Check if email notifier is properly configured"""
        return bool(
            self.email_address and 
            self.email_password and 
            self.recipient_emails and
            self.smtp_server
        )
    
    def send_notification(self, 
                         title: str, 
                         message: str, 
                         notification_type: NotificationType = NotificationType.GENERAL_ALERT,
                         priority: NotificationPriority = NotificationPriority.MEDIUM,
                         **kwargs) -> bool:
        """Send email notification"""
        
        if not self.should_send_notification(notification_type, kwargs.get('product_data')):
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_address
            msg['To'] = ', '.join(self.recipient_emails)
            
            # Add priority to subject
            priority_emoji = self.get_priority_emoji(priority)
            msg['Subject'] = f"{priority_emoji} {title}"
            
            # Create both plain text and HTML versions
            text_body = self._create_text_body(title, message, notification_type, priority)
            html_body = self._create_html_body(title, message, notification_type, priority)
            
            # Attach parts
            msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                
                for recipient in self.recipient_emails:
                    try:
                        msg['To'] = recipient
                        server.send_message(msg)
                        self.logger.info(f"Email notification sent to {recipient}")
                    except Exception as e:
                        self.logger.error(f"Failed to send email to {recipient}: {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")
            return False
    
    def _create_text_body(self, title: str, message: str, 
                         notification_type: NotificationType, 
                         priority: NotificationPriority) -> str:
        """Create plain text email body"""
        
        priority_text = f"Priority: {priority.value.upper()}"
        separator = "=" * 50
        
        return f"""
{separator}
{title}
{separator}

{message}

{priority_text}

---
Smart Price Tracker
Automated price monitoring system
        """.strip()
    
    def _create_html_body(self, title: str, message: str, 
                         notification_type: NotificationType, 
                         priority: NotificationPriority) -> str:
        """Create HTML email body"""
        
        # Color scheme based on notification type
        color_schemes = {
            NotificationType.PRICE_DROP: {'bg': '#d4edda', 'border': '#c3e6cb', 'text': '#155724'},
            NotificationType.STOCK_CHANGE: {'bg': '#d1ecf1', 'border': '#bee5eb', 'text': '#0c5460'},
            NotificationType.TARGET_REACHED: {'bg': '#fff3cd', 'border': '#ffeaa7', 'text': '#856404'},
            NotificationType.RATING_CHANGE: {'bg': '#e2e3e5', 'border': '#d6d8db', 'text': '#383d41'},
            NotificationType.GENERAL_ALERT: {'bg': '#f8f9fa', 'border': '#dee2e6', 'text': '#495057'}
        }
        
        colors = color_schemes.get(notification_type, color_schemes[NotificationType.GENERAL_ALERT])
        
        # Priority styling
        priority_colors = {
            NotificationPriority.LOW: '#6c757d',
            NotificationPriority.MEDIUM: '#fd7e14', 
            NotificationPriority.HIGH: '#dc3545',
            NotificationPriority.URGENT: '#dc3545'
        }
        
        priority_color = priority_colors.get(priority, '#6c757d')
        
        # Convert line breaks to HTML
        html_message = message.replace('\n', '<br>')
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; background-color: #f4f4f4;">
    <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        
        <!-- Header -->
        <div style="background-color: {colors['bg']}; border-left: 5px solid {colors['border']}; padding: 20px;">
            <h1 style="margin: 0; color: {colors['text']}; font-size: 24px;">
                {title}
            </h1>
            <div style="margin-top: 10px;">
                <span style="background-color: {priority_color}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">
                    {priority.value.upper()}
                </span>
            </div>
        </div>
        
        <!-- Content -->
        <div style="padding: 20px; color: #333;">
            <div style="font-size: 16px; line-height: 1.8;">
                {html_message}
            </div>
        </div>
        
        <!-- Footer -->
        <div style="background-color: #f8f9fa; padding: 15px; border-top: 1px solid #dee2e6; text-align: center; color: #6c757d; font-size: 12px;">
            <p style="margin: 0;">
                <strong>Smart Price Tracker</strong><br>
                Automated price monitoring system
            </p>
        </div>
        
    </div>
</body>
</html>
        """.strip()
        
        return html
    
    def send_price_drop_notification(self, product_data: Dict[str, Any]) -> bool:
        """Send price drop notification"""
        
        formatted = self.format_price_drop_message(product_data)
        
        return self.send_notification(
            formatted['title'],
            formatted['message'],
            NotificationType.PRICE_DROP,
            NotificationPriority.HIGH,
            product_data=product_data
        )
    
    def send_stock_change_notification(self, product_data: Dict[str, Any]) -> bool:
        """Send stock change notification"""
        
        formatted = self.format_stock_change_message(product_data)
        priority = NotificationPriority.HIGH if product_data.get('availability') else NotificationPriority.MEDIUM
        
        return self.send_notification(
            formatted['title'],
            formatted['message'],
            NotificationType.STOCK_CHANGE,
            priority,
            product_data=product_data
        )
    
    def send_target_reached_notification(self, product_data: Dict[str, Any]) -> bool:
        """Send target price reached notification"""
        
        formatted = self.format_target_reached_message(product_data)
        
        return self.send_notification(
            formatted['title'],
            formatted['message'],
            NotificationType.TARGET_REACHED,
            NotificationPriority.URGENT,
            product_data=product_data
        )
    
    def send_rating_change_notification(self, product_data: Dict[str, Any]) -> bool:
        """Send rating change notification"""
        
        formatted = self.format_rating_change_message(product_data)
        
        return self.send_notification(
            formatted['title'],
            formatted['message'],
            NotificationType.RATING_CHANGE,
            NotificationPriority.LOW,
            product_data=product_data
        )
    
    def add_recipient(self, email: str) -> bool:
        """Add a recipient email address"""
        
        if email not in self.recipient_emails:
            self.recipient_emails.append(email)
            self.logger.info(f"Added email recipient: {email}")
            return True
        return False
    
    def remove_recipient(self, email: str) -> bool:
        """Remove a recipient email address"""
        
        if email in self.recipient_emails:
            self.recipient_emails.remove(email)
            self.logger.info(f"Removed email recipient: {email}")
            return True
        return False
    
    def get_recipients(self) -> List[str]:
        """Get list of recipient email addresses"""
        return self.recipient_emails.copy() 