import pytest
from httpx import AsyncClient
from app.main import app  # your FastAPI app
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    return asyncio.get_event_loop()

@pytest.fixture(scope="session")
async def client():
   async with AsyncClient(app=app, base_url="http://testserver") as ac:
      yield ac

@pytest.fixture(scope="session")
async def db():
   client = AsyncIOMotorClient(settings.MONGO_URI)
   db = client[settings.DB_NAME]
   yield db
   await client.drop_database(settings.DB_NAME)
