import asyncio
from typing import Dict, Any, List, Optional
import logging
import requests
import json
from datetime import datetime

from .base_notifier import BaseNotifier, NotificationType, NotificationPriority

logger = logging.getLogger(__name__)

class TelegramNotifier(BaseNotifier):
    """Telegram notification service using Bot API"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.bot_token = config.get('telegram_bot_token')
        self.chat_id = config.get('telegram_chat_id')
        self.parse_mode = 'HTML'  # Support for HTML formatting
        
        if self.bot_token:
            self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def is_configured(self) -> bool:
        """Check if Telegram notifier is properly configured"""
        return bool(self.bot_token and self.chat_id)
    
    def send_notification(self, 
                         title: str, 
                         message: str, 
                         notification_type: NotificationType = NotificationType.GENERAL_ALERT,
                         priority: NotificationPriority = NotificationPriority.MEDIUM,
                         **kwargs) -> bool:
        """Send Telegram notification"""
        
        if not self.should_send_notification(notification_type, kwargs.get('product_data')):
            return False
        
        try:
            # Format message for Telegram
            formatted_message = self._format_telegram_message(title, message, notification_type, priority)
            
            # Send message
            response = self._send_telegram_message(formatted_message)
            
            if response and response.get('ok'):
                self.logger.info(f"Telegram notification sent successfully")
                return True
            else:
                error_msg = response.get('description', 'Unknown error') if response else 'No response'
                self.logger.error(f"Failed to send Telegram notification: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send Telegram notification: {e}")
            return False
    
    def _send_telegram_message(self, message: str, disable_web_page_preview: bool = False) -> Optional[Dict]:
        """Send message to Telegram using Bot API"""
        
        url = f"{self.api_url}/sendMessage"
        
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': self.parse_mode,
            'disable_web_page_preview': disable_web_page_preview
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            return response.json()
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
            return None
    
    def _format_telegram_message(self, title: str, message: str, 
                                notification_type: NotificationType, 
                                priority: NotificationPriority) -> str:
        """Format message for Telegram with HTML markup"""
        
        # Priority emoji
        priority_emoji = self.get_priority_emoji(priority)
        
        # Format title with HTML
        html_title = f"<b>{priority_emoji} {title}</b>"
        
        # Convert message to HTML format
        html_message = self._convert_to_html(message)
        
        # Add priority indicator if high priority
        priority_text = ""
        if priority in [NotificationPriority.HIGH, NotificationPriority.URGENT]:
            priority_text = f"\n<i>Priority: {priority.value.upper()}</i>"
        
        return f"{html_title}\n\n{html_message}{priority_text}"
    
    def _convert_to_html(self, message: str) -> str:
        """Convert message formatting to Telegram HTML"""
        
        # Replace URLs with clickable links
        import re
        
        # Find URLs and make them clickable
        url_pattern = r'(https?://[^\s]+)'
        message = re.sub(url_pattern, r'<a href="\1">🔗 View Product</a>', message)
        
        # Format emojis and special characters
        lines = message.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('')
                continue
                
            # Format price information
            if '→' in line and ('$' in line or 'Price' in line):
                formatted_lines.append(f"<code>{line}</code>")
            # Format platform/category info
            elif line.startswith('🏪') or line.startswith('📦'):
                formatted_lines.append(f"<i>{line}</i>")
            # Format timestamps
            elif line.startswith('⏰'):
                formatted_lines.append(f"<i>{line}</i>")
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
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
    
    def send_photo_notification(self, photo_url: str, caption: str) -> bool:
        """Send notification with product image"""
        
        if not self.is_configured():
            return False
        
        url = f"{self.api_url}/sendPhoto"
        
        payload = {
            'chat_id': self.chat_id,
            'photo': photo_url,
            'caption': caption,
            'parse_mode': self.parse_mode
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            result = response.json()
            
            if result.get('ok'):
                self.logger.info("Telegram photo notification sent successfully")
                return True
            else:
                self.logger.error(f"Failed to send Telegram photo: {result.get('description', 'Unknown error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending Telegram photo: {e}")
            return False
    
    def get_bot_info(self) -> Optional[Dict]:
        """Get information about the bot"""
        
        if not self.bot_token:
            return None
        
        url = f"{self.api_url}/getMe"
        
        try:
            response = requests.get(url, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                return result.get('result')
            else:
                self.logger.error(f"Failed to get bot info: {result.get('description', 'Unknown error')}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting bot info: {e}")
            return None
    
    def get_chat_info(self) -> Optional[Dict]:
        """Get information about the chat"""
        
        if not self.is_configured():
            return None
        
        url = f"{self.api_url}/getChat"
        
        payload = {
            'chat_id': self.chat_id
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                return result.get('result')
            else:
                self.logger.error(f"Failed to get chat info: {result.get('description', 'Unknown error')}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting chat info: {e}")
            return None
    
    def test_notification(self) -> bool:
        """Send a test notification to verify configuration"""
        
        if not self.is_configured():
            self.logger.error("Telegram notifier is not configured")
            return False
        
        # Get bot info for test
        bot_info = self.get_bot_info()
        bot_name = bot_info.get('first_name', 'Unknown') if bot_info else 'Unknown'
        
        test_message = f"""
🧪 <b>Test Notification - Telegram</b>

This is a test notification sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<b>Bot Information:</b>
• Name: {bot_name}
• Chat ID: {self.chat_id}

If you received this, your Telegram configuration is working correctly! ✅

<i>Smart Price Tracker</i>
        """.strip()
        
        try:
            response = self._send_telegram_message(test_message)
            
            if response and response.get('ok'):
                self.logger.info("Telegram test notification sent successfully")
                return True
            else:
                error_msg = response.get('description', 'Unknown error') if response else 'No response'
                self.logger.error(f"Telegram test notification failed: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"Telegram test notification error: {e}")
            return False 