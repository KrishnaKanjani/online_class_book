from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime, timezone
from bson import ObjectId
from enum import Enum

class UserRoleEnum(Enum):
   TEACHER = 'teacher'
   STUDENT = 'student'

class UserBase(BaseModel):
   first_name: str = Field(..., min_length=1, max_length=50)
   last_name: str = Field(..., min_length=1, max_length=50)
   email: EmailStr
   phone: str = Field(..., pattern=r'^\+?1?\d{9,15}$')
   age: int = Field(..., ge=13, le=100)
   role: UserRoleEnum = Field(default=UserRoleEnum.STUDENT)
   is_active: bool = Field(default_factory=lambda: True)
   created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
   updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

   class Config:
      populate_by_name = True
      arbitrary_types_allowed = True
      json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}

class UserCreate(UserBase):
   password: str = Field(..., min_length=8)
   subject: Optional[str] = Field(None, max_length=100)  # Only for teachers

    
class User(UserBase):
   id: str = Field(default_factory=ObjectId, alias="_id")
   # id: str = Field(alias="_id")
   subject: Optional[str] = None
   created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
   updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

