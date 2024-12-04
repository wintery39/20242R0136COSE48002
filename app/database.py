from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

engine = create_async_engine(DATABASE_URL)

# 비동기 세션 생성
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
)

# 비동기 세션을 반환하는 get_db 함수
async def get_db():
    async with AsyncSessionLocal() as db:
        yield db