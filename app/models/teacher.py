from pydantic import EmailStr, BaseModel, Field, model_validator
from datetime import datetime, time, timedelta, date
from bson import ObjectId

class TeacherAvailability(BaseModel):
   teacher_id: str = Field(..., description="MongoDB ObjectID of the teacher")
   subject: str
   available_date: datetime
   start_time: datetime
   end_time: datetime

   @model_validator(mode='before')
   def validate_date_and_time(cls, values):
      today = datetime.now().date()
      tomorrow = today + timedelta(days=1)
      available_date = values.get('available_date')
      start = values.get('start_time')
      end = values.get('end_time')

      if available_date.date() != tomorrow:
         raise ValueError("You can only set availability for the next day.")
      if start >= end:
         raise ValueError("Start time must be before end time.")
      return values


class TeacherInfo(BaseModel):
   id: str = Field(alias="_id")
   first_name: str
   last_name: str
   email: EmailStr
   subject: str
   
   class Config:
      populate_by_name = True