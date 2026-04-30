"""
Database Connection Management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from contextlib import contextmanager, asynccontextmanager
from typing import Generator, AsyncGenerator
import logging

from app.config.settings import get_settings
from app.storage.models import Base

logger = logging.getLogger(__name__)
settings = get_settings()


# Synchronous engine and session
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Asynchronous engine and session (for async operations)
if settings.database_type == "postgresql":
    async_database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
elif settings.database_type == "sqlite":
    async_database_url = settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
else:
    async_database_url = settings.database_url

async_engine = create_async_engine(
    async_database_url,
    echo=settings.debug,
    pool_pre_ping=True
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


async def init_db_async():
    """Initialize database tables asynchronously"""
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully (async)")
    except Exception as e:
        logger.error(f"Error creating database tables (async): {e}")
        raise


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Get database session (synchronous)
    
    Usage:
        with get_db() as db:
            # use db session
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@asynccontextmanager
async def get_db_async() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session (asynchronous)
    
    Usage:
        async with get_db_async() as db:
            # use db session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_db_session() -> Session:
    """
    Dependency for FastAPI endpoints (synchronous)
    
    Usage:
        @app.get("/")
        def endpoint(db: Session = Depends(get_db_session)):
            # use db
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_db_session_async() -> AsyncSession:
    """
    Dependency for FastAPI endpoints (asynchronous)
    
    Usage:
        @app.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db_session_async)):
            # use db
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_db():
    """Close database connections"""
    await async_engine.dispose()
    engine.dispose()
    logger.info("Database connections closed")

# Made with Bob
