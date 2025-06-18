from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import Request

def get_db_client(request: Request) -> AsyncIOMotorDatabase:
   return request.app.mongodb_client

def get_database(request: Request) -> AsyncIOMotorDatabase:
   return request.app.mongodb
