from typing import Dict
from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import date, timedelta, time, datetime
from app.middlewares.db import get_database
from app.core.response_validation import custom_jsonable_encoder
from bson import ObjectId
from collections import defaultdict
import logging

router = APIRouter()


@router.get("/available", response_model=Dict)
async def get_available_slots(
    db: AsyncIOMotorDatabase = Depends(get_database)
):
   """
      Returns the list of teachers available tomorrow, 
      with their profile info and grouped availability slots.
   """
   try:
      tomorrow = datetime.combine(datetime.now().date() + timedelta(days=1), time.min)
      logging.info(f"Tomorrow's date: {tomorrow}")
      availabilities = await db.teacher_availabilities.find({"available_date": tomorrow}).to_list(100)
      logging.info(f"Teacher availabilities: {availabilities}")

      if not availabilities:
         return {
            "success": False,
            "message": "No teacher availabilities found for tomorrow.",
            "teachers_available": []
         }

      teacher_map = defaultdict(lambda: {
         "teacher_id": None,
         "first_name": "",
         "last_name": "",
         "email": "",
         "phone": "",
         "subject": "",
         "years_of_exp": 0,
         "slots": []
      })

      for avail in availabilities:
         teacher = await db.users.find_one({"_id": ObjectId(avail["teacher_id"]), "role": "teacher"})
         if not teacher:
            continue

         tid = str(teacher["_id"])
         teacher_entry = teacher_map[tid]
         teacher_entry.update({
            "teacher_id": tid,
            "first_name": teacher["first_name"],
            "last_name": teacher["last_name"],
            "email": teacher["email"],
            "phone": teacher["phone"],
            "subject": teacher.get("subject"),
            "years_of_exp": teacher.get("years_of_exp"),
         })
         teacher_entry["slots"].append({
            "available_date": avail["available_date"],
            "start_time": avail["start_time"],
            "end_time": avail["end_time"],
            "max_no_of_students_each_slot": avail.get("max_no_of_students_each_slot", 1)
         })

      return {
         "success": True,
         "message": "Grouped teacher availability fetched successfully",
         "teachers_available": custom_jsonable_encoder(list(teacher_map.values()))
      }

   except Exception as e:
      raise HTTPException(
         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
         detail=f"Error occurred in getting available slots: {str(e)}"
      )
