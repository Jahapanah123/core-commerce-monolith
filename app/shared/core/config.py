from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

    #app settings
    APP_ENV: str
    DEBUG: bool = False
    API_V1_STR: str
    
    #database settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    
    #DB pool
    DB_POOL_SIZE: int
    DB_MAX_OVERFLOW: int
    DB_POOL_TIMEOUT: int
    DB_POOL_RECYCLE: int
    
    # Redis Settings
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str | None = None

    # RabbitMQ Settings
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int

    # Security Settings
    JWT_SECRET_KEY: str
    JWT_REFRESH_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    
    # OTP
    OTP_LENGTH: int = 6
    OTP_TTL_SECONDS: int = 300
    OTP_MAX_ATTEMPTS: int = 3

    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str

    # Development
    USE_MOCK_SMS: bool = True
    
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
        
    # validation layer
    
    @field_validator("DB_POOL_SIZE")
    @classmethod
    def validate_db_pool_size(cls, value):
        if not(1<=value<=100):
            raise ValueError("DB_POOL_SIZE must be between 1 and 100")
        return value
    
    @field_validator("DB_MAX_OVERFLOW")
    @classmethod
    def validate_db_max_overflow(cls, value):
        if not(0<=value<=50):
            raise ValueError("DB_MAX_OVERFLOW must be between 0 and 100")
        return value
    
    @field_validator("DEBUG")
    @classmethod
    def validate_debug(cls, v, info):
        # production safety rule
        env = info.data.get("APP_ENV")
        if env == "production" and v is True:
            raise ValueError("DEBUG cannot be True in production")
        return v
    
settings = Settings()