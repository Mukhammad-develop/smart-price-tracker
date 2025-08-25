import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import os
from ..utils.config import Config

logger = logging.getLogger(__name__)

class GoogleSheetsExporter:
    """Export price tracking data to Google Sheets"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.client = None
        self.spreadsheet = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Sheets client"""
        if not self.config.is_google_sheets_configured():
            logger.warning("Google Sheets not configured - skipping initialization")
            return
        
        try:
            # Define the scope
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Load credentials
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.config.GOOGLE_SHEETS_CREDENTIALS, 
                scope
            )
            
            # Authorize and create client
            self.client = gspread.authorize(creds)
            
            # Open the spreadsheet
            self.spreadsheet = self.client.open_by_key(self.config.GOOGLE_SHEETS_ID)
            
            logger.info("Google Sheets client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")
            self.client = None
            self.spreadsheet = None
    
    def is_available(self) -> bool:
        """Check if Google Sheets integration is available"""
        return self.client is not None and self.spreadsheet is not None
    
    def export_products(self, products: List[Dict[str, Any]], worksheet_name: str = "Products") -> bool:
        """Export products data to Google Sheets"""
        
        if not self.is_available():
            logger.error("Google Sheets not available")
            return False
        
        try:
            # Get or create worksheet
            try:
                worksheet = self.spreadsheet.worksheet(worksheet_name)
                # Clear existing data
                worksheet.clear()
            except gspread.WorksheetNotFound:
                worksheet = self.spreadsheet.add_worksheet(
                    title=worksheet_name, 
                    rows=1000, 
                    cols=20
                )
            
            if not products:
                logger.info("No products to export")
                return True
            
            # Prepare data for export
            df = pd.DataFrame(products)
            
            # Reorder columns for better presentation
            preferred_columns = [
                'id', 'title', 'platform', 'current_price', 'target_price',
                'availability', 'rating', 'review_count', 'seller', 'brand',
                'category', 'last_checked', 'created_at', 'url'
            ]
            
            # Keep only existing columns in preferred order
            columns = [col for col in preferred_columns if col in df.columns]
            remaining_columns = [col for col in df.columns if col not in columns]
            final_columns = columns + remaining_columns
            
            df = df[final_columns]
            
            # Format data for better readability
            df['current_price'] = df['current_price'].apply(
                lambda x: f"${x:.2f}" if pd.notnull(x) else "N/A"
            )
            df['target_price'] = df['target_price'].apply(
                lambda x: f"${x:.2f}" if pd.notnull(x) else "N/A"
            )
            df['availability'] = df['availability'].apply(
                lambda x: "✅ In Stock" if x else "❌ Out of Stock"
            )
            df['rating'] = df['rating'].apply(
                lambda x: f"⭐ {x:.1f}" if pd.notnull(x) else "N/A"
            )
            
            # Convert DataFrame to list of lists for Google Sheets
            values = [df.columns.tolist()] + df.values.tolist()
            
            # Update worksheet
            worksheet.update('A1', values)
            
            # Format headers
            worksheet.format('A1:Z1', {
                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
            })
            
            # Auto-resize columns
            worksheet.columns_auto_resize(0, len(df.columns))
            
            logger.info(f"Successfully exported {len(products)} products to Google Sheets")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export products to Google Sheets: {e}")
            return False
    
    def export_price_history(self, history_data: List[Dict[str, Any]], worksheet_name: str = "Price History") -> bool:
        """Export price history data to Google Sheets"""
        
        if not self.is_available():
            logger.error("Google Sheets not available")
            return False
        
        try:
            # Get or create worksheet
            try:
                worksheet = self.spreadsheet.worksheet(worksheet_name)
                worksheet.clear()
            except gspread.WorksheetNotFound:
                worksheet = self.spreadsheet.add_worksheet(
                    title=worksheet_name, 
                    rows=5000, 
                    cols=10
                )
            
            if not history_data:
                logger.info("No price history to export")
                return True
            
            # Prepare data
            df = pd.DataFrame(history_data)
            
            # Format price column
            if 'price' in df.columns:
                df['price'] = df['price'].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "N/A")
            
            # Format availability
            if 'availability' in df.columns:
                df['availability'] = df['availability'].apply(
                    lambda x: "✅ Available" if x else "❌ Unavailable"
                )
            
            # Convert to list of lists
            values = [df.columns.tolist()] + df.values.tolist()
            
            # Update worksheet
            worksheet.update('A1', values)
            
            # Format headers
            worksheet.format('A1:Z1', {
                'backgroundColor': {'red': 0.9, 'green': 0.6, 'blue': 0.2},
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
            })
            
            # Auto-resize columns
            worksheet.columns_auto_resize(0, len(df.columns))
            
            logger.info(f"Successfully exported {len(history_data)} price history records to Google Sheets")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export price history to Google Sheets: {e}")
            return False
    
    def create_summary_dashboard(self, products: List[Dict[str, Any]], worksheet_name: str = "Dashboard") -> bool:
        """Create a summary dashboard with key metrics"""
        
        if not self.is_available():
            logger.error("Google Sheets not available")
            return False
        
        try:
            # Get or create worksheet
            try:
                worksheet = self.spreadsheet.worksheet(worksheet_name)
                worksheet.clear()
            except gspread.WorksheetNotFound:
                worksheet = self.spreadsheet.add_worksheet(
                    title=worksheet_name, 
                    rows=100, 
                    cols=10
                )
            
            # Calculate summary metrics
            total_products = len(products)
            active_products = len([p for p in products if p.get('is_active', True)])
            in_stock = len([p for p in products if p.get('availability', False)])
            out_of_stock = total_products - in_stock
            
            # Price analysis
            prices = [p.get('current_price') for p in products if p.get('current_price')]
            avg_price = sum(prices) / len(prices) if prices else 0
            
            # Platforms
            platforms = {}
            for product in products:
                platform = product.get('platform', 'Unknown')
                platforms[platform] = platforms.get(platform, 0) + 1
            
            # Create dashboard data
            dashboard_data = [
                ["📊 Smart Price Tracker Dashboard", ""],
                ["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                ["", ""],
                ["📈 Summary Metrics", ""],
                ["Total Products", total_products],
                ["Active Products", active_products],
                ["In Stock", in_stock],
                ["Out of Stock", out_of_stock],
                ["Average Price", f"${avg_price:.2f}" if avg_price > 0 else "N/A"],
                ["", ""],
                ["🛒 By Platform", ""],
            ]
            
            # Add platform breakdown
            for platform, count in platforms.items():
                dashboard_data.append([f"  {platform.title()}", count])
            
            # Add recent price changes (if available)
            dashboard_data.extend([
                ["", ""],
                ["📉 Recent Changes", ""],
                ["(Check Price History sheet for details)", ""]
            ])
            
            # Update worksheet
            worksheet.update('A1', dashboard_data)
            
            # Format title
            worksheet.format('A1', {
                'backgroundColor': {'red': 0.2, 'green': 0.8, 'blue': 0.2},
                'textFormat': {'bold': True, 'fontSize': 14, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
            })
            
            # Format section headers
            for i, row in enumerate(dashboard_data):
                if row[0] and (row[0].startswith('📈') or row[0].startswith('🛒') or row[0].startswith('📉')):
                    worksheet.format(f'A{i+1}', {
                        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
                        'textFormat': {'bold': True}
                    })
            
            # Auto-resize columns
            worksheet.columns_auto_resize(0, 2)
            
            logger.info("Successfully created dashboard in Google Sheets")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create dashboard in Google Sheets: {e}")
            return False
    
    def update_all_sheets(self, products: List[Dict[str, Any]], history_data: List[Dict[str, Any]]) -> bool:
        """Update all sheets with latest data"""
        
        if not self.is_available():
            logger.error("Google Sheets not available")
            return False
        
        success = True
        
        # Export products
        if not self.export_products(products):
            success = False
        
        # Export price history
        if not self.export_price_history(history_data):
            success = False
        
        # Create dashboard
        if not self.create_summary_dashboard(products):
            success = False
        
        return success 