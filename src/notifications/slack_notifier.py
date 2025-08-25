from typing import Dict, Any, List, Optional
import logging
import requests
import json
from datetime import datetime

from .base_notifier import BaseNotifier, NotificationType, NotificationPriority

logger = logging.getLogger(__name__)

class SlackNotifier(BaseNotifier):
    """Slack notification service using Slack Bot API"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.bot_token = config.get('slack_bot_token')
        self.channel = config.get('slack_channel', '#general')
        
        # Ensure channel starts with #
        if self.channel and not self.channel.startswith('#'):
            self.channel = f"#{self.channel}"
        
        if self.bot_token:
            self.api_url = "https://slack.com/api"
            self.headers = {
                'Authorization': f'Bearer {self.bot_token}',
                'Content-Type': 'application/json'
            }
    
    def is_configured(self) -> bool:
        """Check if Slack notifier is properly configured"""
        return bool(self.bot_token and self.channel)
    
    def send_notification(self, 
                         title: str, 
                         message: str, 
                         notification_type: NotificationType = NotificationType.GENERAL_ALERT,
                         priority: NotificationPriority = NotificationPriority.MEDIUM,
                         **kwargs) -> bool:
        """Send Slack notification"""
        
        if not self.should_send_notification(notification_type, kwargs.get('product_data')):
            return False
        
        try:
            # Create Slack message blocks
            blocks = self._create_message_blocks(title, message, notification_type, priority)
            
            # Send message
            response = self._send_slack_message(blocks)
            
            if response and response.get('ok'):
                self.logger.info(f"Slack notification sent successfully")
                return True
            else:
                error_msg = response.get('error', 'Unknown error') if response else 'No response'
                self.logger.error(f"Failed to send Slack notification: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {e}")
            return False
    
    def _send_slack_message(self, blocks: List[Dict]) -> Optional[Dict]:
        """Send message to Slack using chat.postMessage API"""
        
        url = f"{self.api_url}/chat.postMessage"
        
        payload = {
            'channel': self.channel,
            'blocks': blocks
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            return response.json()
        except Exception as e:
            self.logger.error(f"Error sending Slack message: {e}")
            return None
    
    def _create_message_blocks(self, title: str, message: str, 
                              notification_type: NotificationType, 
                              priority: NotificationPriority) -> List[Dict]:
        """Create Slack message blocks with rich formatting"""
        
        # Color based on notification type and priority
        colors = {
            NotificationType.PRICE_DROP: "#28a745",  # Green
            NotificationType.STOCK_CHANGE: "#17a2b8",  # Blue
            NotificationType.TARGET_REACHED: "#ffc107",  # Yellow
            NotificationType.RATING_CHANGE: "#6c757d",  # Gray
            NotificationType.GENERAL_ALERT: "#007bff"  # Blue
        }
        
        priority_colors = {
            NotificationPriority.LOW: "#6c757d",
            NotificationPriority.MEDIUM: "#fd7e14",
            NotificationPriority.HIGH: "#dc3545",
            NotificationPriority.URGENT: "#dc3545"
        }
        
        # Use priority color if high priority, otherwise use notification type color
        if priority in [NotificationPriority.HIGH, NotificationPriority.URGENT]:
            color = priority_colors[priority]
        else:
            color = colors.get(notification_type, colors[NotificationType.GENERAL_ALERT])
        
        # Priority emoji
        priority_emoji = self.get_priority_emoji(priority)
        
        # Create blocks
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{priority_emoji} {title}*"
                }
            }
        ]
        
        # Add priority indicator for high priority notifications
        if priority in [NotificationPriority.HIGH, NotificationPriority.URGENT]:
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Priority: {priority.value.upper()}*"
                    }
                ]
            })
        
        # Format message content
        formatted_message = self._format_slack_message(message)
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": formatted_message
            }
        })
        
        # Add divider and footer
        blocks.extend([
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Smart Price Tracker • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ])
        
        return blocks
    
    def _format_slack_message(self, message: str) -> str:
        """Format message for Slack markdown"""
        
        lines = message.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append('')
                continue
            
            # Format URLs
            if line.startswith('🔗'):
                url = line.replace('🔗 ', '').strip()
                formatted_lines.append(f"<{url}|🔗 View Product>")
            # Format price information with code blocks
            elif '→' in line and ('$' in line or 'Price' in line):
                formatted_lines.append(f"`{line}`")
            # Format platform/category info in italics
            elif line.startswith('🏪') or line.startswith('📦'):
                formatted_lines.append(f"_{line}_")
            # Bold important information
            elif line.startswith('🎯') or line.startswith('💰'):
                formatted_lines.append(f"*{line}*")
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
    
    def send_rich_notification(self, title: str, product_data: Dict[str, Any], 
                              notification_type: NotificationType) -> bool:
        """Send rich notification with product details and image"""
        
        if not self.is_configured():
            return False
        
        try:
            # Create rich blocks with product information
            blocks = self._create_rich_product_blocks(title, product_data, notification_type)
            
            response = self._send_slack_message(blocks)
            
            if response and response.get('ok'):
                self.logger.info("Slack rich notification sent successfully")
                return True
            else:
                error_msg = response.get('error', 'Unknown error') if response else 'No response'
                self.logger.error(f"Failed to send Slack rich notification: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending Slack rich notification: {e}")
            return False
    
    def _create_rich_product_blocks(self, title: str, product_data: Dict[str, Any], 
                                   notification_type: NotificationType) -> List[Dict]:
        """Create rich message blocks with product details"""
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": title
                }
            }
        ]
        
        # Product information section
        product_title = product_data.get('title', 'Unknown Product')
        current_price = product_data.get('current_price', 0)
        platform = product_data.get('platform', '').title()
        rating = product_data.get('rating', 0)
        availability = product_data.get('availability', False)
        
        # Create fields for product details
        fields = []
        
        if current_price:
            fields.append({
                "type": "mrkdwn",
                "text": f"*Price:*\n${current_price:.2f}"
            })
        
        if platform:
            fields.append({
                "type": "mrkdwn",
                "text": f"*Platform:*\n{platform}"
            })
        
        if rating:
            fields.append({
                "type": "mrkdwn",
                "text": f"*Rating:*\n⭐ {rating:.1f}"
            })
        
        availability_text = "✅ In Stock" if availability else "❌ Out of Stock"
        fields.append({
            "type": "mrkdwn",
            "text": f"*Availability:*\n{availability_text}"
        })
        
        # Add product section
        product_block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{product_title[:100]}*"
            }
        }
        
        # Add product image if available
        image_url = product_data.get('image_url')
        if image_url:
            product_block["accessory"] = {
                "type": "image",
                "image_url": image_url,
                "alt_text": "Product Image"
            }
        
        blocks.append(product_block)
        
        # Add fields section
        if fields:
            blocks.append({
                "type": "section",
                "fields": fields
            })
        
        # Add action buttons
        product_url = product_data.get('url')
        if product_url:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Product"
                        },
                        "url": product_url,
                        "style": "primary"
                    }
                ]
            })
        
        return blocks
    
    def get_bot_info(self) -> Optional[Dict]:
        """Get information about the bot"""
        
        if not self.bot_token:
            return None
        
        url = f"{self.api_url}/auth.test"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                return result
            else:
                self.logger.error(f"Failed to get bot info: {result.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting bot info: {e}")
            return None
    
    def test_notification(self) -> bool:
        """Send a test notification to verify configuration"""
        
        if not self.is_configured():
            self.logger.error("Slack notifier is not configured")
            return False
        
        # Get bot info for test
        bot_info = self.get_bot_info()
        bot_name = bot_info.get('user', 'Unknown') if bot_info else 'Unknown'
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🧪 Test Notification - Slack"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"This is a test notification sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n*Bot Information:*\n• Name: {bot_name}\n• Channel: {self.channel}\n\nIf you received this, your Slack configuration is working correctly! ✅"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Smart Price Tracker"
                    }
                ]
            }
        ]
        
        try:
            response = self._send_slack_message(blocks)
            
            if response and response.get('ok'):
                self.logger.info("Slack test notification sent successfully")
                return True
            else:
                error_msg = response.get('error', 'Unknown error') if response else 'No response'
                self.logger.error(f"Slack test notification failed: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"Slack test notification error: {e}")
            return False 