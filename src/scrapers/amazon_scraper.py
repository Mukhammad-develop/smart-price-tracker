from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urlparse, parse_qs
from .base_scraper import BaseScraper

class AmazonScraper(BaseScraper):
    """Amazon-specific scraper implementation"""
    
    def __init__(self, use_proxy: bool = False, proxy_list: Optional[list] = None):
        super().__init__(use_proxy, proxy_list)
        self.platform = "amazon"
        
        # Amazon-specific headers
        self.default_headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })
    
    def is_valid_url(self, url: str) -> bool:
        """Check if the URL is a valid Amazon product URL"""
        try:
            parsed = urlparse(url)
            if 'amazon.' not in parsed.netloc.lower():
                return False
            
            # Check for product identifier patterns
            amazon_patterns = [
                r'/dp/[A-Z0-9]{10}',
                r'/gp/product/[A-Z0-9]{10}',
                r'/product/[A-Z0-9]{10}',
                r'asin=([A-Z0-9]{10})'
            ]
            
            return any(re.search(pattern, url) for pattern in amazon_patterns)
        except Exception:
            return False
    
    def extract_asin(self, url: str) -> Optional[str]:
        """Extract ASIN (Amazon Standard Identification Number) from URL"""
        patterns = [
            r'/dp/([A-Z0-9]{10})',
            r'/gp/product/([A-Z0-9]{10})',
            r'/product/([A-Z0-9]{10})',
            r'asin=([A-Z0-9]{10})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def extract_product_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract product information from Amazon product page"""
        
        if not self.is_valid_url(url):
            self.logger.error(f"Invalid Amazon URL: {url}")
            return None
        
        response = self.make_request(url)
        if not response:
            self.logger.error(f"Failed to fetch page: {url}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract ASIN
        asin = self.extract_asin(url)
        
        # Initialize product data
        product_data = {
            'url': url,
            'platform': self.platform,
            'product_id': asin,
            'title': None,
            'current_price': None,
            'availability': True,
            'rating': None,
            'review_count': None,
            'seller': None,
            'image_url': None,
            'category': None,
            'brand': None
        }
        
        try:
            # Extract title
            title_selectors = [
                '#productTitle',
                '.product-title',
                'h1.a-size-large',
                '[data-automation-id="product-title"]'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    product_data['title'] = self.clean_text(title_elem.get_text())
                    break
            
            # Extract price
            price_selectors = [
                '.a-price-whole',
                '.a-price .a-offscreen',
                '#corePrice_feature_div .a-price .a-offscreen',
                '.a-price-range .a-price .a-offscreen',
                '#apex_desktop .a-price .a-offscreen',
                '.a-price-current .a-offscreen'
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text()
                    product_data['current_price'] = self.clean_price(price_text)
                    if product_data['current_price']:
                        break
            
            # Extract availability
            availability_indicators = [
                '#availability span',
                '#availability .a-color-success',
                '#availability .a-color-price',
                '.a-color-success',
                '[data-feature-name="availability"] span'
            ]
            
            availability_text = ""
            for selector in availability_indicators:
                avail_elem = soup.select_one(selector)
                if avail_elem:
                    availability_text = avail_elem.get_text().lower()
                    break
            
            # Determine availability
            if any(phrase in availability_text for phrase in ['in stock', 'available', 'ships from']):
                product_data['availability'] = True
            elif any(phrase in availability_text for phrase in ['out of stock', 'unavailable', 'temporarily out']):
                product_data['availability'] = False
            
            # Extract rating
            rating_selectors = [
                '[data-hook="average-star-rating"] .a-icon-alt',
                '.a-icon-alt',
                '.reviewCountTextLinkedHistogram .a-icon-alt',
                '#acrPopover .a-icon-alt'
            ]
            
            for selector in rating_selectors:
                rating_elem = soup.select_one(selector)
                if rating_elem:
                    rating_text = rating_elem.get('title', '') or rating_elem.get_text()
                    if 'out of 5' in rating_text:
                        product_data['rating'] = self.extract_rating(rating_text)
                        break
            
            # Extract review count
            review_selectors = [
                '[data-hook="total-review-count"]',
                '#acrCustomerReviewText',
                '.a-link-normal[href*="#customerReviews"]',
                '#reviewsMedley .a-link-normal'
            ]
            
            for selector in review_selectors:
                review_elem = soup.select_one(selector)
                if review_elem:
                    review_text = review_elem.get_text()
                    product_data['review_count'] = self.extract_review_count(review_text)
                    if product_data['review_count']:
                        break
            
            # Extract seller information
            seller_selectors = [
                '#merchant-info',
                '#sellerProfileTriggerId',
                '.tabular-buybox-text[tabular-attribute-name="Sold by"] span',
                '#soldByThirdParty .a-color-secondary'
            ]
            
            for selector in seller_selectors:
                seller_elem = soup.select_one(selector)
                if seller_elem:
                    seller_text = seller_elem.get_text()
                    if seller_text and 'amazon' not in seller_text.lower():
                        product_data['seller'] = self.clean_text(seller_text)
                        break
            
            if not product_data['seller']:
                product_data['seller'] = 'Amazon'
            
            # Extract main image
            image_selectors = [
                '#landingImage',
                '.a-dynamic-image',
                '#imgTagWrapperId img',
                '.a-main-image img'
            ]
            
            for selector in image_selectors:
                img_elem = soup.select_one(selector)
                if img_elem:
                    product_data['image_url'] = img_elem.get('src') or img_elem.get('data-src')
                    break
            
            # Extract brand
            brand_selectors = [
                '#bylineInfo',
                '.a-link-normal[data-attribute="brand"]',
                '.po-brand .po-break-word',
                '#feature-bullets .a-list-item:contains("Brand")'
            ]
            
            for selector in brand_selectors:
                brand_elem = soup.select_one(selector)
                if brand_elem:
                    brand_text = brand_elem.get_text()
                    # Clean brand text (remove "Visit the", "Brand:", etc.)
                    brand_clean = re.sub(r'(Visit the|Brand:|by\s+)', '', brand_text, flags=re.IGNORECASE)
                    product_data['brand'] = self.clean_text(brand_clean)
                    if product_data['brand']:
                        break
            
            # Extract category from breadcrumbs
            breadcrumb_elem = soup.select_one('#wayfinding-breadcrumbs_feature_div')
            if breadcrumb_elem:
                breadcrumbs = [a.get_text().strip() for a in breadcrumb_elem.select('a')]
                if breadcrumbs:
                    product_data['category'] = ' > '.join(breadcrumbs[-2:])  # Last 2 categories
            
            self.logger.info(f"Successfully extracted data for: {product_data.get('title', 'Unknown')[:50]}")
            return product_data
            
        except Exception as e:
            self.logger.error(f"Error extracting product info: {str(e)}")
            return None
    
    def search_products(self, query: str, max_results: int = 10) -> list:
        """Search for products on Amazon (for future enhancement)"""
        # This would be used for product discovery features
        # Implementation would involve Amazon search API or search page scraping
        pass 