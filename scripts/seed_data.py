import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.config import authorization_utils
from datetime import datetime, timedelta, time
import random

client = AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.DB_NAME]

async def seed():
   # CLEAR PREVIOUS DATA FOR FRESH TESTING (ONLY FOR DEVELOPMENT)
   await db.users.delete_many({})
   await db.teacher_availabilities.delete_many({})
   await db.class_bookings.delete_many({})

   print("✅ Cleared previous data.")

   # Hash the default password
   hashed_teacher_pwd = authorization_utils.get_password_hash("education@123")

   # 1. Add Teachers
   teachers = [
      {
         "first_name": "Alice",
         "last_name": "Matheson",
         "email": "alice@school.com",
         "phone": "+911111111111",
         "age": 35,
         "role": "teacher",
         "subject": "Mathematics",
         "years_of_exp": 1,
         "is_active": True,
         "hashed_password": hashed_teacher_pwd,
         "created_at": datetime.now(),
         "updated_at": datetime.now()
      },
      {
         "first_name": "Bob",
         "last_name": "Physico",
         "email": "bob@school.com",
         "phone": "+922222222222",
         "age": 40,
         "role": "teacher",
         "subject": "English",
         "years_of_exp": 4,
         "is_active": True,
         "hashed_password": hashed_teacher_pwd,
         "created_at": datetime.now(),
         "updated_at": datetime.now()
      },
      {
         "first_name": "Charlie",
         "last_name": "Chemlord",
         "email": "charlie@school.com",
         "phone": "+933333333333",
         "age": 42,
         "role": "teacher",
         "subject": "Chemistry",
         "years_of_exp": 2.5,
         "is_active": True,
         "hashed_password": hashed_teacher_pwd,
         "created_at": datetime.now(),
         "updated_at": datetime.now()
      }
   ]

   teacher_result = await db.users.insert_many(teachers)
   teacher_ids = teacher_result.inserted_ids

   print(f"✅ Inserted {len(teacher_ids)} teachers.")

   # 2. Add Students
   hashed_student_pwd = authorization_utils.get_password_hash("school@123")

   students = []
   for i in range(15):
      students.append({
         "first_name": f"Student{i+1}",
         "last_name": "Test",
         "email": f"student{i+1}@school.com",
         "phone": f"+9199000000{i+1:02}",
         "age": 18 + i % 5,
         "role": "student",
         "school_name": f"""School {random.choice(["ABC", "XYZ", "PQR", "KLM", "DEF", "OPQ", "WXY"])}""",
         "standard": random.choice(["4rd", "5th", "6th", "7th", "8th"]),
         "previuos_standard_result": random.randint(70, 97),
         "is_active": True,
         "hashed_password": hashed_student_pwd,
         "created_at": datetime.now(),
         "updated_at": datetime.now()
      })

   student_result = await db.users.insert_many(students)
   print(f"✅ Inserted {len(student_result.inserted_ids)} students.")

   # 3. Add Availability for Teachers (for tomorrow)
   tomorrow = datetime.now().date() + timedelta(days=1)
   availabilities = []

   for i, teacher_id in enumerate(teacher_ids):
      start_time = time(10 + i, 0)  # 10:00 AM, 11:00 AM, 12:00 PM
      end_time = time(12 + i, 0)        # Till 6:00 PM
      availabilities.append({
         "teacher_id": str(teacher_id),
         "subject": teachers[i]["subject"],
         "available_date": tomorrow,
         "start_time": start_time,
         "end_time": end_time,
         "max_no_of_students_each_slot": random.randint(2, 5)
      })

   availabilities = [
      {
         **doc,
         "available_date": datetime.combine(doc["available_date"], time.min),
         "start_time": datetime.combine(doc["available_date"], doc["start_time"]),
         "end_time": datetime.combine(doc["available_date"], doc["end_time"]),
      }
      for doc in availabilities
   ]

   await db.teacher_availabilities.insert_many(availabilities)
   print("✅ Inserted availability slots for all teachers.")

   # 4. (Optional) Add 3 bookings manually
   bookings = []
   for i in range(3):
      bookings.append({
         "student_id": str(student_result.inserted_ids[i]),
         "teacher_id": str(teacher_ids[i]),
         "subject": teachers[i]["subject"],
         "booking_date": tomorrow,
         "start_time": time(10, 0),
         "end_time": time(11, 0),
         "booked_at": datetime.now(),
         "fees_paid": random.choice([True, False])
      })

   bookings = [
      {
         **doc,
         "payment_timestamp": datetime.now() if doc["fees_paid"] is True else None,
         "booking_date": datetime.combine(doc["booking_date"], time.min),
         "start_time": datetime.combine(doc["booking_date"], doc["start_time"]),
         "end_time": datetime.combine(doc["booking_date"], doc["end_time"]),
      }
      for doc in bookings
   ]

   await db.class_bookings.insert_many(bookings)
   print("✅ Added 3 initial bookings (1 per teacher).")

   print("🎉 Seeding complete!")

if __name__ == "__main__":
   asyncio.run(seed())
