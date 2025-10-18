from app.cred_loader import cred_loader
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from sqlalchemy.orm import declarative_base, sessionmaker
 
db_creds = cred_loader.db_creds
engine = create_async_engine(
        f"mysql+aiomysql://{db_creds['username']}:{db_creds['password']}@{db_creds['host']}:{db_creds['port']}/{db_creds['schema_name']}",
        echo=False,
    )
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db():
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
            

Base = declarative_base()

