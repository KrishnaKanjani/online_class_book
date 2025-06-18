from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.auth import LoginRequest, Token, RefreshToken
from app.models.user import UserCreate, User
from app.core.config import authorization_utils, jwt_utils
from app.middlewares.db import get_database
from app.middlewares.auth import check_if_user_is_registered, get_current_user

router = APIRouter()

@router.post("/register", response_model=Token)
async def register_user(
      user: UserCreate,
      db: AsyncIOMotorDatabase = Depends(get_database)
   ):
   try:
      user_already_not_resgisterd = check_if_user_is_registered(db, user.email),
      if not user_already_not_resgisterd:
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="This shouldn't be happening, we're taking a look...",
            headers={"WWW-Authenticate": "Bearer"},
        )

      hashed_pwd = authorization_utils.get_password_hash(user.password)

      user_data = user.dict()
      user_data["hashed_password"] = hashed_pwd
      user_data.pop("password")

      if user.role.value == "teacher" and not user.subject:
         raise HTTPException(status_code=422, detail="Teacher must provide a subject")
      
      new_user = User(**user_data)
      result = await db.users.insert_one(new_user.model_dump())

      access_token = jwt_utils.create_access_token(
         data={"email": user.email, "user_id": str(result.inserted_id), "role": user.role.value}
      )

      return {"access_token": access_token, "token_type": "bearer"}

   except Exception as e:
      raise HTTPException(
         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
         detail=f"Some error occured: {str(e)}"
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
   

@router.get("/me", response_model=User)
async def get_profile(current_user: User = Depends(get_current_user)):
   return current_user
