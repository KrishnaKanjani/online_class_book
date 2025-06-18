import pytest

student_payload = {
   "first_name": "Test",
   "last_name": "Student",
   "email": "student@example.com",
   "phone": "+919876543210",
   "age": 20,
   "role": "student",
   "password": "strongpassword"
}

teacher_payload = {
   "first_name": "Test",
   "last_name": "Teacher",
   "email": "teacher@example.com",
   "phone": "+919876543211",
   "age": 30,
   "role": "teacher",
   "password": "strongpassword",
   "subject": "Math"
}

@pytest.mark.asyncio
async def test_student_register_and_login(client):
   # Register
   r = await client.post("/auth/register", json=student_payload)
   assert r.status_code == 200
   assert "access_token" in r.json()

   # Login
   login_data = {"email": student_payload["email"], "password": student_payload["password"]}
   r2 = await client.post("/auth/login", json=login_data)
   assert r2.status_code == 200
   assert "access_token" in r2.json()

@pytest.mark.asyncio
async def test_teacher_register(client):
   r = await client.post("/auth/register", json=teacher_payload)
   assert r.status_code == 200
   assert "access_token" in r.json()
