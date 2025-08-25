import os
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration management for the price tracker"""
    
    def __init__(self):
        # Database
        self.DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/price_tracker.db')
        
        # Google Sheets
        self.GOOGLE_SHEETS_CREDENTIALS = os.getenv('GOOGLE_SHEETS_CREDENTIALS', 'config/google_credentials.json')
        self.GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID')
        
        # Email Configuration
        self.SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
        self.EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
        self.EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
        
        # Telegram Configuration
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        self.TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
        
        # Slack Configuration
        self.SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
        self.SLACK_CHANNEL = os.getenv('SLACK_CHANNEL', '#price-alerts')
        
        # Proxy Configuration
        self.PROXY_LIST = os.getenv('PROXY_LIST', '')
        self.USE_PROXY = os.getenv('USE_PROXY', 'false').lower() == 'true'
        
        # Scraping Configuration
        self.REQUEST_DELAY_MIN = float(os.getenv('REQUEST_DELAY_MIN', '1'))
        self.REQUEST_DELAY_MAX = float(os.getenv('REQUEST_DELAY_MAX', '3'))
        self.MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
        
        # Scheduling Configuration
        self.TRACKING_INTERVAL_HOURS = int(os.getenv('TRACKING_INTERVAL_HOURS', '24'))
        self.QUICK_CHECK_INTERVAL_HOURS = int(os.getenv('QUICK_CHECK_INTERVAL_HOURS', '4'))
        
        # Logging Configuration
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FILE = os.getenv('LOG_FILE', 'logs/price_tracker.log')
    
    def get_proxy_list(self) -> Optional[List[str]]:
        """Get list of proxies"""
        if not self.PROXY_LIST:
            return None
        return [proxy.strip() for proxy in self.PROXY_LIST.split(',') if proxy.strip()]
    
    def is_email_configured(self) -> bool:
        """Check if email notifications are properly configured"""
        return bool(self.EMAIL_ADDRESS and self.EMAIL_PASSWORD)
    
    def is_telegram_configured(self) -> bool:
        """Check if Telegram notifications are properly configured"""
        return bool(self.TELEGRAM_BOT_TOKEN and self.TELEGRAM_CHAT_ID)
    
    def is_slack_configured(self) -> bool:
        """Check if Slack notifications are properly configured"""
        return bool(self.SLACK_BOT_TOKEN)
    
    def is_google_sheets_configured(self) -> bool:
        """Check if Google Sheets integration is properly configured"""
        return bool(self.GOOGLE_SHEETS_ID and os.path.exists(self.GOOGLE_SHEETS_CREDENTIALS))
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of warnings/errors"""
        warnings = []
        
        if not self.is_email_configured():
            warnings.append("Email notifications not configured")
        
        if not self.is_telegram_configured():
            warnings.append("Telegram notifications not configured")
        
        if not self.is_slack_configured():
            warnings.append("Slack notifications not configured")
        
        if not self.is_google_sheets_configured():
            warnings.append("Google Sheets integration not configured")
        
        if self.USE_PROXY and not self.get_proxy_list():
            warnings.append("Proxy enabled but no proxy list provided")
        
        return warnings 