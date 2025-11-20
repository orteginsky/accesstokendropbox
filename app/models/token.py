"""Token domain models."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    """Request model for token retrieval."""
    signature: str = Field(..., description="Signature or payload for authentication")
    service: str = Field(default="dropbox", description="Service identifier")

    class Config:
        json_schema_extra = {
            "example": {
                "signature": "your-secure-signature-here",
                "service": "dropbox"
            }
        }


class TokenResponse(BaseModel):
    """Response model for token retrieval."""
    access_token: str = Field(..., description="The Dropbox access token")
    expires_at: Optional[datetime] = Field(None, description="Token expiration timestamp")
    token_type: str = Field(default="bearer", description="Token type")
    refreshed: bool = Field(default=False, description="Whether token was refreshed")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "sl.xxxxxxxxxxxxx",
                "expires_at": "2025-11-12T12:00:00",
                "token_type": "bearer",
                "refreshed": False
            }
        }


class DropboxToken(BaseModel):
    """Internal model for Dropbox token storage."""
    access_token: str
    refresh_token: str
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def is_expired(self) -> bool:
        """Check if token is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at

    def is_about_to_expire(self, minutes: int = 10) -> bool:
        """Check if token is about to expire within specified minutes."""
        if not self.expires_at:
            return False
        from datetime import timedelta
        return datetime.utcnow() >= (self.expires_at - timedelta(minutes=minutes))
