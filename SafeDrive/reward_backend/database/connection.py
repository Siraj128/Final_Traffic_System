from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from utils.config import Config

# SQLITE_URL must start with sqlite+aiosqlite:// for async support
SQLITE_URL = Config.SQLITE_URL
if SQLITE_URL.startswith("sqlite://"):
    SQLITE_URL = SQLITE_URL.replace("sqlite://", "sqlite+aiosqlite://")

engine = create_async_engine(
    SQLITE_URL, connect_args={"check_same_thread": False}
)

AsyncSessionLocal = async_sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()
