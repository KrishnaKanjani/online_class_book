"""
Auto-assignment of class slots for inactive students.

ASSUMPTIONS:
- Teachers have set their availability for the next day.
- Each teacher slot is 1 hour long.
- Students who haven't booked a slot by themselves will be auto-assigned.

SUGGESTION:
- Though this is implemented as a FastAPI background task (runs every 5 hours),
we can use a CRON JOB that run at a particular time period, in production (e.g., run every night at 11:00 PM).
"""

from datetime import timedelta, datetime, time
from motor.motor_asyncio import AsyncIOMotorClient
from app.models.bookings import Booking
from app.core.config import settings
import asyncio
# from fastapi_utils.tasks import repeat_every  # requires `fastapi-utils`

async def auto_assign_unbooked_students():
   mongodb_client = AsyncIOMotorClient(settings.MONGO_URI)
   db = mongodb_client[settings.DB_NAME]
   try:
      # The class slots will be assigned for tomorrow
      tomorrow = datetime.combine(datetime.now().date() + timedelta(days=1), time.min)

      # Step 1: Fetch all student accounts
      all_students = await db.users.find({"role": "student", "is_active": True}).to_list(length=1000)

      # Step 2: Fetch students who already booked a slot
      booked = await db.class_bookings.find({"booking_date": tomorrow}).to_list(length=1000)
      booked_student_ids = {booking["student_id"] for booking in booked}

      # Step 3: Filter students who haven’t booked yet
      unassigned_students = [student for student in all_students if str(student["_id"]) not in booked_student_ids]

      if not unassigned_students:
         print("✅ All students have already booked.")
         return

      # Step 4: Get teacher availability for tomorrow
      teacher_availabilities = await db.teacher_availabilities.find({"available_date": tomorrow}).to_list(length=100)

      # Step 5: Build a mapping of teacher -> available 1-hour slots
      teacher_slots = {}

      for availability in teacher_availabilities:
         teacher_id = str(availability["teacher_id"])         
         start_time = availability["start_time"]
         max_allowed = availability.get("max_no_of_students_each_slot", 1)
         end_time = availability["end_time"]
         
         slots = {}
         while start_time < end_time:
            slot_end = start_time + timedelta(hours=1)
            slots[start_time] = {
               "end_time": slot_end,
               "count": 0,
               "max": max_allowed
            }
            start_time = slot_end

         teacher_slots[teacher_id] = {
            "subject": availability["subject"],
            "slots": slots,
         }

      # Step 6: Mark already booked time slots for each teacher
      for booking in booked:
         teacher_id = booking["teacher_id"]
         start_time = booking["start_time"]
         if teacher_id in teacher_slots and start_time in teacher_slots[teacher_id]["slots"]:
               teacher_slots[teacher_id]["slots"][start_time]["count"] += 1

      # Step 7: Auto-assign each unassigned student to an available slot
      assigned_count = 0

      for student in unassigned_students:
         assigned = False
         for teacher_id, info in teacher_slots.items():
            for start_time, slot_info in info["slots"].items():
               if slot_info["count"] < slot_info["max"]:
                  # Create booking record
                  new_booking = Booking(
                     student_id=str(student["_id"]),
                     teacher_id=teacher_id,
                     subject=info["subject"],
                     booking_date=tomorrow,
                     start_time=start_time,
                     end_time=slot_info["end_time"]
                  )
                  await db.class_bookings.insert_one(new_booking.dict())

                  slot_info["count"] += 1
                  assigned_count += 1
                  assigned = True
                  break
            if assigned:
               break

      print(f"Auto-assigned {assigned_count} students to free class slots.")

   except Exception as e:
      print(f"Error during auto-assignment: {str(e)}")

   finally:
      mongodb_client.close()

if __name__ == "__main__":
   asyncio.run(auto_assign_unbooked_students())
