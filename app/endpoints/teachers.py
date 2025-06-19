from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.teacher import TeacherAvailability
from app.middlewares.db import get_database
from app.middlewares.auth import get_current_teacher
from app.models.user import User, UserUpdate
from app.core.response_validation import custom_jsonable_encoder
from bson import ObjectId
from datetime import timedelta, datetime, time
from collections import defaultdict

router = APIRouter()

class AvailabilityResponse(TeacherAvailability):
   success: bool
   message: str
   id: str 

   class Config:
      json_encoders = {ObjectId: str}

   
@router.get("/me", response_model=User)
async def get_teacher_profile(current_user: User = Depends(get_current_teacher)):
   return current_user


@router.patch("/me", response_model=User)
async def update_teacher_profile(
   data: UserUpdate,
   db: AsyncIOMotorDatabase = Depends(get_database),
   teacher: User = Depends(get_current_teacher)
):
   update_fields = {k: v for k, v in data.dict().items() if v is not None}
   print(teacher.id)
   if "subject" in update_fields or "years_of_exp" in update_fields:
      if teacher.role != "teacher":
         raise HTTPException(status_code=403, detail="Only teachers can update subject or experience.")

   await db.users.update_one({"_id": ObjectId(teacher.id)}, {"$set": update_fields})
   updated = await db.users.find_one({"_id": ObjectId(teacher.id)})
   updated["_id"] = str(updated["_id"])
   return User(**updated)


@router.post("/availability", response_model=AvailabilityResponse)
async def set_availability(
   data: TeacherAvailability,
   db: AsyncIOMotorDatabase = Depends(get_database),
   teacher: User = Depends(get_current_teacher)
):
   try:
      # Ensure teacher is setting their own availability
      if str(teacher.id) != data.teacher_id:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized teacher ID")

      # Normalize availability date to midnight datetime
      availability_date = datetime.combine(data.available_date.date(), time.min)

      # Check if the teacher already has an overlapping availability for the same day
      overlap_exists = await db.teacher_availabilities.find_one({
         "teacher_id": data.teacher_id,
         "available_date": availability_date,
         "$or": [
            {
               "start_time": {"$lt": data.end_time},
               "end_time": {"$gt": data.start_time}
            }
         ]
      })
      if overlap_exists:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Availability overlaps with an existing slot"
         )

      # Prepare document with datetime normalization
      availability_doc = {
         **data.dict(),
         "available_date": availability_date,
      }
      result = await db.teacher_availabilities.insert_one(availability_doc)
      return {"id": str(result.inserted_id), "success": True, "message": "Availability set successfully", "data": data.dict()}
   
   except HTTPException as httpex:
      raise httpex
   
   except Exception as e:
      raise HTTPException(
         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
         detail=f"Error setting availability: {str(e)}"
      )


@router.get("/available_slots", response_model=Dict)
async def get_my_available_slots(
   db: AsyncIOMotorDatabase = Depends(get_database),
   teacher: User = Depends(get_current_teacher)
):
   try:
      # Get tomorrow's date as datetime object at 00:00
      tomorrow = datetime.combine(datetime.now().date() + timedelta(days=1), time.min)

      # Query availability of current teacher for tomorrow
      availabilities = db.teacher_availabilities.find({
         "teacher_id": str(teacher.id),
         "available_date": tomorrow
      })

      if availabilities:
         return {
            "success": True,
            "message": "Availability found for the logged-in teacher.",
            "available_slots": [custom_jsonable_encoder(availability) async for availability in availabilities]
         }
      else:
         return {
            "success": False,
            "message": "No availability found for the logged-in teacher.",
            "available_slots": {}
         }

   except Exception as e:
      raise HTTPException(
         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
         detail=f"Failed to fetch teacher availability: {str(e)}"
      )


@router.get("/bookings", response_model=list)
async def view_my_student_registeration(
   db: AsyncIOMotorDatabase = Depends(get_database),
   teacher: User = Depends(get_current_teacher)
):
   """
      Returns all class bookings for tomorrow for the logged-in teacher, grouped by their time slots.
   """
   try:
      tomorrow = datetime.combine(datetime.now().date() + timedelta(days=1), time.min)

      bookings = await db.class_bookings.find({
         "teacher_id": str(teacher.id),
         "booking_date": tomorrow
      }).to_list(100)

      if not bookings:
         return []

      # Fetch all student IDs involved in the bookings
      student_ids = list({ObjectId(b["student_id"]) for b in bookings})

      # Fetch student data
      students_cursor = db.users.find({"_id": {"$in": student_ids}})
      student_map = {
         str(s["_id"]): {
            "first_name": s["first_name"],
            "last_name": s["last_name"],
            "email": s["email"],
            "school_name": s["school_name"],
            "standard": s["standard"],
            "previuos_standard_result": s["previuos_standard_result"]
         }
         async for s in students_cursor
      }

      # Group bookings by (start_time, end_time)
      grouped_slots = defaultdict(list)
      for b in bookings:
         key = (
            b["start_time"].strftime("%H:%M"),
            b["end_time"].strftime("%H:%M")
         )

         student_info = student_map.get(b["student_id"])
         if not student_info:
            continue

         grouped_slots[key].append({
            **student_info,
            "student_id": b["student_id"],
            "is_paid": b.get("is_paid", False)
         })

      # Step 4: Construct response list
      result = []
      for (start, end), students in grouped_slots.items():
         result.append({
            "booking_date": tomorrow,
            "subject": teacher.subject,
            "start_time": start,
            "end_time": end,
            "students": students
         })

      return result

      # detailed = []
      # for b in bookings:
      #    student_info = student_map.get(b["student_id"])
      #    if not student_info:
      #       continue 

      #    detailed.append({
      #       "teacher_id": b["teacher_id"],
      #       "student_id": b["student_id"],
      #       "booking_date": b["booking_date"],
      #       "subject": b["subject"],
      #       "start_time": b["start_time"],
      #       "end_time": b["end_time"],
      #       "students": [student_info]
      #    })

      # return detailed

   except Exception as e:
      raise HTTPException(
         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
         detail=f"An error occurred while fetching student reservations: {str(e)}"
      )