#!/usr/bin/env python3
"""
Step 4 Demo: Profit Estimation, Dashboard, and Seller Comparison Features

This script demonstrates the new functionality added in Step 4:
- Profit estimation module with platform fees
- Interactive dashboard with charts and visualizations
- Seller comparison and analysis features
- Enhanced notification system integration
"""

import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.tracker import PriceTracker
from src.utils.config import Config
from src.utils.profit_calculator import ProfitCalculator
from src.notifications.notification_manager import NotificationManager

def main():
    print("=" * 60)
    print("💰 Step 4 Demo: Profit Estimation & Dashboard Features")
    print("=" * 60)
    
    # Initialize components
    config = Config()
    tracker = PriceTracker(config)
    profit_calc = ProfitCalculator()
    notification_manager = NotificationManager(config)
    
    # Show notification system integration
    print(f"\n📬 Notification System Status:")
    notification_status = tracker.get_notification_status()
    print(f"  - Configured services: {notification_status.get('configured_services', [])}")
    print(f"  - Total services: {notification_status.get('total_services', 0)}")
    
    for service, status in notification_status.get('service_status', {}).items():
        status_icon = "✅" if status.get('configured') else "❌"
        enabled_icon = "🔔" if status.get('enabled') else "🔕"
        print(f"  - {service.title()}: {status_icon} {enabled_icon}")
    
    # Demonstrate profit calculator
    print(f"\n💰 Profit Calculator Demo:")
    
    # Example calculations for different platforms
    cost_price = 15.00
    selling_price = 35.00
    
    print(f"  Example: Cost ${cost_price:.2f} → Selling ${selling_price:.2f}")
    print(f"  {'='*50}")
    
    platforms = ['amazon', 'ebay', 'walmart']
    profit_results = {}
    
    for platform in platforms:
        try:
            profit_data = profit_calc.calculate_profit_for_platform(platform, selling_price, cost_price)
            profit_results[platform] = profit_data
            
            print(f"\n  🏪 {platform.title()} Analysis:")
            print(f"    💵 Gross Profit: ${profit_data['gross_profit']:.2f}")
            print(f"    💸 Total Fees: ${profit_data['total_fees']:.2f}")
            print(f"    💰 Net Profit: ${profit_data['net_profit']:.2f}")
            print(f"    📊 Profit Margin: {profit_data['profit_margin_percent']:.1f}%")
            print(f"    📈 ROI: {profit_data['roi_percent']:.1f}%")
            print(f"    ⚖️  Break-even: ${profit_data['break_even_price']:.2f}")
            print(f"    {'✅ Profitable' if profit_data['is_profitable'] else '❌ Not Profitable'}")
            
            # Show fee breakdown
            print(f"    Fee Breakdown:")
            for fee_name, fee_value in profit_data['fee_breakdown'].items():
                print(f"      • {fee_name.replace('_', ' ').title()}: ${fee_value:.2f}")
                
        except Exception as e:
            print(f"  ❌ Error calculating {platform}: {e}")
    
    # Platform comparison
    print(f"\n🔍 Platform Comparison:")
    if profit_results:
        best_platform = max(profit_results.items(), key=lambda x: x[1]['net_profit'])
        worst_platform = min(profit_results.items(), key=lambda x: x[1]['net_profit'])
        
        print(f"  🏆 Best Platform: {best_platform[0].title()} (${best_platform[1]['net_profit']:.2f} profit)")
        print(f"  📉 Worst Platform: {worst_platform[0].title()} (${worst_platform[1]['net_profit']:.2f} profit)")
        
        # Show profit difference
        profit_diff = best_platform[1]['net_profit'] - worst_platform[1]['net_profit']
        print(f"  💡 Difference: ${profit_diff:.2f} ({profit_diff/worst_platform[1]['net_profit']*100:.1f}% more)")
    
    # Break-even analysis
    print(f"\n⚖️  Break-even Analysis:")
    target_margin = 25.0  # 25% target profit margin
    
    for platform in platforms[:2]:  # Show for first 2 platforms
        try:
            breakeven_data = profit_calc.calculate_break_even_analysis(cost_price, platform, target_margin)
            print(f"\n  🎯 {platform.title()} - Target {target_margin}% margin:")
            print(f"    Required selling price: ${breakeven_data['required_selling_price']:.2f}")
            print(f"    Actual margin achieved: {breakeven_data['actual_profit_margin']:.1f}%")
            print(f"    Expected net profit: ${breakeven_data['expected_net_profit']:.2f}")
            
        except Exception as e:
            print(f"  ❌ Break-even error for {platform}: {e}")
    
    # Show current tracking data
    print(f"\n📊 Current Tracking Data:")
    products = tracker.get_tracked_products()
    analytics = tracker.get_analytics(days=30)
    
    print(f"  - Tracked products: {len(products)}")
    print(f"  - Price checks (30 days): {analytics.get('total_price_checks', 0)}")
    print(f"  - Products with changes: {analytics.get('products_with_changes', 0)}")
    print(f"  - Average price: ${analytics.get('average_price', 0):.2f}")
    
    # Show platform breakdown
    platforms_data = analytics.get('platform_breakdown', {})
    if platforms_data:
        print(f"  - Platform breakdown:")
        for platform, count in platforms_data.items():
            print(f"    • {platform.title()}: {count} products")
    
    # Show biggest changes
    biggest_drop = analytics.get('biggest_price_drop')
    if biggest_drop:
        savings = biggest_drop.get('first_price', 0) - biggest_drop.get('last_price', 0)
        print(f"  - Biggest price drop: ${savings:.2f} on {biggest_drop.get('product_title', 'Unknown')[:40]}...")
    
    biggest_increase = analytics.get('biggest_price_increase')
    if biggest_increase:
        increase = biggest_increase.get('last_price', 0) - biggest_increase.get('first_price', 0)
        print(f"  - Biggest price increase: ${increase:.2f} on {biggest_increase.get('product_title', 'Unknown')[:40]}...")
    
    # Demonstrate profit analysis for tracked products
    if products:
        print(f"\n💼 Profit Analysis for Tracked Products:")
        
        for i, product in enumerate(products[:3], 1):  # Show first 3 products
            title = product.get('title', 'Unknown')[:40]
            current_price = product.get('current_price')
            user_cost_price = product.get('user_cost_price')
            platform = product.get('platform', 'unknown')
            
            print(f"\n  {i}. {title}...")
            print(f"     Platform: {platform.title()}")
            print(f"     Current Price: ${current_price:.2f}" if current_price else "     Current Price: N/A")
            
            if user_cost_price and current_price:
                try:
                    profit_data = profit_calc.calculate_profit_for_platform(platform, current_price, user_cost_price)
                    print(f"     Cost Price: ${user_cost_price:.2f}")
                    print(f"     Net Profit: ${profit_data['net_profit']:.2f}")
                    print(f"     Margin: {profit_data['profit_margin_percent']:.1f}%")
                    print(f"     {'✅ Profitable' if profit_data['is_profitable'] else '❌ Not Profitable'}")
                except Exception as e:
                    print(f"     ❌ Profit calculation error: {e}")
            else:
                print(f"     💡 Set cost price to see profit analysis")
    
    # Dashboard information
    print(f"\n📊 Dashboard Features:")
    print(f"  🚀 Main Dashboard: python src/dashboard/app.py")
    print(f"    • Interactive charts and visualizations")
    print(f"    • Real-time price history graphs")
    print(f"    • Profit calculator with live updates")
    print(f"    • Platform comparison analytics")
    print(f"    • Auto-refresh every 5 minutes")
    print(f"    • Available at: http://127.0.0.1:8050")
    
    print(f"\n🔗 URL Manager: python src/dashboard/url_manager.py")
    print(f"    • Add new products with target/cost prices")
    print(f"    • URL validation and platform detection")
    print(f"    • Product management interface")
    print(f"    • Quick actions (test notifications, export, tracking)")
    print(f"    • Available at: http://127.0.0.1:8051")
    
    # Export capabilities
    print(f"\n📤 Export Capabilities:")
    export_status = tracker.get_export_status()
    print(f"  - Google Sheets: {'✅ Available' if export_status.get('google_sheets_available') else '❌ Not configured'}")
    print(f"  - Excel Export: {'✅ Available' if export_status.get('excel_available') else '❌ Not available'}")
    print(f"  - Export Directory: {export_status.get('export_directory', 'N/A')}")
    print(f"  - Recent Exports: {len(export_status.get('recent_exports', []))}")
    
    # Test notification system (if configured)
    notification_services = notification_status.get('configured_services', [])
    if notification_services:
        print(f"\n📬 Testing Notification System:")
        print(f"  Available services: {', '.join(notification_services)}")
        
        user_input = input(f"  Test notifications? (y/N): ").lower().strip()
        if user_input == 'y':
            try:
                results = tracker.test_notifications()
                print(f"  📧 Test Results:")
                for service, success in results.items():
                    status = "✅ Success" if success else "❌ Failed"
                    print(f"    • {service.title()}: {status}")
            except Exception as e:
                print(f"  ❌ Test error: {e}")
    else:
        print(f"\n📬 Notification System:")
        print(f"  ℹ️  No notification services configured")
        print(f"  💡 Configure email, Telegram, or Slack in your .env file")
    
    # Summary of Step 4 features
    print(f"\n🎉 Step 4 Features Summary:")
    print(f"  ✅ Advanced profit calculation with platform-specific fees")
    print(f"  ✅ Interactive dashboard with real-time charts")
    print(f"  ✅ URL management interface for easy product addition")
    print(f"  ✅ Platform comparison and break-even analysis")
    print(f"  ✅ Enhanced notification system with alert logic")
    print(f"  ✅ Seller comparison and profit margin optimization")
    print(f"  ✅ Comprehensive analytics with visual insights")
    print(f"  ✅ Auto-refreshing dashboard with live data")
    
    print(f"\n💡 Next Steps:")
    print(f"  1. Start the dashboard: python src/dashboard/app.py")
    print(f"  2. Start URL manager: python src/dashboard/url_manager.py")
    print(f"  3. Add products with cost prices for profit analysis")
    print(f"  4. Configure notifications for automated alerts")
    print(f"  5. Step 5 will add full automation and scheduling")
    
    print(f"\n📁 Files created in Step 4:")
    print(f"  • src/utils/profit_calculator.py - Platform fee calculations")
    print(f"  • src/dashboard/app.py - Interactive dashboard with charts")
    print(f"  • src/dashboard/url_manager.py - URL management interface")
    print(f"  • Enhanced notification integration in tracker")
    print(f"  • Profit analysis and seller comparison features")

if __name__ == "__main__":
    main() 