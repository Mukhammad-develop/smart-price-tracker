from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any

Base = declarative_base()

class Product(Base):
    """Product model for storing tracked product information"""
    
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(1000), nullable=False, unique=True)
    platform = Column(String(50), nullable=False)  # amazon, ebay, walmart, etc.
    title = Column(String(500))
    current_price = Column(Float)
    target_price = Column(Float)
    availability = Column(Boolean, default=True)
    rating = Column(Float)
    review_count = Column(Integer)
    seller = Column(String(200))
    image_url = Column(String(1000))
    product_id = Column(String(100))  # Platform-specific product ID
    category = Column(String(100))
    brand = Column(String(100))
    
    # Tracking settings
    is_active = Column(Boolean, default=True)
    track_price = Column(Boolean, default=True)
    track_availability = Column(Boolean, default=True)
    track_rating = Column(Boolean, default=False)
    
    # User settings
    user_cost_price = Column(Float)  # For profit calculation
    notification_enabled = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_checked = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<Product(id={self.id}, title='{self.title[:50]}...', price={self.current_price})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert product to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'url': self.url,
            'platform': self.platform,
            'title': self.title,
            'current_price': self.current_price,
            'target_price': self.target_price,
            'availability': self.availability,
            'rating': self.rating,
            'review_count': self.review_count,
            'seller': self.seller,
            'image_url': self.image_url,
            'product_id': self.product_id,
            'category': self.category,
            'brand': self.brand,
            'is_active': self.is_active,
            'user_cost_price': self.user_cost_price,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_checked': self.last_checked.isoformat() if self.last_checked else None
        }

class PriceHistory(Base):
    """Model for storing historical price data"""
    
    __tablename__ = 'price_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, nullable=False, index=True)
    price = Column(Float, nullable=False)
    availability = Column(Boolean, nullable=False)
    rating = Column(Float)
    review_count = Column(Integer)
    seller = Column(String(200))
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<PriceHistory(product_id={self.product_id}, price={self.price}, timestamp={self.timestamp})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert price history to dictionary"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'price': self.price,
            'availability': self.availability,
            'rating': self.rating,
            'review_count': self.review_count,
            'seller': self.seller,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class Alert(Base):
    """Model for storing alert configurations and history"""
    
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)  # price_drop, stock_change, rating_change
    condition_value = Column(Float)  # Target price, rating threshold, etc.
    is_active = Column(Boolean, default=True)
    notification_methods = Column(String(200))  # comma-separated: email,telegram,slack
    last_triggered = Column(DateTime(timezone=True))
    trigger_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Alert(product_id={self.product_id}, type={self.alert_type}, value={self.condition_value})>" 