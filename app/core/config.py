"""
Application configuration management using Pydantic Settings.

This module provides centralized configuration management with:
- Environment variable support
- Type validation
- Default values for development
- Easy extension for future settings (API keys, OAuth, etc.)
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Attributes:
        PROJECT_NAME: Display name for the application.
        ENVIRONMENT: Current environment (dev/staging/prod).
        DATABASE_URL: SQLAlchemy database connection string.
        DEBUG: Enable debug mode (auto-set based on environment).
        
    Future Phase Placeholders:
        - GOOGLE_CLIENT_ID: For OAuth integration
        - GOOGLE_CLIENT_SECRET: For OAuth integration
        - OPENAI_API_KEY: For LLM integration
        - VECTOR_DB_URL: For RAG retrieval
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    # Core Settings
    PROJECT_NAME: str = "Education RAG"
    ENVIRONMENT: Literal["dev", "staging", "prod"] = "dev"
    DEBUG: bool = True
    
    # Database Settings
    # SQLite for development, easily swappable to PostgreSQL
    DATABASE_URL: str = "sqlite:///./education_rag.db"
    
    # OpenAI Settings (Phase 3-4)
    OPENAI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536
    
    # Vector Store Settings
    FAISS_INDEX_PATH: str = "data/faiss/index.faiss"
    FAISS_METADATA_PATH: str = "data/faiss/metadata.json"
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    
    # Future: OAuth Settings (stub only)
    # GOOGLE_CLIENT_ID: str = ""
    # GOOGLE_CLIENT_SECRET: str = ""
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "dev"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "prod"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are only loaded once,
    improving performance and ensuring consistency.
    
    Returns:
        Settings: The application settings instance.
    """
    return Settings()
