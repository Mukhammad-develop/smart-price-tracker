from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
from typing import Generator
from ..models.product import Base
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv('DATABASE_URL', 'sqlite:///data/price_tracker.db')
        
        # Create engine with appropriate settings
        if self.database_url.startswith('sqlite'):
            self.engine = create_engine(
                self.database_url,
                poolclass=StaticPool,
                connect_args={'check_same_thread': False},
                echo=False
            )
        else:
            self.engine = create_engine(self.database_url, echo=False)
        
        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        self.create_tables()
    
    def create_tables(self):
        """Create all database tables"""
        try:
            # Ensure data directory exists for SQLite
            if self.database_url.startswith('sqlite'):
                db_path = self.database_url.replace('sqlite:///', '')
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_session_direct(self) -> Session:
        """Get database session for direct use (remember to close it)"""
        return self.SessionLocal()
    
    def close(self):
        """Close database connection"""
        self.engine.dispose()

# Global database manager instance
db_manager = DatabaseManager()

# Convenience function for getting sessions
def get_db_session() -> Generator[Session, None, None]:
    """Get database session - convenience function"""
    yield from db_manager.get_session() 