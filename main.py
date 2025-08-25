#!/usr/bin/env python3
"""
Smart Price Tracker - Main Entry Point

A comprehensive web scraping tool for tracking product prices across multiple e-commerce platforms.
"""

import logging
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.tracker import PriceTracker
from src.utils.config import Config

def setup_logging(config: Config):
    """Set up logging configuration"""
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(config.LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main function"""
    
    print("=" * 60)
    print("🛍️  Smart Price Tracker")
    print("=" * 60)
    
    # Load configuration
    config = Config()
    setup_logging(config)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Smart Price Tracker")
    
    # Validate configuration
    warnings = config.validate_config()
    if warnings:
        logger.warning("Configuration warnings:")
        for warning in warnings:
            logger.warning(f"  - {warning}")
    
    # Initialize tracker
    try:
        tracker = PriceTracker(config)
        logger.info("Price tracker initialized successfully")
        
        # Example usage - Add some sample products
        print("\n📦 Example Usage:")
        print("To add a product for tracking, use:")
        print("  tracker.add_product('https://amazon.com/product-url', target_price=50.00)")
        print("\nTo run tracking on all products:")
        print("  result = tracker.run_tracking()")
        print("\nTo get tracked products:")
        print("  products = tracker.get_tracked_products()")
        
        # Interactive mode for demonstration
        print(f"\n🚀 Tracker is ready! You can now:")
        print("  1. Add products via the web interface (coming in step 3)")
        print("  2. Use the Python API directly")
        print("  3. Set up automated scheduling (coming in step 5)")
        
        # Show current status
        products = tracker.get_tracked_products()
        print(f"\n📊 Current Status:")
        print(f"  - Tracked products: {len(products)}")
        print(f"  - Available scrapers: {', '.join(tracker.scrapers.keys())}")
        print(f"  - Database: {config.DATABASE_URL}")
        
        if products:
            print(f"\n📋 Tracked Products:")
            for product in products[:5]:  # Show first 5
                status = "✅" if product['availability'] else "❌"
                price = f"${product['current_price']:.2f}" if product['current_price'] else "N/A"
                print(f"  {status} {product['title'][:50]}... - {price}")
            
            if len(products) > 5:
                print(f"  ... and {len(products) - 5} more products")
        
        return tracker
        
    except Exception as e:
        logger.error(f"Failed to initialize tracker: {e}")
        return None

if __name__ == "__main__":
    tracker = main()
    
    # Keep the script running for interactive use
    if tracker:
        print(f"\n💡 Tip: The tracker object is available as 'tracker' variable")
        print("   You can use it to add products, run tracking, etc.")
        
        # Example of adding a test product (commented out)
        # Uncomment and modify with a real Amazon URL to test
        """
        print("\n🧪 Testing with a sample Amazon product...")
        sample_url = "https://www.amazon.com/dp/B08N5WRWNW"  # Example Echo Dot
        try:
            product_id = tracker.add_product(sample_url, target_price=30.00)
            if product_id:
                print(f"✅ Successfully added product with ID: {product_id}")
                
                # Run a test tracking update
                result = tracker.run_tracking([product_id])
                print(f"📊 Tracking result: {result}")
            else:
                print("❌ Failed to add sample product")
        except Exception as e:
            print(f"❌ Error testing with sample product: {e}")
        """ 