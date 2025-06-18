from pydantic import BaseModel, EmailStr
from typing import Optional

class Token(BaseModel):
   access_token: str
   token_type: str = "bearer"

class TokenData(BaseModel):
   email: Optional[str] = None
   user_id: Optional[str] = None
   role: Optional[str] = None

class LoginRequest(BaseModel):
   email: EmailStr
   password: str

class RefreshToken(BaseModel):
   refresh_token: str