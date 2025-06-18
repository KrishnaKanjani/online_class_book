from datetime import datetime, timedelta
from typing import Dict, Any

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from passlib.context import CryptContext

class JWTConfig(BaseModel):
   """Configuration for JWT settings."""
   secret_key: str
   algorithm: str
   access_token_expire_minutes: int
   refresh_token_expire_minutes: int


class JWTUtils:
   """Utility class for JWT operations."""

   def __init__(self, config: JWTConfig):
      self.config = config
      self.security = HTTPBearer()

   @property
   def access_token_expire_minutes(self):
      return self.config.access_token_expire_minutes

   @property
   def refresh_token_expire_minutes(self):
      return self.config.refresh_token_expire_minutes

   def create_access_token(self, data: Dict[str, Any]) -> str:
      """
      Create a new access token.

      Args:
         data: The payload data to encode in the token

      Returns:
         The encoded JWT token string
      """
      to_encode = data.copy()
      expire = datetime.utcnow() + timedelta(
         minutes=self.config.access_token_expire_minutes
      )
      to_encode.update({"exp": expire, "type": "access"})

      return jwt.encode(
         to_encode, self.config.secret_key, algorithm=self.config.algorithm
      )

   def create_refresh_token(self, data: Dict[str, Any]) -> str:
      """
      Create a new refresh token.

      Args:
         data: The payload data to encode in the token

      Returns:
         The encoded JWT refresh token string
      """
      to_encode = data.copy()
      expire = datetime.utcnow() + timedelta(
         minutes=self.config.refresh_token_expire_minutes
      )
      to_encode.update({"exp": expire, "type": "refresh"})

      return jwt.encode(
         to_encode, self.config.secret_key, algorithm=self.config.algorithm
      )

   def decode_token(self, token: str) -> Dict[str, Any]:
      """
      Decode and validate a JWT token.

      Args:
         token: The token to decode

      Returns:
         The decoded payload

      Raises:
         HTTPException: If token is invalid or expired
      """
      try:
         payload = jwt.decode(
            token, self.config.secret_key, algorithms=[self.config.algorithm]
         )
         return payload
      except jwt.ExpiredSignatureError:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
               "msg": "Token has expired",
               "code": "expired_token",
            },
         )
      except jwt.InvalidTokenError:
         raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
         )

   def verify_refresh_token(self, token: str):
      """
      Verify refresh token.

      Args:
         token: The token to decode

      Returns:
         The decoded payload

      Raises:
         HTTPException: If token is invalid or expired
      """
      try:
         payload = self.decode_token(token)
         return payload
      except jwt.PyJWTError:
         raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
      
class AuthorizationUtils:
   """Authorization class for Password related operations."""

   def __init__(self):
      self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

   def verify_password(self, plain_password, hashed_password):
      return self.pwd_context.verify(plain_password, hashed_password)

   def get_password_hash(self, password):
      return self.pwd_context.hash(password)


