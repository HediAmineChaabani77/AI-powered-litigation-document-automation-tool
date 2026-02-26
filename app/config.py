"""Application configuration loaded from environment variables."""

import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Litigation AI Tool"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    upload_dir: str = "/tmp/uploads"
    max_file_size_mb: int = 50
    debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
