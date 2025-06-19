from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, EmailStr, Field
from app.models.auth import LoginRequest, Token, RefreshToken
from app.models.user import UserCreate, User
from app.core.config import authorization_utils, jwt_utils
from app.middlewares.db import get_database
from app.middlewares.auth import check_if_user_is_registered
from bson import ObjectId
import logging

router = APIRouter()

@router.post("/register", response_model=Token)
async def register_user(
      user: UserCreate,
      db: AsyncIOMotorDatabase = Depends(get_database)
   ):
   result = None
   try:
      logging.info(f"Registration request received for email: {user.email}, role: {user.role}")

      user_already_not_resgisterd = await check_if_user_is_registered(user.email, db)
      if not user_already_not_resgisterd:
         logging.warning(f"User with email {user.email} is already registered.")
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="This shouldn't be happening, we're taking a look...",
            headers={"WWW-Authenticate": "Bearer"},
         )

      # Role-specific validations
      if user.role == "teacher":
         if not user.subject:
            logging.error("Teacher registration failed: Subject missing.")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Teacher must provide a subject")
         if not user.years_of_exp:
            logging.error("Teacher registration failed: Years of experience missing.")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Teacher must provide years of experience")

      if user.role == "student":
         if not user.school_name:
            logging.error("Student registration failed: School name missing.")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Student must provide school name")
         if not user.standard:
            logging.error("Student registration failed: Current standard missing.")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Student must provide their current standard")
         if not user.previuos_standard_result:
            logging.error("Student registration failed: Previous standard result missing.")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Student must provide result of previous standard (in %)")

      # Validate password strength
      logging.info("Validating password strength.")
      authorization_utils.validate_password_strength(user.password)

      # Hash password and prepare user data
      hashed_pwd = authorization_utils.get_password_hash(user.password)
      user_data = user.model_dump()
      user_data["hashed_password"] = hashed_pwd
      user_data.pop("password")
      new_user = {**user_data}

      logging.info(f"Inserting new user into database for email: {user.email}")
      result = await db.users.insert_one(new_user)

      access_token = jwt_utils.create_access_token(
         data={"email": user.email, "user_id": str(result.inserted_id), "role": user.role}
      )
      logging.info(f"User registered successfully: {user.email} | ID: {result.inserted_id}")

      return {"access_token": access_token, "token_type": "bearer"}
   
   except HTTPException as httpex:
      if result:
         logging.warning(f"Cleaning up user due to HTTPException: {result.inserted_id}")
         await db.users.delete_one({"_id": ObjectId(result.inserted_id)})   
      raise httpex
   
   except Exception as e:
      if result:
         logging.exception(f"Unexpected error occurred. Cleaning up user: {result.inserted_id}")
         await db.users.delete_one({"_id": ObjectId(result.inserted_id)})  
      raise HTTPException(
         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
         detail=f"Some error occurred: {str(e)}"
      )

@router.post("/login", response_model=Token)
async def login_user(
      data: LoginRequest,
      db: AsyncIOMotorDatabase = Depends(get_database)
   ):
   user = await db.users.find_one({"email": data.email})
   
   if not user or not authorization_utils.verify_password(data.password, user["hashed_password"]):
      raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

   token = jwt_utils.create_access_token(
      data={"email": user["email"], "user_id": str(user["_id"]), "role": user["role"]}
   )
   return {"access_token": token, "token_type": "bearer"}


class ResetPasswordRequest(BaseModel):
   email: EmailStr = Field(..., example="student1@example.com")
   old_password: str = Field(..., example="OldPass123!")
   new_password: str = Field(
      ..., 
      min_length=8, 
      example="NewStrongPass@456", 
      description="Must be at least 8 characters with 1 capital letter, 2 numbers, and 1 special character"
   )

@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
   req: ResetPasswordRequest,
   db: AsyncIOMotorDatabase = Depends(get_database)
):
   """
      Reset password securely.
   """
   try:
      user = await db.users.find_one({"email": req.email})
      if not user:
         raise HTTPException(status_code=404, detail="User not found")

      if req.old_password == req.new_password:
         raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Old and New password can not be same. Choose a different password")
            
      if not authorization_utils.verify_password(req.old_password, user.get("hashed_password", "")):
         raise HTTPException(status_code=401, detail="Old password is incorrect")

      # Validate password strength
      authorization_utils.validate_password_strength(req.new_password)

      new_hashed = authorization_utils.get_password_hash(req.new_password)

      result = await db.users.update_one(
         {"_id": user["_id"]},
         {"$set": {"hashed_password": new_hashed}}
      )

      if result.modified_count != 1:
         raise HTTPException(status_code=500, detail="Password reset failed. Try again later.")

      return {"success": True, "message": "Password reset successful."}
   
   except HTTPException as httpex:
      raise httpex
   
   except Exception as e:
      raise HTTPException(
      status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Error in reseting password: {str(e)}"
      )

@router.post("/refresh", response_model=Token)
async def refresh_access_token(payload: RefreshToken):
   try:
      decoded = jwt_utils.verify_refresh_token(payload.refresh_token)

      new_access_token = jwt_utils.create_refresh_token(
         data={
            "email": decoded["email"],
            "user_id": decoded["user_id"],
            "role": decoded["role"]
         }
      )

      return {"access_token": new_access_token, "token_type": "bearer"}

   except Exception as e:
      raise HTTPException(status_code=500, detail=f"Could not refresh token: {str(e)}")

