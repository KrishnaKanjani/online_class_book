from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, time, datetime, timezone
from bson import ObjectId

class Booking(BaseModel):
   student_id: str = Field(..., example="665e3dcf6dd8e693cefa77c4")
   teacher_id: str = Field(..., example="665e3dcf6dd8e693cefa77c2")
   subject: str = Field(..., example="Mathematics")
   booking_date: datetime = Field(..., example="2025-06-21T00:00:00")
   start_time: datetime = Field(..., example="2025-06-21T10:00:00")
   end_time: datetime = Field(..., example="2025-06-21T11:00:00")
   booked_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc), example="2025-06-20T18:00:00+00:00")
   fees_paid: bool = Field(default=False, example=False)
   payment_timestamp: Optional[datetime] = Field(default=None, example="2025-06-20T19:30:00+00:00")

   class Config:
      json_encoders = {ObjectId: str}
