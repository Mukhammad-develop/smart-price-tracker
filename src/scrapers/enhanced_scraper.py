import random
import time
import json
import base64
from typing import Dict, List, Optional, Any, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc
import requests
import logging
from datetime import datetime, timedelta
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class EnhancedScraper(BaseScraper):
    """Enhanced scraper with advanced anti-bot protection and stealth features"""
    
    def __init__(self, use_proxy: bool = False, proxy_list: Optional[List[str]] = None,
                 use_selenium: bool = False, headless: bool = True):
        super().__init__(use_proxy, proxy_list)
        
        self.use_selenium = use_selenium
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        
        # Advanced anti-bot settings
        self.request_delays = {
            'min': 2,
            'max': 8,
            'between_pages': (10, 30)
        }
        
        # Behavioral patterns
        self.mouse_movements = True
        self.scroll_behavior = True
        self.typing_delays = True
        
        # Session management
        self.session_duration_limit = timedelta(minutes=45)  # Rotate sessions every 45 min
        self.session_start_time = datetime.utcnow()
        self.request_count = 0
        self.max_requests_per_session = 100
        
        # Browser fingerprint rotation
        self.browser_profiles = self._load_browser_profiles()
        self.current_profile_index = 0
        
        # Captcha detection and handling
        self.captcha_selectors = [
            'img[src*="captcha"]',
            '.captcha',
            '#captcha',
            '[class*="recaptcha"]',
            'iframe[src*="recaptcha"]'
        ]
        
        logger.info("EnhancedScraper initialized with advanced anti-bot protection")
    
    def _load_browser_profiles(self) -> List[Dict[str, Any]]:
        """Load realistic browser profiles for fingerprint rotation"""
        
        return [
            {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'viewport': (1920, 1080),
                'language': 'en-US,en;q=0.9',
                'timezone': 'America/New_York',
                'platform': 'Win32'
            },
            {
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'viewport': (1440, 900),
                'language': 'en-US,en;q=0.9',
                'timezone': 'America/Los_Angeles',
                'platform': 'MacIntel'
            },
            {
                'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'viewport': (1920, 1080),
                'language': 'en-US,en;q=0.9',
                'timezone': 'America/Chicago',
                'platform': 'Linux x86_64'
            },
            {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
                'viewport': (1366, 768),
                'language': 'en-US,en;q=0.5',
                'timezone': 'America/Denver',
                'platform': 'Win32'
            }
        ]
    
    def _should_rotate_session(self) -> bool:
        """Check if session should be rotated"""
        
        session_age = datetime.utcnow() - self.session_start_time
        return (session_age > self.session_duration_limit or 
                self.request_count > self.max_requests_per_session)
    
    def _rotate_session(self):
        """Rotate browser session and fingerprint"""
        
        if self.driver:
            self.driver.quit()
            self.driver = None
        
        # Rotate to next browser profile
        self.current_profile_index = (self.current_profile_index + 1) % len(self.browser_profiles)
        
        # Reset session counters
        self.session_start_time = datetime.utcnow()
        self.request_count = 0
        
        # Wait before starting new session
        time.sleep(random.uniform(30, 120))
        
        logger.info(f"Rotated to browser profile {self.current_profile_index}")
    
    def _get_selenium_driver(self) -> webdriver.Chrome:
        """Create a stealth Selenium WebDriver with current profile"""
        
        if self.driver and not self._should_rotate_session():
            return self.driver
        
        if self._should_rotate_session():
            self._rotate_session()
        
        profile = self.browser_profiles[self.current_profile_index]
        
        # Use undetected-chromedriver for better stealth
        options = uc.ChromeOptions()
        
        if self.headless:
            options.add_argument('--headless=new')
        
        # Stealth options
        options.add_argument(f'--user-agent={profile["user_agent"]}')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')  # Faster loading
        options.add_argument('--disable-javascript')  # For some sites
        
        # Viewport and window size
        options.add_argument(f'--window-size={profile["viewport"][0]},{profile["viewport"][1]}')
        
        # Proxy configuration
        if self.use_proxy and self.proxy_list:
            proxy = random.choice(self.proxy_list)
            options.add_argument(f'--proxy-server={proxy}')
        
        # Additional stealth preferences
        prefs = {
            "profile.default_content_setting_values": {
                "notifications": 2,
                "media_stream": 2,
            },
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.images": 2
        }
        options.add_experimental_option("prefs", prefs)
        
        try:
            # Create undetected Chrome driver
            self.driver = uc.Chrome(options=options, version_main=None)
            
            # Execute stealth scripts
            self._execute_stealth_scripts()
            
            # Set realistic viewport
            self.driver.set_window_size(*profile["viewport"])
            
            logger.info("Created stealth Selenium driver")
            return self.driver
            
        except Exception as e:
            logger.error(f"Failed to create Selenium driver: {e}")
            # Fallback to regular requests
            self.use_selenium = False
            return None
    
    def _execute_stealth_scripts(self):
        """Execute JavaScript to make browser more human-like"""
        
        if not self.driver:
            return
        
        # Remove webdriver property
        self.driver.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        # Mock plugins
        self.driver.execute_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
        """)
        
        # Mock languages
        self.driver.execute_script("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)
        
        # Override permissions
        self.driver.execute_script("""
            const originalQuery = window.navigator.permissions.query;
            return window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
    
    def _human_like_delay(self, action_type: str = 'default'):
        """Add human-like delays between actions"""
        
        delays = {
            'default': (1, 3),
            'typing': (0.1, 0.3),
            'mouse_move': (0.5, 1.5),
            'page_load': (3, 8),
            'between_requests': (2, 6)
        }
        
        min_delay, max_delay = delays.get(action_type, delays['default'])
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def _simulate_human_behavior(self):
        """Simulate human browsing behavior"""
        
        if not self.driver:
            return
        
        try:
            # Random mouse movements
            if self.mouse_movements:
                actions = ActionChains(self.driver)
                for _ in range(random.randint(1, 3)):
                    x = random.randint(100, 800)
                    y = random.randint(100, 600)
                    actions.move_by_offset(x, y)
                    self._human_like_delay('mouse_move')
                actions.perform()
            
            # Random scrolling
            if self.scroll_behavior:
                scroll_count = random.randint(1, 3)
                for _ in range(scroll_count):
                    scroll_y = random.randint(200, 800)
                    self.driver.execute_script(f"window.scrollBy(0, {scroll_y});")
                    self._human_like_delay('mouse_move')
            
        except Exception as e:
            logger.debug(f"Error in human behavior simulation: {e}")
    
    def _detect_captcha(self) -> bool:
        """Detect if a CAPTCHA is present on the page"""
        
        if not self.driver:
            return False
        
        for selector in self.captcha_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and any(el.is_displayed() for el in elements):
                    logger.warning("CAPTCHA detected on page")
                    return True
            except:
                continue
        
        return False
    
    def _handle_captcha(self) -> bool:
        """Handle CAPTCHA if detected (placeholder for future implementation)"""
        
        logger.warning("CAPTCHA detected - implementing fallback strategy")
        
        # Strategy 1: Wait and retry (sometimes CAPTCHAs disappear)
        time.sleep(random.uniform(10, 30))
        
        if not self._detect_captcha():
            logger.info("CAPTCHA resolved automatically")
            return True
        
        # Strategy 2: Rotate session
        logger.info("Rotating session due to CAPTCHA")
        self._rotate_session()
        return False
    
    def _detect_bot_detection(self, response_text: str) -> bool:
        """Detect if the page indicates bot detection"""
        
        bot_indicators = [
            'blocked',
            'bot detected',
            'access denied',
            'unusual traffic',
            'verify you are human',
            'cloudflare',
            'please complete the security check',
            'suspicious activity'
        ]
        
        text_lower = response_text.lower()
        return any(indicator in text_lower for indicator in bot_indicators)
    
    def make_request(self, url: str, max_retries: int = 3, delay_range: tuple = (2, 8)) -> Optional[requests.Response]:
        """Enhanced request method with advanced anti-bot protection"""
        
        if self.use_selenium:
            return self._make_selenium_request(url, max_retries)
        else:
            return self._make_requests_request(url, max_retries, delay_range)
    
    def _make_selenium_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """Make request using Selenium with stealth features"""
        
        for attempt in range(max_retries):
            try:
                driver = self._get_selenium_driver()
                if not driver:
                    return None
                
                # Human-like delay before request
                self._human_like_delay('between_requests')
                
                # Load the page
                driver.get(url)
                self.request_count += 1
                
                # Wait for page to load
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                
                # Check for CAPTCHA
                if self._detect_captcha():
                    if not self._handle_captcha():
                        continue  # Retry with new session
                
                # Simulate human behavior
                self._simulate_human_behavior()
                
                # Check for bot detection in page content
                page_source = driver.page_source
                if self._detect_bot_detection(page_source):
                    logger.warning(f"Bot detection suspected on {url}")
                    self._rotate_session()
                    continue
                
                # Create a mock response object
                class MockResponse:
                    def __init__(self, content, status_code=200):
                        self.content = content.encode('utf-8')
                        self.text = content
                        self.status_code = status_code
                        self.headers = {}
                
                return MockResponse(page_source)
                
            except Exception as e:
                logger.error(f"Selenium request failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    delay = (2 ** attempt) + random.uniform(1, 5)
                    time.sleep(delay)
                    
                    # Rotate session on repeated failures
                    if attempt > 0:
                        self._rotate_session()
        
        return None
    
    def _make_requests_request(self, url: str, max_retries: int = 3, delay_range: tuple = (2, 8)) -> Optional[requests.Response]:
        """Enhanced requests method with better anti-bot protection"""
        
        for attempt in range(max_retries):
            try:
                # Rotate user agent more frequently
                headers = self.default_headers.copy()
                headers['User-Agent'] = self.get_random_user_agent()
                
                # Add more realistic headers
                headers.update({
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0'
                })
                
                # Random delay with jitter
                min_delay, max_delay = delay_range
                delay = random.uniform(min_delay, max_delay)
                time.sleep(delay)
                
                # Make request with session
                response = self.session.get(
                    url,
                    headers=headers,
                    timeout=30,
                    allow_redirects=True,
                    proxies=self.get_random_proxy() if self.use_proxy else None
                )
                
                self.request_count += 1
                
                # Check response for bot detection
                if response.status_code == 403 or self._detect_bot_detection(response.text):
                    logger.warning(f"Bot detection suspected on {url} (status: {response.status_code})")
                    # Longer delay on detection
                    time.sleep(random.uniform(30, 120))
                    continue
                
                if response.status_code == 200:
                    logger.debug(f"Successfully scraped: {url}")
                    return response
                
                logger.warning(f"HTTP {response.status_code} for {url}")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    delay = (2 ** attempt) * random.uniform(1, 3)
                    time.sleep(delay)
        
        return None
    
    def extract_product_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract product information with enhanced error handling"""
        
        try:
            response = self.make_request(url)
            if not response:
                return None
            
            # Use the appropriate parsing method based on the platform
            if 'amazon.' in url:
                return self._extract_amazon_info(response)
            elif 'ebay.' in url:
                return self._extract_ebay_info(response)
            elif 'walmart.' in url:
                return self._extract_walmart_info(response)
            else:
                logger.warning(f"Unsupported platform for URL: {url}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting product info from {url}: {e}")
            return None
    
    def _extract_amazon_info(self, response) -> Optional[Dict[str, Any]]:
        """Extract Amazon product information with enhanced selectors"""
        
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Enhanced selectors for Amazon
        title_selectors = [
            '#productTitle',
            '.product-title',
            '[data-automation-id="product-title"]',
            'h1.a-size-large'
        ]
        
        price_selectors = [
            '.a-price-whole',
            '.a-price .a-offscreen',
            '#priceblock_dealprice',
            '#priceblock_ourprice',
            '.a-price-range .a-price .a-offscreen',
            '[data-automation-id="product-price"]'
        ]
        
        # Extract with multiple fallbacks
        title = None
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = self.clean_text(element.get_text())
                break
        
        price = None
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price = self.clean_price(element.get_text())
                if price:
                    break
        
        # Additional data extraction
        availability = True  # Default assumption
        availability_selectors = [
            '#availability span',
            '.a-color-state',
            '[data-automation-id="availability-text"]'
        ]
        
        for selector in availability_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text().lower()
                if any(word in text for word in ['out of stock', 'unavailable', 'currently unavailable']):
                    availability = False
                    break
        
        return {
            'title': title,
            'current_price': price,
            'availability': availability,
            'platform': 'amazon',
            'scraped_at': datetime.utcnow().isoformat()
        }
    
    def _extract_ebay_info(self, response) -> Optional[Dict[str, Any]]:
        """Extract eBay product information (placeholder)"""
        # Implementation would be similar to Amazon but with eBay-specific selectors
        return {
            'title': 'eBay Product (placeholder)',
            'current_price': 0.0,
            'availability': True,
            'platform': 'ebay',
            'scraped_at': datetime.utcnow().isoformat()
        }
    
    def _extract_walmart_info(self, response) -> Optional[Dict[str, Any]]:
        """Extract Walmart product information (placeholder)"""
        # Implementation would be similar to Amazon but with Walmart-specific selectors
        return {
            'title': 'Walmart Product (placeholder)',
            'current_price': 0.0,
            'availability': True,
            'platform': 'walmart',
            'scraped_at': datetime.utcnow().isoformat()
        }
    
    def is_valid_url(self, url: str) -> bool:
        """Enhanced URL validation"""
        
        supported_domains = [
            'amazon.com', 'amazon.co.uk', 'amazon.de', 'amazon.fr', 'amazon.it', 'amazon.es',
            'ebay.com', 'ebay.co.uk', 'ebay.de',
            'walmart.com',
            'aliexpress.com'
        ]
        
        return any(domain in url.lower() for domain in supported_domains)
    
    def cleanup(self):
        """Clean up resources"""
        
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
        
        if self.session:
            self.session.close()
        
        logger.info("EnhancedScraper cleaned up")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup() 