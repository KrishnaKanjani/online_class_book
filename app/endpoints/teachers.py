from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field
from typing import Dict, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.teacher import TeacherAvailability
from app.models.bookings import Booking
from app.middlewares.db import get_database
from app.middlewares.auth import get_current_teacher
from app.models.user import User
from app.core.response_validation import custom_jsonable_encoder
from bson import ObjectId
from datetime import date, timedelta, datetime, time

router = APIRouter()

class AvailabilityResponse(TeacherAvailability):
   id: str = Field(alias="_id")

   class Config:
      json_encoders = {ObjectId: str}

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

      # Check if already set for the same day
      exists = await db.teacher_availabilities.find_one({
         "teacher_id": data.teacher_id,
         "available_date": availability_date
      })
      if exists:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Availability already set for this date")

      # Prepare document with datetime normalization
      availability_doc = {
         **data.dict(),
         "available_date": availability_date,
         "start_time": data.start_time,
         "end_time": data.end_time,
         "subject": data.subject,
      }
      result = await db.teacher_availabilities.insert_one(availability_doc)
      return {**data.dict(), "_id": str(result.inserted_id)}
   
   except HTTPException as httpex:
      raise httpex
   
   except Exception as e:
      raise HTTPException(
         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
         detail=f"Error setting availability: {str(e)}"
      )


@router.get("/available/slots", response_model=Dict)
async def get_available_slots(
   db: AsyncIOMotorDatabase = Depends(get_database)
):
   tomorrow = datetime.combine(datetime.now().date() + timedelta(days=1), time.min)
   availabilities = await db.teacher_availabilities.find({"available_date": tomorrow}).to_list(100)
   if availabilities:
      return {
         "success": True,
         "message": "Available teachers fetched",
         "teachera_availabe": custom_jsonable_encoder(availabilities) 
      }
   else:
      return {
         "success": False,
         "message": "No available teachers for tomorrow",
         "teachera_availabe": custom_jsonable_encoder(availabilities) 
      }


@router.get("/student_reservation", response_model=list[Booking])
async def view_teacher_bookings(
   db: AsyncIOMotorDatabase = Depends(get_database),
   teacher: User = Depends(get_current_teacher)
):
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
               "phone": s["phone"]
         }
         async for s in students_cursor
      }

      detailed = []
      for b in bookings:
         student_info = student_map.get(b["student_id"])
         if not student_info:
               continue  # Skip if student not found (shouldn't happen)
         detailed.append({
            "booking_date": b["booking_date"],
            "subject": b["subject"],
            "start_time": b["start_time"],
            "end_time": b["end_time"],
            "students": [student_info]
         })

      return detailed

   except Exception as e:
      raise HTTPException(
         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
         detail=f"An error occurred while fetching student reservations: {str(e)}"
      )