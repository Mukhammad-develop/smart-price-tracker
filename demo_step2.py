#!/usr/bin/env python3
"""
Step 2 Demo: Data Storage, Historical Tracking, and Export Features

This script demonstrates the new functionality added in Step 2:
- Historical price tracking with timestamps
- Google Sheets integration
- Excel export functionality
- Analytics and reporting
"""

import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.tracker import PriceTracker
from src.storage.data_manager import DataManager
from src.utils.config import Config

def main():
    print("=" * 60)
    print("📊 Step 2 Demo: Data Storage & Export Features")
    print("=" * 60)
    
    # Initialize components
    config = Config()
    tracker = PriceTracker(config)
    data_manager = DataManager(config)
    
    print(f"\n🔧 Configuration Status:")
    warnings = config.validate_config()
    if warnings:
        for warning in warnings:
            print(f"  ⚠️  {warning}")
    else:
        print("  ✅ All integrations configured")
    
    # Show current data status
    products = tracker.get_tracked_products()
    print(f"\n📦 Current Data:")
    print(f"  - Tracked products: {len(products)}")
    
    if products:
        print(f"  - Sample products:")
        for i, product in enumerate(products[:3], 1):
            status = "✅" if product.get('availability') else "❌"
            price = f"${product.get('current_price'):.2f}" if product.get('current_price') else "N/A"
            print(f"    {i}. {status} {product.get('title', 'Unknown')[:40]}... - {price}")
    
    # Demonstrate analytics
    print(f"\n📈 Analytics Demo:")
    analytics = tracker.get_analytics(days=30)
    print(f"  - Total products analyzed: {analytics.get('total_products', 0)}")
    print(f"  - Total price checks: {analytics.get('total_price_checks', 0)}")
    print(f"  - Products with changes: {analytics.get('products_with_changes', 0)}")
    print(f"  - Average price: ${analytics.get('average_price', 0):.2f}")
    
    # Platform breakdown
    platforms = analytics.get('platform_breakdown', {})
    if platforms:
        print(f"  - Platform breakdown:")
        for platform, count in platforms.items():
            print(f"    • {platform.title()}: {count} products")
    
    # Show biggest changes
    biggest_drop = analytics.get('biggest_price_drop')
    if biggest_drop:
        print(f"  - Biggest price drop: {biggest_drop.get('product_title', 'Unknown')[:30]}...")
        print(f"    ${biggest_drop.get('first_price'):.2f} → ${biggest_drop.get('last_price'):.2f} ({biggest_drop.get('change_percent'):.1f}%)")
    
    biggest_increase = analytics.get('biggest_price_increase')
    if biggest_increase:
        print(f"  - Biggest price increase: {biggest_increase.get('product_title', 'Unknown')[:30]}...")
        print(f"    ${biggest_increase.get('first_price'):.2f} → ${biggest_increase.get('last_price'):.2f} ({biggest_increase.get('change_percent'):.1f}%)")
    
    # Demonstrate export functionality
    print(f"\n📤 Export Capabilities:")
    export_status = tracker.get_export_status()
    print(f"  - Google Sheets available: {'✅' if export_status.get('google_sheets_available') else '❌'}")
    print(f"  - Excel export available: {'✅' if export_status.get('excel_available') else '❌'}")
    print(f"  - Export directory: {export_status.get('export_directory', 'N/A')}")
    
    recent_exports = export_status.get('recent_exports', [])
    if recent_exports:
        print(f"  - Recent exports ({len(recent_exports)}):")
        for export_file in recent_exports[:3]:
            print(f"    • {export_file}")
    
    # Demo Excel export
    print(f"\n📊 Excel Export Demo:")
    try:
        if products:
            export_result = tracker.export_data("excel", export_type="comprehensive")
            if export_result['success']:
                print(f"  ✅ Excel export successful: {export_result['filepath']}")
            else:
                print(f"  ❌ Excel export failed: {export_result['message']}")
        else:
            print(f"  ℹ️  No products to export")
    except Exception as e:
        print(f"  ❌ Export error: {e}")
    
    # Demo Google Sheets export (if configured)
    if export_status.get('google_sheets_available'):
        print(f"\n📊 Google Sheets Export Demo:")
        try:
            export_result = tracker.export_data("google_sheets")
            if export_result['success']:
                print(f"  ✅ Google Sheets export successful")
            else:
                print(f"  ❌ Google Sheets export failed: {export_result['message']}")
        except Exception as e:
            print(f"  ❌ Google Sheets error: {e}")
    
    # Show price history for a product (if available)
    if products:
        print(f"\n📈 Price History Demo:")
        sample_product = products[0]
        product_id = sample_product.get('id')
        
        try:
            history_data = tracker.get_product_history(product_id, days=30)
            if 'error' not in history_data:
                print(f"  Product: {history_data.get('product_title', 'Unknown')[:40]}...")
                summary = history_data.get('summary', {})
                print(f"  - Current price: ${history_data.get('current_price', 0):.2f}")
                print(f"  - Target price: ${history_data.get('target_price', 0):.2f}" if history_data.get('target_price') else "  - No target price set")
                print(f"  - Price range: ${summary.get('min_price', 0):.2f} - ${summary.get('max_price', 0):.2f}")
                print(f"  - Average price: ${summary.get('avg_price', 0):.2f}")
                print(f"  - Total checks: {summary.get('total_checks', 0)}")
                
                price_change = summary.get('price_change')
                if price_change:
                    direction = price_change.get('direction', 'stable')
                    emoji = "📈" if direction == 'up' else "📉" if direction == 'down' else "➡️"
                    print(f"  - Trend: {emoji} {direction.title()} ({price_change.get('percent', 0):.1f}%)")
            else:
                print(f"  ❌ {history_data.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"  ❌ History error: {e}")
    
    # Summary of new features
    print(f"\n🎉 Step 2 Features Summary:")
    print(f"  ✅ Timestamped price history tracking")
    print(f"  ✅ Google Sheets integration with dashboard")
    print(f"  ✅ Excel export with multiple sheets and analysis")
    print(f"  ✅ Comprehensive analytics and reporting")
    print(f"  ✅ Automated daily export functionality")
    print(f"  ✅ Price trend analysis and change detection")
    print(f"  ✅ Export file management and cleanup")
    
    print(f"\n💡 Next Steps:")
    print(f"  1. Configure Google Sheets credentials for cloud sync")
    print(f"  2. Set up automated daily exports")
    print(f"  3. Add more products to see richer analytics")
    print(f"  4. Step 3 will add notification system")
    
    print(f"\n📁 Files created in Step 2:")
    print(f"  • src/storage/google_sheets.py - Google Sheets integration")
    print(f"  • src/storage/excel_exporter.py - Excel export functionality")
    print(f"  • src/storage/data_manager.py - Data orchestration and analytics")
    print(f"  • exports/ directory - Excel export files")

if __name__ == "__main__":
    main() 