from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime, timezone
from bson import ObjectId
from enum import Enum

class UserRoleEnum(Enum):
   TEACHER = 'teacher'
   STUDENT = 'student'


class UserBase(BaseModel):
   first_name: str = Field(..., min_length=1, max_length=50, example="Krishna")
   last_name: str = Field(..., min_length=1, max_length=50, example="kanjani")
   email: EmailStr = Field(..., example="krishna.kanjani@example.com")
   phone: str = Field(..., pattern=r'^\+?1?\d{9,15}$', example="+919900000000")
   age: int = Field(..., ge=13, le=100, example=20)
   role: UserRoleEnum = Field(default=UserRoleEnum.STUDENT, example="student")
   is_active: bool = Field(default_factory=lambda: True, example=True)
   created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc), example=datetime.now(tz=timezone.utc))
   updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc), example=datetime.now(tz=timezone.utc))

   class Config:
      populate_by_name = True
      arbitrary_types_allowed = True
      use_enum_values = True
      json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class UserCreate(UserBase):
   password: str = Field(..., example="StrongPass@123")
   subject: Optional[str] = Field(None, max_length=100, example="Mathematics")  # Only for teachers
   years_of_exp: Optional[float] = Field(None, example=2.5)   # Only for teachers

   school_name: Optional[str] = Field(None, example="Sunshine Public School")   # Only for students
   standard: Optional[str] = Field(None, example="10th")   # Only for students
   previuos_standard_result: Optional[float] = Field(None, example=88.6)   # Only for students


class UserUpdate(BaseModel):
   first_name: Optional[str] = Field(None, example="Johnny")
   last_name: Optional[str] = Field(None, example="Doe")
   phone: Optional[str] = Field(None, example="+919988887777")
   email: Optional[EmailStr] = Field(None, example="johnny.doe@example.com")
   age: int = Field(..., ge=13, le=100, example=20)
   # For teacher
   subject: Optional[str] = Field(None, example="Science")
   years_of_exp: Optional[int] = Field(None, example=3)
   # For student
   school_name: Optional[str] = Field(None, example="St. Xavier's High School")
   standard: Optional[str] = Field(None, example="9th")
   previuos_standard_result: Optional[float] = Field(None, example=91.5)

   class Config:
      json_schema_extra = {
         "example": {
            "first_name": "Alice",
            "last_name": "Doe",
            "email": "alice@example.com",
            "age": 24,
            "phone": "+911234567890",
            # For teacher
            "subject": "Mathematics",
            "years_of_exp": 5,
            # For student
            "school_name": "Bluebell High",
            "standard": "12th",
            "previuos_standard_result": 91.2

         }
      }
    
class User(UserBase):
   id: str = Field(alias="_id", example="665e3dcf6dd8e693cefa77c2")
   subject: Optional[str] = Field(None, example="Physics")
   created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc), example=datetime.now(tz=timezone.utc))
   updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc), example=datetime.now(tz=timezone.utc))

   class Config:
      json_encoders = {ObjectId: str}
