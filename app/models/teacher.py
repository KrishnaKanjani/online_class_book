from pydantic import EmailStr, BaseModel, Field, model_validator
from datetime import datetime, timedelta

class TeacherAvailability(BaseModel):
   teacher_id: str = Field(..., description="MongoDB ObjectID of the teacher", example="665e3dcf6dd8e693cefa77c2")
   subject: str = Field(..., example="Mathematics")
   available_date: datetime = Field(..., example="2025-06-21T00:00:00")
   start_time: datetime = Field(..., example="2025-06-21T10:00:00")
   end_time: datetime = Field(..., example="2025-06-21T12:00:00")
   max_no_of_students_each_slot: int = Field(default=1, example=2)

   @model_validator(mode='after')
   def validate_date_and_time(cls, values):
      today = datetime.now().date()
      tomorrow = today + timedelta(days=1)
      available_date = values.available_date
      start = values.start_time
      end = values.end_time
      
      if available_date.date() != tomorrow:
         raise ValueError("You can only set availability for the next day.")
      if start >= end:
         raise ValueError("Start time must be before end time.")
      return values


class TeacherInfo(BaseModel):
   id: str = Field(alias="_id", example="665e3dcf6dd8e693cefa77c2")
   first_name: str = Field(..., example="John")
   last_name: str = Field(..., example="Doe")
   email: EmailStr = Field(..., example="john.doe@example.com")
   subject: str = Field(..., example="Science")

   class Config:
      populate_by_name = True
