import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment and .env file."""
    
    # API configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "OpenSource Navigator AI API"
    VERSION: str = "1.0.0"
    
    # GitHub Integration
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_API_BASE_URL: str = "https://api.github.com"
    GITHUB_SEARCH_CACHE_TTL_SECONDS: int = 120
    
    # Ollama Integration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "deepseek-r1:8b"  # Configurable: e.g. qwen3:4b, deepseek-r1:8b, etc.
    OLLAMA_TIMEOUT_SECONDS: float = 180.0
    
    # CORS
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
