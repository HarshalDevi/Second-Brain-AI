import ssl

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


def _async_db_url(url: str) -> str:
    # Accept both:
    #  - postgresql://
    #  - postgres://
    # Convert to asyncpg.
    u = url.replace("postgres://", "postgresql://")
    if u.startswith("postgresql+asyncpg://"):
        return u
    if u.startswith("postgresql://"):
        return u.replace("postgresql://", "postgresql+asyncpg://", 1)
    return u


# --- SSL FIX FOR SUPABASE POOLER ---
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
# ---------------------------------


engine = create_async_engine(
    _async_db_url(settings.database_url),
    pool_pre_ping=True,
    connect_args={
        "ssl": ssl_context
    },
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)