import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from app.config import settings


class Base(DeclarativeBase):
    pass


def normalize_db_url(url: str) -> str:
    # Ensure asyncpg driver
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


engine = create_async_engine(
    normalize_db_url(settings.database_url),
    poolclass=NullPool,          # 🔥 Required for PgBouncer transaction mode
    pool_pre_ping=True,
    connect_args={
        "ssl": ssl_context,
        "statement_cache_size": 0,  # 🔥 Disable asyncpg statement cache
        "prepare_threshold": 0,     # 🔥 Disable asyncpg prepared statements ENTIRELY
    },
    execution_options={
        "compiled_cache": None,     # 🔥 Disable SQLAlchemy compiled cache
    },
)


AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)