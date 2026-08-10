import ssl
from uuid import uuid4
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

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


def pgbouncer_safe_url(url: str) -> str:
    parsed = urlsplit(normalize_db_url(url))
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.setdefault("prepared_statement_cache_size", "0")
    return urlunsplit(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            urlencode(query),
            parsed.fragment,
        )
    )


ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


engine = create_async_engine(
    pgbouncer_safe_url(settings.database_url),
    poolclass=NullPool,
    pool_pre_ping=True,
    connect_args={
        "ssl": ssl_context,
        "statement_cache_size": 0,
        "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
    },
    execution_options={
        "compiled_cache": None,
    },
)


AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
