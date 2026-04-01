from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ADMIN_SECRET_TOKEN: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 # 
    ALLOWED_ORIGINS: str = "*"


    model_config = SettingsConfigDict(env_file=".env",extra="ignore")
settings = Settings()