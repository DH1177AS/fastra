from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from fastra_security.crypto.key_derivation import derive_encryption_key

engine = None
async_session_factory = None

class Base(DeclarativeBase):
    pass

async def init_encrypted_db(master_password: str, db_url: str = None):
    global engine, async_session_factory
    if db_url is None:
        db_url = "sqlite+aiosqlite:///./secure_snapbuild.db"
    key = derive_encryption_key(master_password)
    engine = create_async_engine(db_url, echo=False)
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_encrypted_session():
    async with async_session_factory() as session:
        yield session