"""
Database Initialization Script
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.storage.database import init_db
from app.storage.models import Base
from app.config.settings import get_settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Initialize the database"""
    try:
        settings = get_settings()
        logger.info(f"Initializing database: {settings.database_type}")
        logger.info(f"Database URL: {settings.database_url}")
        
        # Create all tables
        init_db()
        
        logger.info("✅ Database initialized successfully!")
        logger.info(f"Created tables: {', '.join(Base.metadata.tables.keys())}")
        
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
