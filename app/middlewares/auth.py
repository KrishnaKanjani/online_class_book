from fastapi import HTTPException, status
from fastapi.params import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.auth import TokenData
from app.middlewares.db import get_database
from app.models.user import User
from app.core.config import jwt_utils, settings
import jwt
from bson import ObjectId

security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

credentials_exception = HTTPException(
   status_code=status.HTTP_401_UNAUTHORIZED,
   detail="Could not validate credentials",
   headers={"WWW-Authenticate": "Bearer"},
)

already_registered_exception = HTTPException(
   status_code=status.HTTP_400_BAD_REQUEST,
   detail="User already registered",
   headers={"WWW-Authenticate": "Bearer"},
)

invalid_creds_exception = HTTPException(
   status_code=status.HTTP_400_BAD_REQUEST,
   detail="Invalid user",
   headers={"WWW-Authenticate": "Bearer"},
)

async def check_if_user_is_registered(
      email: str,
      db: AsyncIOMotorDatabase = Depends(get_database)
   ) -> bool:

   try:
      user = await db.users.find_one({"email": email})
      if user is not None:
         raise already_registered_exception
   
   except jwt.PyJWTError:
      raise credentials_exception

   return False

async def get_current_user(
   credentials: HTTPAuthorizationCredentials = Depends(security),
   db: AsyncIOMotorDatabase = Depends(get_database),
) -> User:
   token = credentials.credentials
   try:
      payload = jwt_utils.decode_token(token)
      user_id = payload.get("user_id")

      if user_id is None:
         raise credentials_exception
      
   except jwt.PyJWTError:
      raise credentials_exception

   user_data = await db.users.find_one({"_id": ObjectId(user_id)})
   if not user_data:
      raise credentials_exception
   user_data["_id"] = str(user_data["_id"])
   return User(**user_data)

async def get_current_teacher(user: User = Depends(get_current_user)) -> User:
   if user.role != "teacher":
      raise HTTPException(status_code=403, detail="Only teachers allowed")
   return user

async def get_current_student(user: User = Depends(get_current_user)) -> User:
   if user.role != "student":
      raise HTTPException(status_code=403, detail="Only students allowed")
   return user
