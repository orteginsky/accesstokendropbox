# app/core/config.py
"""Application configuration."""
import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""

    # Application settings
    APP_NAME: str = Field(default="AccessTokenDropbox", description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # API settings
    API_SECRET_KEY: str = Field(..., description="Secret key for API authentication")
    AUTH_MODE: str = Field(default="simple", description="Authentication mode: simple or hmac")
    ALLOWED_SIGNATURES: List[str] = Field(
        default_factory=list,
        description="List of allowed signatures for HMAC mode"
    )

    # Google Cloud settings
    GCP_PROJECT_ID: str = Field(..., description="Google Cloud Project ID")
    SECRET_NAME: str = Field(
        default="dropbox-access-token",
        description="Secret name in Secret Manager"
    )
    GOOGLE_APPLICATION_CREDENTIALS: str = Field(
        default="",
        description="Path to GCP service account credentials JSON file"
    )

    # Dropbox settings
    DROPBOX_APP_KEY: str = Field(..., description="Dropbox App Key")
    DROPBOX_APP_SECRET: str = Field(..., description="Dropbox App Secret")
    DROPBOX_REDIRECT_URI: str = Field(
        default="http://localhost:8080/oauth2/callback",
        description="Dropbox OAuth2 redirect URI"
    )

    # Server settings
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8080, description="Server port")

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

        # Allow parsing comma-separated values into lists
        @staticmethod
        def parse_env_var(field_name: str, raw_val: str):
            if field_name == "ALLOWED_SIGNATURES":
                return [x.strip() for x in raw_val.split(",") if x.strip()]
            return raw_val


# Create global settings instance
settings = Settings()
