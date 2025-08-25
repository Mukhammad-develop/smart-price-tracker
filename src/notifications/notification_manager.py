from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from .base_notifier import BaseNotifier, NotificationType, NotificationPriority
from .email_notifier import EmailNotifier
from .telegram_notifier import TelegramNotifier
from .slack_notifier import SlackNotifier
from ..core.database import db_manager
from ..models.product import Product, PriceHistory, Alert
from ..utils.config import Config

logger = logging.getLogger(__name__)

class NotificationManager:
    """Manages all notification services and handles alert logic"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.notifiers: Dict[str, BaseNotifier] = {}
        self._initialize_notifiers()
    
    def _initialize_notifiers(self):
        """Initialize all notification services"""
        
        # Email notifier
        if self.config.is_email_configured():
            email_config = {
                'smtp_server': self.config.SMTP_SERVER,
                'smtp_port': self.config.SMTP_PORT,
                'email_address': self.config.EMAIL_ADDRESS,
                'email_password': self.config.EMAIL_PASSWORD,
                'recipient_emails': [self.config.EMAIL_ADDRESS]  # Default to sender
            }
            self.notifiers['email'] = EmailNotifier(email_config)
            logger.info("Email notifier initialized")
        
        # Telegram notifier
        if self.config.is_telegram_configured():
            telegram_config = {
                'telegram_bot_token': self.config.TELEGRAM_BOT_TOKEN,
                'telegram_chat_id': self.config.TELEGRAM_CHAT_ID
            }
            self.notifiers['telegram'] = TelegramNotifier(telegram_config)
            logger.info("Telegram notifier initialized")
        
        # Slack notifier
        if self.config.is_slack_configured():
            slack_config = {
                'slack_bot_token': self.config.SLACK_BOT_TOKEN,
                'slack_channel': self.config.SLACK_CHANNEL
            }
            self.notifiers['slack'] = SlackNotifier(slack_config)
            logger.info("Slack notifier initialized")
        
        logger.info(f"Initialized {len(self.notifiers)} notification services: {list(self.notifiers.keys())}")
    
    def send_notification(self, title: str, message: str, 
                         notification_type: NotificationType = NotificationType.GENERAL_ALERT,
                         priority: NotificationPriority = NotificationPriority.MEDIUM,
                         channels: List[str] = None,
                         product_data: Dict[str, Any] = None) -> Dict[str, bool]:
        """Send notification through specified channels"""
        
        if not channels:
            channels = list(self.notifiers.keys())
        
        results = {}
        
        for channel in channels:
            if channel in self.notifiers:
                try:
                    success = self.notifiers[channel].send_notification(
                        title, message, notification_type, priority, 
                        product_data=product_data
                    )
                    results[channel] = success
                    
                    if success:
                        logger.info(f"Notification sent successfully via {channel}")
                    else:
                        logger.warning(f"Failed to send notification via {channel}")
                        
                except Exception as e:
                    logger.error(f"Error sending notification via {channel}: {e}")
                    results[channel] = False
            else:
                logger.warning(f"Notifier '{channel}' not available")
                results[channel] = False
        
        return results
    
    def check_and_send_alerts(self, product_id: int, previous_data: Dict[str, Any], 
                             current_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for alert conditions and send notifications"""
        
        alerts_sent = []
        
        with db_manager.get_session() as session:
            product = session.query(Product).filter(Product.id == product_id).first()
            
            if not product or not product.notification_enabled:
                return alerts_sent
            
            # Prepare product data for notifications
            product_notification_data = {
                'id': product.id,
                'title': product.title,
                'url': product.url,
                'platform': product.platform,
                'current_price': current_data.get('current_price'),
                'previous_price': previous_data.get('current_price'),
                'target_price': product.target_price,
                'availability': current_data.get('availability'),
                'previous_availability': previous_data.get('availability'),
                'rating': current_data.get('rating'),
                'previous_rating': previous_data.get('rating'),
                'review_count': current_data.get('review_count'),
                'seller': current_data.get('seller'),
                'image_url': product.image_url
            }
            
            # Check price drop alert
            if self._should_send_price_drop_alert(product, previous_data, current_data):
                alert_result = self._send_price_drop_alert(product_notification_data)
                alerts_sent.append(alert_result)
            
            # Check target price reached
            if self._should_send_target_reached_alert(product, current_data):
                alert_result = self._send_target_reached_alert(product_notification_data)
                alerts_sent.append(alert_result)
            
            # Check stock change alert
            if self._should_send_stock_change_alert(previous_data, current_data):
                alert_result = self._send_stock_change_alert(product_notification_data)
                alerts_sent.append(alert_result)
            
            # Check rating change alert (if enabled)
            if product.track_rating and self._should_send_rating_change_alert(previous_data, current_data):
                alert_result = self._send_rating_change_alert(product_notification_data)
                alerts_sent.append(alert_result)
        
        return alerts_sent
    
    def _should_send_price_drop_alert(self, product: Product, previous_data: Dict, current_data: Dict) -> bool:
        """Check if price drop alert should be sent"""
        
        prev_price = previous_data.get('current_price')
        curr_price = current_data.get('current_price')
        
        if not prev_price or not curr_price:
            return False
        
        # Price must have dropped by at least 1% or $1
        price_drop = prev_price - curr_price
        price_drop_pct = (price_drop / prev_price) * 100 if prev_price > 0 else 0
        
        return price_drop > 0 and (price_drop >= 1.0 or price_drop_pct >= 1.0)
    
    def _should_send_target_reached_alert(self, product: Product, current_data: Dict) -> bool:
        """Check if target price reached alert should be sent"""
        
        if not product.target_price:
            return False
        
        curr_price = current_data.get('current_price')
        if not curr_price:
            return False
        
        return curr_price <= product.target_price
    
    def _should_send_stock_change_alert(self, previous_data: Dict, current_data: Dict) -> bool:
        """Check if stock change alert should be sent"""
        
        prev_availability = previous_data.get('availability')
        curr_availability = current_data.get('availability')
        
        # Only alert on actual changes
        return prev_availability is not None and prev_availability != curr_availability
    
    def _should_send_rating_change_alert(self, previous_data: Dict, current_data: Dict) -> bool:
        """Check if rating change alert should be sent"""
        
        prev_rating = previous_data.get('rating')
        curr_rating = current_data.get('rating')
        
        if not prev_rating or not curr_rating:
            return False
        
        # Alert on rating changes of 0.2 or more
        rating_change = abs(curr_rating - prev_rating)
        return rating_change >= 0.2
    
    def _send_price_drop_alert(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send price drop alert"""
        
        results = {}
        
        for channel, notifier in self.notifiers.items():
            try:
                if hasattr(notifier, 'send_price_drop_notification'):
                    success = notifier.send_price_drop_notification(product_data)
                else:
                    formatted = notifier.format_price_drop_message(product_data)
                    success = notifier.send_notification(
                        formatted['title'], formatted['message'],
                        NotificationType.PRICE_DROP, NotificationPriority.HIGH
                    )
                results[channel] = success
            except Exception as e:
                logger.error(f"Error sending price drop alert via {channel}: {e}")
                results[channel] = False
        
        return {
            'type': 'price_drop',
            'product_id': product_data.get('id'),
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _send_target_reached_alert(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send target price reached alert"""
        
        results = {}
        
        for channel, notifier in self.notifiers.items():
            try:
                if hasattr(notifier, 'send_target_reached_notification'):
                    success = notifier.send_target_reached_notification(product_data)
                else:
                    formatted = notifier.format_target_reached_message(product_data)
                    success = notifier.send_notification(
                        formatted['title'], formatted['message'],
                        NotificationType.TARGET_REACHED, NotificationPriority.URGENT
                    )
                results[channel] = success
            except Exception as e:
                logger.error(f"Error sending target reached alert via {channel}: {e}")
                results[channel] = False
        
        return {
            'type': 'target_reached',
            'product_id': product_data.get('id'),
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _send_stock_change_alert(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send stock change alert"""
        
        results = {}
        
        for channel, notifier in self.notifiers.items():
            try:
                if hasattr(notifier, 'send_stock_change_notification'):
                    success = notifier.send_stock_change_notification(product_data)
                else:
                    formatted = notifier.format_stock_change_message(product_data)
                    priority = NotificationPriority.HIGH if product_data.get('availability') else NotificationPriority.MEDIUM
                    success = notifier.send_notification(
                        formatted['title'], formatted['message'],
                        NotificationType.STOCK_CHANGE, priority
                    )
                results[channel] = success
            except Exception as e:
                logger.error(f"Error sending stock change alert via {channel}: {e}")
                results[channel] = False
        
        return {
            'type': 'stock_change',
            'product_id': product_data.get('id'),
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _send_rating_change_alert(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send rating change alert"""
        
        results = {}
        
        for channel, notifier in self.notifiers.items():
            try:
                if hasattr(notifier, 'send_rating_change_notification'):
                    success = notifier.send_rating_change_notification(product_data)
                else:
                    formatted = notifier.format_rating_change_message(product_data)
                    success = notifier.send_notification(
                        formatted['title'], formatted['message'],
                        NotificationType.RATING_CHANGE, NotificationPriority.LOW
                    )
                results[channel] = success
            except Exception as e:
                logger.error(f"Error sending rating change alert via {channel}: {e}")
                results[channel] = False
        
        return {
            'type': 'rating_change',
            'product_id': product_data.get('id'),
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def send_daily_summary(self, analytics_data: Dict[str, Any]) -> Dict[str, bool]:
        """Send daily summary notification"""
        
        title = "📊 Daily Price Tracking Summary"
        
        total_products = analytics_data.get('total_products', 0)
        products_with_changes = analytics_data.get('products_with_changes', 0)
        total_checks = analytics_data.get('total_price_checks', 0)
        
        message_parts = [
            f"📈 Daily Summary for {datetime.now().strftime('%Y-%m-%d')}",
            "",
            f"📦 Products tracked: {total_products}",
            f"🔄 Price checks performed: {total_checks}",
            f"📊 Products with changes: {products_with_changes}",
        ]
        
        # Add biggest changes
        biggest_drop = analytics_data.get('biggest_price_drop')
        if biggest_drop:
            savings = biggest_drop.get('first_price', 0) - biggest_drop.get('last_price', 0)
            message_parts.append(f"💰 Biggest drop: ${savings:.2f} on {biggest_drop.get('product_title', 'Unknown')[:30]}...")
        
        biggest_increase = analytics_data.get('biggest_price_increase')
        if biggest_increase:
            increase = biggest_increase.get('last_price', 0) - biggest_increase.get('first_price', 0)
            message_parts.append(f"📈 Biggest increase: ${increase:.2f} on {biggest_increase.get('product_title', 'Unknown')[:30]}...")
        
        # Platform breakdown
        platforms = analytics_data.get('platform_breakdown', {})
        if platforms:
            message_parts.append("")
            message_parts.append("🏪 Platform breakdown:")
            for platform, count in platforms.items():
                message_parts.append(f"  • {platform.title()}: {count}")
        
        message_parts.append("")
        message_parts.append("💡 Keep tracking for the best deals!")
        
        message = '\n'.join(message_parts)
        
        return self.send_notification(
            title, message, 
            NotificationType.GENERAL_ALERT, 
            NotificationPriority.LOW
        )
    
    def test_all_notifications(self) -> Dict[str, bool]:
        """Test all configured notification services"""
        
        results = {}
        
        for channel, notifier in self.notifiers.items():
            try:
                success = notifier.test_notification()
                results[channel] = success
                
                if success:
                    logger.info(f"Test notification successful for {channel}")
                else:
                    logger.warning(f"Test notification failed for {channel}")
                    
            except Exception as e:
                logger.error(f"Error testing {channel} notification: {e}")
                results[channel] = False
        
        return results
    
    def get_notification_status(self) -> Dict[str, Any]:
        """Get status of all notification services"""
        
        status = {
            'total_services': len(self.notifiers),
            'configured_services': list(self.notifiers.keys()),
            'service_status': {}
        }
        
        for channel, notifier in self.notifiers.items():
            status['service_status'][channel] = {
                'configured': notifier.is_configured(),
                'enabled': notifier.enabled,
                'class': notifier.__class__.__name__
            }
        
        return status
    
    def enable_notifications(self, channels: List[str] = None) -> Dict[str, bool]:
        """Enable notifications for specified channels"""
        
        if not channels:
            channels = list(self.notifiers.keys())
        
        results = {}
        
        for channel in channels:
            if channel in self.notifiers:
                self.notifiers[channel].enabled = True
                results[channel] = True
                logger.info(f"Enabled notifications for {channel}")
            else:
                results[channel] = False
                logger.warning(f"Channel '{channel}' not found")
        
        return results
    
    def disable_notifications(self, channels: List[str] = None) -> Dict[str, bool]:
        """Disable notifications for specified channels"""
        
        if not channels:
            channels = list(self.notifiers.keys())
        
        results = {}
        
        for channel in channels:
            if channel in self.notifiers:
                self.notifiers[channel].enabled = False
                results[channel] = True
                logger.info(f"Disabled notifications for {channel}")
            else:
                results[channel] = False
                logger.warning(f"Channel '{channel}' not found")
        
        return results
    
    def add_custom_alert(self, product_id: int, alert_type: str, condition_value: float,
                        notification_methods: List[str] = None) -> bool:
        """Add custom alert for a product"""
        
        if not notification_methods:
            notification_methods = list(self.notifiers.keys())
        
        with db_manager.get_session() as session:
            alert = Alert(
                product_id=product_id,
                alert_type=alert_type,
                condition_value=condition_value,
                notification_methods=','.join(notification_methods),
                is_active=True
            )
            
            session.add(alert)
            session.commit()
            
            logger.info(f"Added custom alert for product {product_id}: {alert_type} = {condition_value}")
            return True 