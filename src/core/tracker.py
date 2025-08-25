from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging
import os
from urllib.parse import urlparse

from .database import db_manager
from ..models.product import Product, PriceHistory, Alert
from ..scrapers.amazon_scraper import AmazonScraper
from ..storage.data_manager import DataManager
from ..utils.config import Config

logger = logging.getLogger(__name__)

class PriceTracker:
    """Main price tracking orchestrator"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.scrapers = {}
        self.data_manager = DataManager(config)
        self._initialize_scrapers()
    
    def _initialize_scrapers(self):
        """Initialize platform-specific scrapers"""
        proxy_list = None
        if self.config.USE_PROXY and self.config.PROXY_LIST:
            proxy_list = self.config.PROXY_LIST.split(',')
        
        # Initialize Amazon scraper
        self.scrapers['amazon'] = AmazonScraper(
            use_proxy=self.config.USE_PROXY,
            proxy_list=proxy_list
        )
        
        logger.info(f"Initialized {len(self.scrapers)} scrapers")
    
    def detect_platform(self, url: str) -> Optional[str]:
        """Detect which platform a URL belongs to"""
        try:
            parsed = urlparse(url.lower())
            domain = parsed.netloc
            
            if 'amazon.' in domain:
                return 'amazon'
            elif 'ebay.' in domain:
                return 'ebay'  # Will be implemented in future steps
            elif 'walmart.' in domain:
                return 'walmart'  # Will be implemented in future steps
            elif 'aliexpress.' in domain:
                return 'aliexpress'  # Will be implemented in future steps
            
            return None
        except Exception as e:
            logger.error(f"Error detecting platform for URL {url}: {e}")
            return None
    
    def add_product(self, url: str, target_price: float = None, user_cost_price: float = None) -> Optional[int]:
        """Add a new product to track"""
        
        platform = self.detect_platform(url)
        if not platform:
            logger.error(f"Unsupported platform for URL: {url}")
            return None
        
        if platform not in self.scrapers:
            logger.error(f"No scraper available for platform: {platform}")
            return None
        
        scraper = self.scrapers[platform]
        
        # Check if product already exists
        with db_manager.get_session() as session:
            existing = session.query(Product).filter(Product.url == url).first()
            if existing:
                logger.info(f"Product already tracked: {existing.title}")
                return existing.id
        
        # Scrape initial product data
        logger.info(f"Scraping initial data for: {url}")
        product_data = scraper.extract_product_info(url)
        
        if not product_data:
            logger.error(f"Failed to scrape product data from: {url}")
            return None
        
        # Create product record
        with db_manager.get_session() as session:
            product = Product(
                url=url,
                platform=platform,
                title=product_data.get('title'),
                current_price=product_data.get('current_price'),
                target_price=target_price,
                availability=product_data.get('availability', True),
                rating=product_data.get('rating'),
                review_count=product_data.get('review_count'),
                seller=product_data.get('seller'),
                image_url=product_data.get('image_url'),
                product_id=product_data.get('product_id'),
                category=product_data.get('category'),
                brand=product_data.get('brand'),
                user_cost_price=user_cost_price,
                last_checked=datetime.utcnow()
            )
            
            session.add(product)
            session.commit()
            session.refresh(product)
            
            # Add initial price history record
            if product.current_price:
                history = PriceHistory(
                    product_id=product.id,
                    price=product.current_price,
                    availability=product.availability,
                    rating=product.rating,
                    review_count=product.review_count,
                    seller=product.seller
                )
                session.add(history)
                session.commit()
            
            logger.info(f"Added product to tracking: {product.title} (ID: {product.id})")
            return product.id
    
    def update_product(self, product_id: int) -> bool:
        """Update a single product's information"""
        
        with db_manager.get_session() as session:
            product = session.query(Product).filter(Product.id == product_id).first()
            
            if not product or not product.is_active:
                logger.warning(f"Product {product_id} not found or inactive")
                return False
            
            scraper = self.scrapers.get(product.platform)
            if not scraper:
                logger.error(f"No scraper for platform: {product.platform}")
                return False
            
            logger.info(f"Updating product: {product.title}")
            
            # Scrape current data
            current_data = scraper.extract_product_info(product.url)
            if not current_data:
                logger.error(f"Failed to scrape updated data for product {product_id}")
                return False
            
            # Store previous values for comparison
            prev_price = product.current_price
            prev_availability = product.availability
            prev_rating = product.rating
            
            # Update product record
            product.title = current_data.get('title') or product.title
            product.current_price = current_data.get('current_price')
            product.availability = current_data.get('availability', True)
            product.rating = current_data.get('rating')
            product.review_count = current_data.get('review_count')
            product.seller = current_data.get('seller')
            product.image_url = current_data.get('image_url') or product.image_url
            product.category = current_data.get('category') or product.category
            product.brand = current_data.get('brand') or product.brand
            product.last_checked = datetime.utcnow()
            
            # Add price history record
            if product.current_price:
                history = PriceHistory(
                    product_id=product.id,
                    price=product.current_price,
                    availability=product.availability,
                    rating=product.rating,
                    review_count=product.review_count,
                    seller=product.seller
                )
                session.add(history)
            
            session.commit()
            
            # Check for significant changes
            changes = []
            if prev_price and product.current_price and prev_price != product.current_price:
                price_change = ((product.current_price - prev_price) / prev_price) * 100
                changes.append(f"Price: ${prev_price} → ${product.current_price} ({price_change:+.1f}%)")
            
            if prev_availability != product.availability:
                status = "In Stock" if product.availability else "Out of Stock"
                changes.append(f"Availability: {status}")
            
            if prev_rating and product.rating and abs(prev_rating - product.rating) > 0.1:
                changes.append(f"Rating: {prev_rating} → {product.rating}")
            
            if changes:
                logger.info(f"Changes detected for {product.title}: {'; '.join(changes)}")
            
            return True
    
    def run_tracking(self, product_ids: List[int] = None, export_after: bool = False) -> Dict[str, Any]:
        """Run tracking for specified products or all active products"""
        
        with db_manager.get_session() as session:
            query = session.query(Product).filter(Product.is_active == True)
            
            if product_ids:
                query = query.filter(Product.id.in_(product_ids))
            
            products = query.all()
            
            if not products:
                logger.info("No active products to track")
                return {'updated': 0, 'failed': 0, 'total': 0}
            
            logger.info(f"Starting tracking run for {len(products)} products")
            
            updated_count = 0
            failed_count = 0
            
            for product in products:
                try:
                    if self.update_product(product.id):
                        updated_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Error updating product {product.id}: {e}")
                    failed_count += 1
            
            result = {
                'updated': updated_count,
                'failed': failed_count,
                'total': len(products),
                'timestamp': datetime.utcnow().isoformat(),
                'export_results': None
            }
            
            # Run export if requested
            if export_after and updated_count > 0:
                logger.info("Running export after tracking update...")
                export_results = self.data_manager.run_daily_export()
                result['export_results'] = export_results
            
            logger.info(f"Tracking run completed: {updated_count} updated, {failed_count} failed")
            return result
    
    def get_product_history(self, product_id: int, days: int = 30) -> List[Dict]:
        """Get price history for a product"""
        return self.data_manager.get_product_price_trend(product_id, days)
    
    def get_tracked_products(self, active_only: bool = True) -> List[Dict]:
        """Get list of all tracked products"""
        return self.data_manager.get_all_products_data(active_only)
    
    def remove_product(self, product_id: int) -> bool:
        """Remove a product from tracking (soft delete)"""
        
        with db_manager.get_session() as session:
            product = session.query(Product).filter(Product.id == product_id).first()
            
            if not product:
                logger.warning(f"Product {product_id} not found")
                return False
            
            product.is_active = False
            session.commit()
            
            logger.info(f"Removed product from tracking: {product.title}")
            return True
    
    def export_data(self, export_type: str = "excel", **kwargs) -> Dict[str, Any]:
        """Export tracking data"""
        
        result = {
            'success': False,
            'export_type': export_type,
            'filepath': None,
            'message': None
        }
        
        try:
            if export_type.lower() == "excel":
                filepath = self.data_manager.export_to_excel(**kwargs)
                if filepath:
                    result['success'] = True
                    result['filepath'] = filepath
                    result['message'] = f"Data exported to {filepath}"
                else:
                    result['message'] = "Failed to export to Excel"
            
            elif export_type.lower() == "google_sheets":
                success = self.data_manager.export_to_google_sheets(**kwargs)
                result['success'] = success
                result['message'] = "Data exported to Google Sheets" if success else "Failed to export to Google Sheets"
            
            else:
                result['message'] = f"Unsupported export type: {export_type}"
            
        except Exception as e:
            result['message'] = f"Export error: {str(e)}"
            logger.error(f"Export error: {e}")
        
        return result
    
    def get_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get price analytics for the specified period"""
        return self.data_manager.get_price_analytics(days)
    
    def get_export_status(self) -> Dict[str, Any]:
        """Get export capabilities status"""
        return self.data_manager.get_export_status() 