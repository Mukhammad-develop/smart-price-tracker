from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
import logging
import os

from .google_sheets import GoogleSheetsExporter
from .excel_exporter import ExcelExporter
from ..core.database import db_manager
from ..models.product import Product, PriceHistory, Alert
from ..utils.config import Config

logger = logging.getLogger(__name__)

class DataManager:
    """Manages all data storage, export, and analytics operations"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.google_sheets = GoogleSheetsExporter(config)
        self.excel_exporter = ExcelExporter(config)
    
    def get_all_products_data(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all products data from database"""
        
        with db_manager.get_session() as session:
            query = session.query(Product)
            
            if active_only:
                query = query.filter(Product.is_active == True)
            
            products = query.order_by(Product.created_at.desc()).all()
            return [p.to_dict() for p in products]
    
    def get_all_price_history(self, days: int = None, product_ids: List[int] = None) -> List[Dict[str, Any]]:
        """Get price history data from database"""
        
        with db_manager.get_session() as session:
            query = session.query(PriceHistory)
            
            # Filter by date range if specified
            if days:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                query = query.filter(PriceHistory.timestamp >= cutoff_date)
            
            # Filter by product IDs if specified
            if product_ids:
                query = query.filter(PriceHistory.product_id.in_(product_ids))
            
            history = query.order_by(PriceHistory.timestamp.desc()).all()
            return [h.to_dict() for h in history]
    
    def get_price_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive price analytics"""
        
        with db_manager.get_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get products with recent activity
            products_query = session.query(Product).filter(
                and_(
                    Product.is_active == True,
                    Product.last_checked >= cutoff_date
                )
            )
            products = products_query.all()
            
            # Get price history for analysis
            history_query = session.query(PriceHistory).filter(
                PriceHistory.timestamp >= cutoff_date
            )
            history = history_query.all()
            
            # Calculate analytics
            analytics = {
                'period_days': days,
                'total_products': len(products),
                'total_price_checks': len(history),
                'products_with_changes': 0,
                'biggest_price_drop': None,
                'biggest_price_increase': None,
                'average_price': 0,
                'stock_changes': {'in_to_out': 0, 'out_to_in': 0},
                'platform_breakdown': {},
                'price_trends': [],
                'generated_at': datetime.utcnow().isoformat()
            }
            
            # Calculate average price
            prices = [p.current_price for p in products if p.current_price]
            if prices:
                analytics['average_price'] = sum(prices) / len(prices)
            
            # Platform breakdown
            for product in products:
                platform = product.platform
                analytics['platform_breakdown'][platform] = analytics['platform_breakdown'].get(platform, 0) + 1
            
            # Analyze price changes for each product
            price_changes = []
            
            for product in products:
                product_history = [h for h in history if h.product_id == product.id]
                if len(product_history) >= 2:
                    # Sort by timestamp
                    product_history.sort(key=lambda x: x.timestamp)
                    
                    first_price = product_history[0].price
                    last_price = product_history[-1].price
                    
                    if first_price and last_price and first_price > 0:
                        change_amount = last_price - first_price
                        change_percent = (change_amount / first_price) * 100
                        
                        change_data = {
                            'product_id': product.id,
                            'product_title': product.title,
                            'first_price': first_price,
                            'last_price': last_price,
                            'change_amount': change_amount,
                            'change_percent': change_percent,
                            'platform': product.platform
                        }
                        
                        price_changes.append(change_data)
                        
                        if abs(change_percent) > 1:  # More than 1% change
                            analytics['products_with_changes'] += 1
            
            # Find biggest changes
            if price_changes:
                # Biggest drop (most negative change)
                biggest_drop = min(price_changes, key=lambda x: x['change_percent'])
                if biggest_drop['change_percent'] < 0:
                    analytics['biggest_price_drop'] = biggest_drop
                
                # Biggest increase (most positive change)
                biggest_increase = max(price_changes, key=lambda x: x['change_percent'])
                if biggest_increase['change_percent'] > 0:
                    analytics['biggest_price_increase'] = biggest_increase
            
            analytics['price_trends'] = sorted(price_changes, key=lambda x: x['change_percent'])
            
            return analytics
    
    def export_to_google_sheets(self, include_history: bool = True, history_days: int = 30) -> bool:
        """Export all data to Google Sheets"""
        
        if not self.google_sheets.is_available():
            logger.warning("Google Sheets not available - skipping export")
            return False
        
        try:
            # Get data
            products = self.get_all_products_data()
            history_data = []
            
            if include_history:
                history_data = self.get_all_price_history(days=history_days)
            
            # Export to Google Sheets
            success = self.google_sheets.update_all_sheets(products, history_data)
            
            if success:
                logger.info("Successfully exported data to Google Sheets")
            else:
                logger.error("Failed to export data to Google Sheets")
            
            return success
            
        except Exception as e:
            logger.error(f"Error exporting to Google Sheets: {e}")
            return False
    
    def export_to_excel(self, export_type: str = "comprehensive", 
                       include_history: bool = True, 
                       history_days: int = 30,
                       filename: str = None) -> Optional[str]:
        """Export data to Excel file"""
        
        try:
            # Get data
            products = self.get_all_products_data()
            history_data = []
            
            if include_history:
                history_data = self.get_all_price_history(days=history_days)
            
            # Export based on type
            if export_type == "products_only":
                filepath = self.excel_exporter.export_products(products, filename)
            elif export_type == "history_only":
                filepath = self.excel_exporter.export_price_history(history_data, filename)
            else:  # comprehensive
                filepath = self.excel_exporter.export_comprehensive_report(products, history_data, filename)
            
            if filepath:
                logger.info(f"Successfully exported data to Excel: {filepath}")
            else:
                logger.error("Failed to export data to Excel")
            
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return None
    
    def run_daily_export(self) -> Dict[str, Any]:
        """Run daily automated export to both Google Sheets and Excel"""
        
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'google_sheets_success': False,
            'excel_success': False,
            'excel_filepath': None,
            'analytics': None
        }
        
        try:
            # Generate analytics
            analytics = self.get_price_analytics(days=7)  # Last 7 days
            results['analytics'] = analytics
            
            # Export to Google Sheets
            results['google_sheets_success'] = self.export_to_google_sheets(
                include_history=True, 
                history_days=30
            )
            
            # Export to Excel with timestamp
            timestamp = datetime.now().strftime("%Y%m%d")
            filename = f"daily_report_{timestamp}.xlsx"
            
            excel_path = self.export_to_excel(
                export_type="comprehensive",
                include_history=True,
                history_days=30,
                filename=filename
            )
            
            if excel_path:
                results['excel_success'] = True
                results['excel_filepath'] = excel_path
            
            logger.info(f"Daily export completed - Google Sheets: {results['google_sheets_success']}, Excel: {results['excel_success']}")
            
        except Exception as e:
            logger.error(f"Error in daily export: {e}")
        
        return results
    
    def cleanup_old_exports(self, keep_days: int = 30) -> int:
        """Clean up old Excel export files"""
        
        try:
            export_dir = self.excel_exporter.get_export_directory()
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            
            cleaned_count = 0
            
            for filename in os.listdir(export_dir):
                if filename.endswith('.xlsx'):
                    filepath = os.path.join(export_dir, filename)
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    
                    if file_mtime < cutoff_date:
                        try:
                            os.remove(filepath)
                            cleaned_count += 1
                            logger.info(f"Removed old export file: {filename}")
                        except Exception as e:
                            logger.error(f"Failed to remove {filename}: {e}")
            
            logger.info(f"Cleaned up {cleaned_count} old export files")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up exports: {e}")
            return 0
    
    def get_product_price_trend(self, product_id: int, days: int = 30) -> Dict[str, Any]:
        """Get detailed price trend for a specific product"""
        
        with db_manager.get_session() as session:
            # Get product info
            product = session.query(Product).filter(Product.id == product_id).first()
            
            if not product:
                return {'error': 'Product not found'}
            
            # Get price history
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            history = session.query(PriceHistory).filter(
                and_(
                    PriceHistory.product_id == product_id,
                    PriceHistory.timestamp >= cutoff_date
                )
            ).order_by(PriceHistory.timestamp.asc()).all()
            
            if not history:
                return {'error': 'No price history found'}
            
            # Calculate trend data
            prices = [h.price for h in history if h.price]
            timestamps = [h.timestamp.isoformat() for h in history]
            
            trend_data = {
                'product_id': product_id,
                'product_title': product.title,
                'platform': product.platform,
                'current_price': product.current_price,
                'target_price': product.target_price,
                'price_history': [h.to_dict() for h in history],
                'summary': {
                    'min_price': min(prices) if prices else None,
                    'max_price': max(prices) if prices else None,
                    'avg_price': sum(prices) / len(prices) if prices else None,
                    'total_checks': len(history),
                    'first_check': history[0].timestamp.isoformat() if history else None,
                    'last_check': history[-1].timestamp.isoformat() if history else None
                }
            }
            
            # Calculate price change
            if len(prices) >= 2:
                first_price = prices[0]
                last_price = prices[-1]
                change_amount = last_price - first_price
                change_percent = (change_amount / first_price) * 100 if first_price > 0 else 0
                
                trend_data['summary']['price_change'] = {
                    'amount': change_amount,
                    'percent': change_percent,
                    'direction': 'up' if change_amount > 0 else 'down' if change_amount < 0 else 'stable'
                }
            
            return trend_data
    
    def get_export_status(self) -> Dict[str, Any]:
        """Get status of export capabilities and recent exports"""
        
        status = {
            'google_sheets_available': self.google_sheets.is_available(),
            'excel_available': True,  # Excel is always available
            'export_directory': self.excel_exporter.get_export_directory(),
            'recent_exports': self.excel_exporter.list_exports()[:10],  # Last 10 exports
            'total_products': 0,
            'total_history_records': 0
        }
        
        # Get data counts
        with db_manager.get_session() as session:
            status['total_products'] = session.query(Product).filter(Product.is_active == True).count()
            status['total_history_records'] = session.query(PriceHistory).count()
        
        return status 