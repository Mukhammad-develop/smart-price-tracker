from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import requests
from bs4 import BeautifulSoup
import time
import random
from fake_useragent import UserAgent
import logging
from urllib.parse import urlparse

class BaseScraper(ABC):
    """Abstract base class for all platform scrapers"""
    
    def __init__(self, use_proxy: bool = False, proxy_list: Optional[List[str]] = None):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.use_proxy = use_proxy
        self.proxy_list = proxy_list or []
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Default headers
        self.default_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def get_random_user_agent(self) -> str:
        """Get a random user agent string"""
        try:
            return self.ua.random
        except Exception:
            # Fallback user agents
            fallback_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            ]
            return random.choice(fallback_agents)
    
    def get_random_proxy(self) -> Optional[Dict[str, str]]:
        """Get a random proxy from the proxy list"""
        if not self.use_proxy or not self.proxy_list:
            return None
        
        proxy = random.choice(self.proxy_list)
        return {
            'http': f'http://{proxy}',
            'https': f'https://{proxy}'
        }
    
    def make_request(self, url: str, max_retries: int = 3, delay_range: tuple = (1, 3)) -> Optional[requests.Response]:
        """Make HTTP request with retry logic and anti-bot measures"""
        
        for attempt in range(max_retries):
            try:
                # Set random user agent
                headers = self.default_headers.copy()
                headers['User-Agent'] = self.get_random_user_agent()
                
                # Get proxy if enabled
                proxies = self.get_random_proxy()
                
                # Add random delay
                delay = random.uniform(delay_range[0], delay_range[1])
                time.sleep(delay)
                
                response = self.session.get(
                    url,
                    headers=headers,
                    proxies=proxies,
                    timeout=30,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Rate limited
                    self.logger.warning(f"Rate limited on attempt {attempt + 1}, waiting longer...")
                    time.sleep(delay * 2)
                else:
                    self.logger.warning(f"HTTP {response.status_code} on attempt {attempt + 1}")
                    
            except Exception as e:
                self.logger.error(f"Request failed on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(delay * (attempt + 1))
        
        return None
    
    @abstractmethod
    def extract_product_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract product information from the given URL"""
        pass
    
    @abstractmethod
    def is_valid_url(self, url: str) -> bool:
        """Check if the URL is valid for this platform"""
        pass
    
    def clean_price(self, price_text: str) -> Optional[float]:
        """Clean and convert price text to float"""
        if not price_text:
            return None
        
        # Remove currency symbols and whitespace
        import re
        price_clean = re.sub(r'[^\d.,]', '', price_text.strip())
        
        # Handle different decimal separators
        if ',' in price_clean and '.' in price_clean:
            # Assume comma is thousands separator
            price_clean = price_clean.replace(',', '')
        elif ',' in price_clean:
            # Could be decimal separator in some locales
            if len(price_clean.split(',')[-1]) <= 2:
                price_clean = price_clean.replace(',', '.')
        
        try:
            return float(price_clean)
        except ValueError:
            return None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        cleaned = ' '.join(text.strip().split())
        return cleaned
    
    def extract_rating(self, rating_text: str) -> Optional[float]:
        """Extract numeric rating from text"""
        if not rating_text:
            return None
        
        import re
        # Look for patterns like "4.5 out of 5" or "4.5/5" or just "4.5"
        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
        if rating_match:
            try:
                rating = float(rating_match.group(1))
                # Normalize to 5-point scale if needed
                if rating > 5:
                    rating = rating / 2  # Assume 10-point scale
                return min(rating, 5.0)
            except ValueError:
                pass
        
        return None
    
    def extract_review_count(self, review_text: str) -> Optional[int]:
        """Extract review count from text"""
        if not review_text:
            return None
        
        import re
        # Look for numbers, handling commas
        review_match = re.search(r'([\d,]+)', review_text.replace(',', ''))
        if review_match:
            try:
                return int(review_match.group(1))
            except ValueError:
                pass
        
        return None 