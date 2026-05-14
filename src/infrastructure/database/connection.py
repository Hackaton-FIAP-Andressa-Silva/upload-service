from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from src.infrastructure.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncSession:
    async with AsyncSessionFactory() as session:
        yield session
