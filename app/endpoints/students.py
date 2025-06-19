from app.models.bookings import Booking
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field
from datetime import timedelta, time, datetime
from app.models.bookings import Booking
from app.models.user import User, UserUpdate
from app.middlewares.db import get_database
from app.middlewares.auth import get_current_student
from bson import ObjectId
import logging

router = APIRouter()

class BookingResponse(Booking):
   success: bool
   message: str
   booking_id: str 

   
@router.get("/me", response_model=User)
async def get_student_profile(current_user: User = Depends(get_current_student)):
   return current_user


@router.patch("/me", response_model=User)
async def update_student_profile(
   data: UserUpdate,
   db: AsyncIOMotorDatabase = Depends(get_database),
   student: User = Depends(get_current_student)
):
   update_fields = {k: v for k, v in data.dict().items() if v is not None}

   if "school_name" in update_fields or "standard" in update_fields:
      if student.role != "student":
         raise HTTPException(status_code=403, detail="Only students can update school/standard info.")

   await db.users.update_one({"_id": ObjectId(student.id)}, {"$set": update_fields})
   updated = await db.users.find_one({"_id": ObjectId(student.id)})
   updated["_id"] = str(updated["_id"])
   return User(**updated)


@router.get("/bookings")
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
               "years_of_exp": teacher.get("years_of_exp")
            }
         })

      return bookings

   except Exception as e:
      raise HTTPException(status_code=500, detail=f"Error fetching bookings: {str(e)}")
    
class BookSlotRequest(BaseModel):
   teacher_id: str = Field(..., example="60f7f72b9e1d8e6b2c5d6e3d")
   slot_start: str = Field(..., example="10:00") # Format: 'HH:MM'

@router.post("/book", response_model=BookingResponse)
async def book_slot(
   request: BookSlotRequest,
   db: AsyncIOMotorDatabase = Depends(get_database),
   student: User = Depends(get_current_student)
):
   """
      Book a class slot for a student.
      Validations:
      - Slot must be available within teacher's availability.
      - Max number of students per slot not exceeded.
      - Student must not have already booked this same slot.
   """
   try:
      logging.info(f"Booking request received: {request.dict()} by student: {student.id}")
      teacher_id = request.teacher_id
      slot_start = request.slot_start

      try:
         hour, minute = map(int, slot_start.split(":"))
         logging.debug(f"Parsed slot time: hour={hour}, minute={minute}")
      except ValueError:
         logging.error("Invalid time format received.")
         raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")

      tomorrow_date = datetime.now().date() + timedelta(days=1)
      slot_start_dt = datetime.combine(tomorrow_date, time(hour, minute))
      slot_end_dt = slot_start_dt + timedelta(hours=1)
      booking_date_dt = datetime.combine(tomorrow_date, time.min)

      logging.info(f"Attempting to book for teacher {teacher_id} on {booking_date_dt} from {slot_start_dt} to {slot_end_dt}")

      availabilities = await db.teacher_availabilities.find({
         "teacher_id": teacher_id,
         "available_date": booking_date_dt
      }).to_list(length=10)

      if not availabilities:
         logging.warning(f"No availability found for teacher {teacher_id} on {booking_date_dt}")
         raise HTTPException(status_code=404, detail="No availability found for this teacher.")

      matched_availability = None
      for availability in availabilities:
         if availability["start_time"] <= slot_start_dt < availability["end_time"]:
            matched_availability = availability
            break

      if not matched_availability:
         logging.warning(f"Slot time {slot_start_dt} not within any availability for teacher {teacher_id}")
         raise HTTPException(status_code=400, detail="Time not within any of the teacher's available slots")

      logging.info(f"Matched availability found: {matched_availability}")

      existing_bookings = await db.class_bookings.find({
         "teacher_id": teacher_id,
         "booking_date": booking_date_dt,
         "start_time": slot_start_dt,
         "end_time": slot_end_dt,
         "subject": matched_availability["subject"]
      }).to_list(length=100)

      max_allowed = matched_availability.get("max_no_of_students_each_slot", 1)
      logging.debug(f"Existing bookings: {len(existing_bookings)} / {max_allowed}")

      if len(existing_bookings) >= max_allowed:
         logging.warning("Booking failed: slot already full.")
         raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Slot already full. Max {max_allowed} students allowed."
         )

      duplicate_booking = await db.class_bookings.find_one({
         "student_id": str(student.id),
         "teacher_id": teacher_id,
         "booking_date": booking_date_dt,
         "start_time": slot_start_dt
      })
      if duplicate_booking:
         logging.warning(f"Duplicate booking attempt by student {student.id} for slot {slot_start_dt}")
         raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already booked this slot."
         )

      booking = Booking(
         student_id=str(student.id),
         teacher_id=teacher_id,
         subject=availability["subject"],
         booking_date=booking_date_dt,
         start_time=slot_start_dt,
         end_time=slot_end_dt
      )
      result = await db.class_bookings.insert_one(booking.model_dump())
      logging.info(f"Booking successful: {str(result.inserted_id)}")
      
      return {
         "success": True,
         "message": "Slot Booked successfully",
         **booking.model_dump(exclude=('_id')),
         "booking_id": str(result.inserted_id)
      }

   except HTTPException as httpex:
      logging.error(f"HTTPException during booking: {httpex.detail}")
      raise httpex

   except Exception as e:
      logging.exception("Unhandled exception occurred while booking.")
      raise HTTPException(
         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
         detail=f"Error booking this slot: {str(e)}"
      )
@router.post("/slot/pay", status_code=200)
async def mark_slot_booking_paid(
   booking_id: str = Query(..., example="60f7f72b9e1d8e6b2c5d6e3d"),
   db: AsyncIOMotorDatabase = Depends(get_database)
):
   """
      This endpoint assumes that a booking with the provided ID exists and updates its payment status.

      In production, this should be called after successful payment (e.g., via Razorpay/Stripe webhook).
      We could trigger this from your payment success callback.

      Fields Updated:
      - `fees_paid = True`
      - `payment_timestamp = current timestamp`

      Parameters:
      - booking_id (str): The ID of the booking to mark as paid.
   """
   try:
      booking = await db.class_bookings.find_one({"_id": ObjectId(booking_id)})

      if not booking:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

      await db.class_bookings.update_one(
         {"_id": ObjectId(booking_id)},
         {
            "$set": {
               "is_paid": True,
               "payment_timestamp": datetime.now()
            }
         }
      )

      return {"success": True, "message": "Booking marked as paid."}

   except HTTPException as httpex:
      raise httpex
   
   except Exception as e:
      raise HTTPException(
         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
         detail=f"Failed to mark booking as paid: {str(e)}"
      )


@router.delete("/booking/{booking_id}", status_code=204)
async def cancel_booking(
   booking_id: str = Path(..., example="60f7f72b9e1d8e6b2c5d6e3d"),
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
      return {"success": True, "message": "Booking deleted successfully"}

   except HTTPException as httpex:
      raise httpex
   
   except Exception as e:
      raise HTTPException(status_code=500, detail=f"Error cancelling booking: {str(e)}")