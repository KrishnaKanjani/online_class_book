from pydantic import BaseModel, EmailStr
from typing import Optional

class Token(BaseModel):
   access_token: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   token_type: str = "bearer"

class TokenData(BaseModel):
   email: Optional[str] = "krishna.kanjani@example.com"
   user_id: Optional[str] = "665e3dcf6dd8e693cefa77c2"
   role: Optional[str] = "student"

class LoginRequest(BaseModel):
   email: EmailStr = "krishna.kanjani@example.com"
   password: str = "StrongPass@123"

class RefreshToken(BaseModel):
   refresh_token: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
