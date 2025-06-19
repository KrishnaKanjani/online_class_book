from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings, cors_origins
from contextlib import asynccontextmanager
from tasks.auto_assign import auto_assign_unbooked_students
from app.endpoints import auth, teachers, students, slots
from fastapi_utils.tasks import repeat_every
from fastapi.openapi.utils import get_openapi

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

app.add_middleware(
   CORSMiddleware,
   allow_origins=cors_origins, 
   allow_credentials=True,
   allow_methods=["*"],
   allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(teachers.router, prefix="/teacher", tags=["Teachers"])
app.include_router(slots.router, prefix="/slots", tags=["Slots"])
app.include_router(students.router, prefix="/student", tags=["Students"])


@app.get("/")
async def root():
   return {"message": "Welcome to Online Class Booking API. Please go to /docs to get the API list"}

@app.get("/health")
async def root():
   return {"message": "Application status healthy"}


def custom_openapi():
   # if app.openapi_schema:
   #    return app.openapi_schema
   openapi_schema = get_openapi(
      title="Online Class Booking System",
      version="0.0.5",
      description="",
      routes=app.routes,
   )
   openapi_schema["info"]["x-logo"] = {
      "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
   }
   app.openapi_schema = openapi_schema
   return app.openapi_schema
