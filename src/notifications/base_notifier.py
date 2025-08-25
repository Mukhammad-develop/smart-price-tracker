from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Types of notifications"""
    PRICE_DROP = "price_drop"
    PRICE_INCREASE = "price_increase" 
    STOCK_CHANGE = "stock_change"
    TARGET_REACHED = "target_reached"
    RATING_CHANGE = "rating_change"
    GENERAL_ALERT = "general_alert"

class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class BaseNotifier(ABC):
    """Abstract base class for all notification services"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = True
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def send_notification(self, 
                         title: str, 
                         message: str, 
                         notification_type: NotificationType = NotificationType.GENERAL_ALERT,
                         priority: NotificationPriority = NotificationPriority.MEDIUM,
                         **kwargs) -> bool:
        """Send a notification"""
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the notifier is properly configured"""
        pass
    
    def format_price_drop_message(self, product_data: Dict[str, Any]) -> Dict[str, str]:
        """Format a price drop notification message"""
        
        title = f"💰 Price Drop Alert!"
        
        product_title = product_data.get('title', 'Unknown Product')[:50]
        current_price = product_data.get('current_price', 0)
        previous_price = product_data.get('previous_price', 0)
        target_price = product_data.get('target_price')
        platform = product_data.get('platform', '').title()
        url = product_data.get('url', '')
        
        # Calculate savings
        savings = previous_price - current_price if previous_price and current_price else 0
        savings_pct = (savings / previous_price * 100) if previous_price and previous_price > 0 else 0
        
        message_parts = [
            f"🛍️ {product_title}",
            f"",
            f"💸 Price dropped from ${previous_price:.2f} to ${current_price:.2f}",
            f"💰 You save: ${savings:.2f} ({savings_pct:.1f}%)",
        ]
        
        if target_price and current_price <= target_price:
            message_parts.append(f"🎯 Target price ${target_price:.2f} reached!")
        
        message_parts.extend([
            f"🏪 Platform: {platform}",
            f"🔗 {url}",
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ])
        
        return {
            'title': title,
            'message': '\n'.join(message_parts)
        }
    
    def format_stock_change_message(self, product_data: Dict[str, Any]) -> Dict[str, str]:
        """Format a stock change notification message"""
        
        product_title = product_data.get('title', 'Unknown Product')[:50]
        is_available = product_data.get('availability', False)
        platform = product_data.get('platform', '').title()
        url = product_data.get('url', '')
        current_price = product_data.get('current_price', 0)
        
        if is_available:
            title = f"✅ Back in Stock!"
            emoji = "🎉"
            status = "back in stock"
        else:
            title = f"❌ Out of Stock Alert"
            emoji = "⚠️"
            status = "out of stock"
        
        message_parts = [
            f"🛍️ {product_title}",
            f"",
            f"{emoji} This item is now {status}",
        ]
        
        if is_available and current_price:
            message_parts.append(f"💰 Current price: ${current_price:.2f}")
        
        message_parts.extend([
            f"🏪 Platform: {platform}",
            f"🔗 {url}",
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ])
        
        return {
            'title': title,
            'message': '\n'.join(message_parts)
        }
    
    def format_target_reached_message(self, product_data: Dict[str, Any]) -> Dict[str, str]:
        """Format a target price reached notification"""
        
        title = f"🎯 Target Price Reached!"
        
        product_title = product_data.get('title', 'Unknown Product')[:50]
        current_price = product_data.get('current_price', 0)
        target_price = product_data.get('target_price', 0)
        platform = product_data.get('platform', '').title()
        url = product_data.get('url', '')
        
        message_parts = [
            f"🛍️ {product_title}",
            f"",
            f"🎯 Your target price of ${target_price:.2f} has been reached!",
            f"💰 Current price: ${current_price:.2f}",
            f"🏪 Platform: {platform}",
            f"🔗 {url}",
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        return {
            'title': title,
            'message': '\n'.join(message_parts)
        }
    
    def format_rating_change_message(self, product_data: Dict[str, Any]) -> Dict[str, str]:
        """Format a rating change notification"""
        
        product_title = product_data.get('title', 'Unknown Product')[:50]
        current_rating = product_data.get('rating', 0)
        previous_rating = product_data.get('previous_rating', 0)
        review_count = product_data.get('review_count', 0)
        platform = product_data.get('platform', '').title()
        url = product_data.get('url', '')
        
        rating_change = current_rating - previous_rating if current_rating and previous_rating else 0
        
        if rating_change > 0:
            title = f"⭐ Rating Improved!"
            emoji = "📈"
            direction = "improved"
        else:
            title = f"⭐ Rating Declined"
            emoji = "📉"
            direction = "declined"
        
        message_parts = [
            f"🛍️ {product_title}",
            f"",
            f"{emoji} Rating {direction} from {previous_rating:.1f} to {current_rating:.1f}",
            f"📊 Based on {review_count} reviews",
            f"🏪 Platform: {platform}",
            f"🔗 {url}",
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ]
        
        return {
            'title': title,
            'message': '\n'.join(message_parts)
        }
    
    def format_general_message(self, title: str, content: str, product_data: Dict[str, Any] = None) -> Dict[str, str]:
        """Format a general notification message"""
        
        message_parts = [content]
        
        if product_data:
            product_title = product_data.get('title', 'Unknown Product')[:50]
            platform = product_data.get('platform', '').title()
            url = product_data.get('url', '')
            
            message_parts.extend([
                f"",
                f"🛍️ {product_title}",
                f"🏪 Platform: {platform}",
                f"🔗 {url}"
            ])
        
        message_parts.append(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return {
            'title': title,
            'message': '\n'.join(message_parts)
        }
    
    def get_priority_emoji(self, priority: NotificationPriority) -> str:
        """Get emoji for notification priority"""
        priority_emojis = {
            NotificationPriority.LOW: "ℹ️",
            NotificationPriority.MEDIUM: "⚠️",
            NotificationPriority.HIGH: "🚨",
            NotificationPriority.URGENT: "🔥"
        }
        return priority_emojis.get(priority, "📢")
    
    def should_send_notification(self, notification_type: NotificationType, product_data: Dict[str, Any] = None) -> bool:
        """Check if notification should be sent based on configuration and conditions"""
        
        if not self.enabled:
            return False
        
        if not self.is_configured():
            self.logger.warning(f"{self.__class__.__name__} is not properly configured")
            return False
        
        # Add custom logic here for rate limiting, quiet hours, etc.
        return True
    
    def test_notification(self) -> bool:
        """Send a test notification to verify configuration"""
        
        test_message = {
            'title': f"🧪 Test Notification - {self.__class__.__name__}",
            'message': f"This is a test notification sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nIf you received this, your {self.__class__.__name__} configuration is working correctly! ✅"
        }
        
        try:
            return self.send_notification(
                test_message['title'],
                test_message['message'],
                NotificationType.GENERAL_ALERT,
                NotificationPriority.LOW
            )
        except Exception as e:
            self.logger.error(f"Test notification failed: {e}")
            return False 