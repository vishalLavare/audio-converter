import os
import tempfile
from pathlib import Path
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    APP_NAME: str = "Instagram Reel to MP3 Converter"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Limits & Timeouts
    MAX_DOWNLOAD_SIZE_MB: int = 100
    DOWNLOAD_TIMEOUT_SECONDS: int = 180
    CONVERSION_TIMEOUT_SECONDS: int = 180
    CLEANUP_AFTER_MINUTES: int = 30
    DEFAULT_BITRATE: str = "192k"
    
    # Security & CORS
    CORS_ORIGINS: Union[List[str], str] = ["*"]
    RATE_LIMIT: str = "30/minute"
    
    # Storage
    TEMP_DIR: str = os.getenv(
        "TEMP_DIR",
        str(Path(tempfile.gettempdir()) / "reel_converter") if os.name == "nt" else "/tmp/reel_converter"
    )
    
    # Custom binaries (optional overrides)
    FFMPEG_PATH: str = ""
    FFPROBE_PATH: str = ""

    # Optional Cookie Authentication (for YouTube bot challenge bypass on servers)
    COOKIES_FILE: str = ""
    YOUTUBE_COOKIES_TEXT: str = ""

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if v == "*":
            return ["*"]
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


settings = Settings()

# Ensure base temp dir exists
Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)
