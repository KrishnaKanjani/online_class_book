# Online Class Book API

A FastAPI-based REST API for managing online class bookings between teachers and students with JWT authentication.

## Features

- JWT Authentication: Secure authentication with 15-minute token expiration (logic for refresh token also written)
- Role-based Access: Students and Teachers with different permissions
- Class Booking System: Teachers set availability, students book time slots
- MongoDB Integration: Database cofiguration
- Comprehensive Testing: Full test suite with pytest
- Middleware & Dependencies: Clean architecture with proper separation of concerns
- Background task: Auto assigns classes to the active students on the available slots

## Installation & Setup

### Prerequisites
- Python 3.8+
- MongoDB 
- Git

### Installation Steps
1. Create virtual environment
   python -m venv venv
   On Windows: venv\Scripts\activate

2. Install dependencies
   pip install -r requirements.txt

3. Environment Configuration
   Create a `.env` file in the root directory
   - Keys for environment variables is mentioned in `.env.example`

4. Run the application
   - Execute the below script to feed the initial (test) data in the db (mongodb)
      ```bash
      python -m scripts.seed_data
      ```
   - Command to execute the application
      ```bash
      uvicorn app.main:app --reload
      or
      uvicorn app.main:app --reload --port {specific port}
      ```

5. Background Task of auto assigning the students to free slots is implemented in tasks/auto_assign.py
   - Command to test execute it:
      ```bash
         python -m tasks.auto_assign
      ```

6. Access the API
   - API Documentation: http://localhost:8000/docs OR http://localhost:{port}/docs
   - Alternative Docs: http://localhost:8000/redoc OR http://localhost:{port}/redoc

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `POST /auth/reset-password` - Reset the password with password strength validation
- `POST /auth/refresh` - Refresh access token

### Teachers
- `GET /teacher/me` - Get current teacher profile
- `PATCH /teacher/me` - Update current teacher profile
- `POST /teacher/availability` - Set availability for next day 
- `GET /teacher/available_slots` - Get teacher's available slots
- `GET /teacher/bookings` - Get all bookings for teacher
- `GET /slots/available` - List all teachers with their available slots and details

### Students
- `GET /student/me` - Get current student profile
- `PATCH /student/me` - Update current student profile
- `POST /students/book` - Book a time slot with teacher
- `GET /students/bookings` - Get student's bookings
- `DELETE /students/bookings/{booking_id}` - Cancel booking

## Default Data

The system comes with pre-populated data once you execute the script "scripts/seed_data.py" as mentioned:

### Teachers (3 accounts)
1. Math Teacher - alice@school.com (Subject: Mathematics)
2. Chemistry Teacher - charlie@school.com (Subject: Chemistry)
3. English Teacher - bob@school.com (Subject: English)

### Students (15 accounts)
- student1@school.com to student15@school.com

> Default Password for all **teacher** accounts: `education@123`

> Default Password for all **student** accounts: `school@123`

## Testing

Run the test suite:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py -v

# Generate HTML Coverage Report
pytest --cov=app --cov-report=html
--- then open start htmlcov/index.html(WINDOWS), open htmlcov/index.html(macOS)
```

## MongoDB Collections

- `users`: User accounts (students and teachers)
- `class_bookings`: Class booking records
- `teacher_availabilities`: Teacher availability slots
