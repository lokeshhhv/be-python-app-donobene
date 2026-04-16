from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # 30 minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7 # 7 days
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASS: str

    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }

settings = Settings()
