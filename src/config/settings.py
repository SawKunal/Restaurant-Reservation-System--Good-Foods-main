"""Configuration settings for the Restaurant AI Agent."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    
    # Groq API Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # Application Configuration
    APP_NAME: str = os.getenv("APP_NAME", "Restaurant AI Agent")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Model Configuration
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "llama-3.1-8b-instant")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2048"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.2"))
    
    # Data Configuration
    RESTAURANT_DATA_FILE: str = os.getenv("RESTAURANT_DATA_FILE", "src/data/restaurants.json")
    RESERVATION_DATA_FILE: str = os.getenv("RESERVATION_DATA_FILE", "src/data/reservations.json")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that all required settings are present."""
        if not cls.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY environment variable is required")
        return True

# Create a global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings."""
    return settings
