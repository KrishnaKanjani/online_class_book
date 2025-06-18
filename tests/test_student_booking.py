import pytest
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_student_can_see_slots_and_book(client, db):
   # Login student
   login_data = {"email": "student@example.com", "password": "strongpassword"}
   login_resp = await client.post("/auth/login", json=login_data)
   token = login_resp.json()["access_token"]

   # Get slots
   r = await client.get("/teacher/available/slots", headers={"Authorization": f"Bearer {token}"})
   assert r.status_code == 200
   slots = r.json()
   assert len(slots) > 0

   teacher_id = slots[0]["teacher_id"]
   slot_start = slots[0]["start_time"]

   # Book slot
   book_url = f"/student/booking/?teacher_id={teacher_id}&slot_start={slot_start}"
   r2 = await client.post(book_url, headers={"Authorization": f"Bearer {token}"})
   assert r2.status_code == 200
   assert r2.json()["start_time"] == slot_start
