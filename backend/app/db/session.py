from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event
from app.config import get_settings
import logging

settings = get_settings()
is_sqlite = "sqlite" in settings.DATABASE_URL
connect_args = {"check_same_thread": False, "timeout": 5} if is_sqlite else {}
# Pool explicite pour Postgres (écritures concurrentes sans fichier unique verrouillé)
pool_kwargs = (
    {}
    if is_sqlite
    else {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
    }
)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args=connect_args,
    pool_pre_ping=True,
    **pool_kwargs,
)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

if is_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        try:
            # busy_timeout en premier pour limiter les erreurs "database is locked"
            cursor.execute("PRAGMA busy_timeout=30000;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
        except Exception as e:
            logging.warning(f"SQLite PRAGMA setup skipped due to lock/contention: {e}")
        finally:
            cursor.close()

async def get_db():
    async with SessionLocal() as db:
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise