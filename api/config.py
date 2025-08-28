from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    aws_region: str = "us-east-1"
    s3_bucket: str
    redis_url: str = "redis://localhost:6379/0"
    database_url: str
    insightface_provider: str = "CPUExecutionProvider"
    thumbnail_max_px: int = 512

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
