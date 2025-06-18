import pytest
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_set_teacher_availability(client):
   # Login teacher
   login_data = {"email": "teacher@example.com", "password": "strongpassword"}
   login_resp = await client.post("/auth/login", json=login_data)
   token = login_resp.json()["access_token"]

   tomorrow = datetime.now() + timedelta(days=1)

   payload = {
      "available_date": tomorrow.strftime("%Y-%m-%d"),
      "start_time": "10:00:00",
      "end_time": "13:00:00"
   }

   r = await client.post(
      "/availability/",
      json=payload,
      headers={"Authorization": f"Bearer {token}"}
   )

   assert r.status_code in [200, 201]
