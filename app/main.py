from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from contextlib import asynccontextmanager
from tasks.auto_assign import auto_assign_unbooked_students
from app.endpoints import auth, teachers, students
from fastapi_utils.tasks import repeat_every

@repeat_every(seconds=5 * 60 * 60)  # every 5 hours
async def schedule_auto_assignment():
   await auto_assign_unbooked_students()

@asynccontextmanager
async def lifespan(app: FastAPI):
   app.mongodb_client = AsyncIOMotorClient(settings.MONGO_URI)
   app.mongodb = app.mongodb_client[settings.DB_NAME]
   yield
   app.mongodb_client.close()

app = FastAPI(lifespan=lifespan, title="Online Class Booking API")

# Routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(teachers.router, prefix="/teacher", tags=["Teachers"])
app.include_router(students.router, prefix="/student", tags=["Students"])

@app.get("/")
async def root():
   return {"message": "Welcome to Online Class Booking API"}
