from pydantic import BaseModel, Field
from datetime import date, time, datetime, timezone
from bson import ObjectId

class Booking(BaseModel):
   student_id: str
   teacher_id: str
   subject: str
   booking_date: datetime
   start_time: datetime
   end_time: datetime
   booked_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

   class Config:
      json_encoders = {ObjectId: str}
