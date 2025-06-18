from app.models.bookings import Booking
from pydantic import Field
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import date, timedelta, time, datetime
from app.models.bookings import Booking
from app.models.user import User
from app.middlewares.db import get_database
from app.middlewares.auth import get_current_student
from bson import ObjectId

router = APIRouter()

class BookingResponse(Booking):
   id: str = Field(alias="_id")

@router.get("/students/bookings")
async def get_student_bookings(
   db: AsyncIOMotorDatabase = Depends(get_database),
   student: User = Depends(get_current_student)
):
   try:
      today = datetime.now()
      bookings_cursor = db.class_bookings.find({
         "student_id": str(student.id),
         "booking_date": {"$gte": today}
      })

      bookings = []
      async for booking in bookings_cursor:
         teacher = await db.users.find_one({"_id": ObjectId(booking["teacher_id"])})
         bookings.append({
            "booking_id": str(booking["_id"]),
            "booking_date": str(booking["booking_date"]),
            "start_time": booking["start_time"].strftime("%H:%M"),
            "end_time": booking["end_time"].strftime("%H:%M"),
            "teacher": {
               "first_name": teacher.get("first_name"),
               "last_name": teacher.get("last_name"),
               "email": teacher.get("email"),
               "subject": teacher.get("subject"),
            }
         })

      return bookings

   except Exception as e:
      raise HTTPException(status_code=500, detail=f"Error fetching bookings: {str(e)}")
    
@router.post("/booking", response_model=BookingResponse)
async def book_slot(
   teacher_id: str,
   slot_start: str, # Format: 'HH:MM'
   db: AsyncIOMotorDatabase = Depends(get_database),
   student: User = Depends(get_current_student)
):
   # Parse slot start as datetime
   try:
      hour, minute = map(int, slot_start.split(":"))
   except ValueError:
      raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")

   # Compose full datetime objects for tomorrow's date and times
   tomorrow_date = datetime.now().date() + timedelta(days=1)
   slot_start_dt = datetime.combine(tomorrow_date, time(hour, minute))
   slot_end_dt = slot_start_dt + timedelta(hours=1)
   
   # Check if teacher exists and has availability
   availability = await db.teacher_availabilities.find_one({
      "teacher_id": teacher_id,
      "available_date": datetime.combine(tomorrow_date, time.min)
   })
   if not availability:
      raise HTTPException(status_code=404, detail="No availability for this teacher")

   # Check if slot is within range
   if not (availability["start_time"] <= slot_start_dt < availability["end_time"]):
      raise HTTPException(status_code=400, detail="Time not within available range")

   slot_end = time(slot_start.hour + 1, 0)

   # Check if already booked
   conflict = await db.class_bookings.find_one({
      "teacher_id": teacher_id,
      "booking_date": datetime.combine(tomorrow_date, time.min),
      "start_time": slot_start_dt
   })
   if conflict:
      raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slot already booked")

   # Check if student already booked
   student_conflict = await db.class_bookings.find_one({
      "student_id": str(student.id),
      "booking_date": datetime.combine(tomorrow_date, time.min)
   })
   if student_conflict:
      raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You've already booked a class")

   # Create booking
   booking = Booking(
      student_id=str(student.id),
      teacher_id=teacher_id,
      subject=availability["subject"],
      booking_date=datetime.combine(tomorrow_date, time.min),
      start_time=slot_start,
      end_time=slot_end
   )
   result = await db.class_bookings.insert_one(booking.model_dump())
   return {**booking.dict(), "_id": str(result.inserted_id)}

@router.delete("/booking/{booking_id}", status_code=204)
async def cancel_booking(
   booking_id: str,
   db: AsyncIOMotorDatabase = Depends(get_database),
   student = Depends(get_current_student)
):
   try:
      if not ObjectId.is_valid(booking_id):
         raise HTTPException(status_code=400, detail="Invalid booking ID")

      booking = await db.class_bookings.find_one({"_id": ObjectId(booking_id)})

      if not booking:
         raise HTTPException(status_code=404, detail="Booking not found")

      if booking["student_id"] != str(student.id):
         raise HTTPException(status_code=403, detail="Not allowed to cancel others' bookings")

      await db.class_bookings.delete_one({"_id": ObjectId(booking_id)})
      return 

   except Exception as e:
      raise HTTPException(status_code=500, detail=f"Error cancelling booking: {str(e)}")