from pydantic_settings import BaseSettings
from functools import lru_cache
from app.core.security import JWTConfig, JWTUtils, AuthorizationUtils

class Settings(BaseSettings):
   MONGO_URI: str
   DB_NAME: str
   SECRET_KEY: str
   ALGORITHM: str = "HS256"
   ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
   REFRESH_ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

   class Config:
      env_file = ".env"

@lru_cache()
def get_settings():
   return Settings()

settings = get_settings()
jwt_utils = JWTUtils(config=JWTConfig(
   secret_key=settings.SECRET_KEY,
   algorithm=settings.ALGORITHM,
   access_token_expire_minutes=settings.REFRESH_ACCESS_TOKEN_EXPIRE_MINUTES,
   refresh_token_expire_minutes=settings.REFRESH_ACCESS_TOKEN_EXPIRE_MINUTES
))
authorization_utils = AuthorizationUtils()
