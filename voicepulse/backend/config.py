import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV = Path(__file__).resolve().parent.parent / ".env"

class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV))
    GROQ_API_KEY: str = ""
    HF_TOKEN: str = ""
    MONGO_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "sentiment_pulse"
    REDIS_URL: str = "redis://localhost:6379/0"
    HF_HOME: str = ""

cfg = Config()
if cfg.HF_HOME:
    os.environ["HF_HOME"] = cfg.HF_HOME
