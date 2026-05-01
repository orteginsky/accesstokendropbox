# app/repositories/dropbox_repository.py
"""Repository for Dropbox API operations."""
import logging
from typing import Optional
from datetime import datetime, timedelta
import requests

from ..models.token import DropboxToken
from ..core.config import settings

logger = logging.getLogger(__name__)


class DropboxRepository:
    """Repository for interacting with Dropbox API."""

    def __init__(self):
        """Initialize Dropbox repository."""
        self.token_url = "https://api.dropbox.com/oauth2/token"
        self.check_url = "https://api.dropboxapi.com/2/check/user"
        self.app_key = settings.DROPBOX_APP_KEY
        self.app_secret = settings.DROPBOX_APP_SECRET

    def validate_token(self, access_token: str) -> bool:
        """
        Validate if access token is still active.

        Args:
            access_token: The access token to validate

        Returns:
            True if token is valid, False otherwise
        """
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            response = requests.post(
                self.check_url,
                headers=headers,
                json={"query": "test"},
                timeout=10
            )

            if response.status_code == 200:
                logger.info("Token is valid")
                return True
            else:
                logger.warning(f"Token validation failed: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Error validating token: {e}")
            return False

    def refresh_access_token(self, refresh_token: str) -> Optional[DropboxToken]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: The refresh token

        Returns:
            New DropboxToken if successful, None otherwise
        """
        try:
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.app_key,
                "client_secret": self.app_secret
            }

            response = requests.post(
                self.token_url,
                data=data,
                timeout=10
            )

            if response.status_code == 200:
                token_data = response.json()

                # Calculate expiration time
                expires_in = token_data.get("expires_in", 14400)  # Default 4 hours
                expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

                new_token = DropboxToken(
                    access_token=token_data["access_token"],
                    refresh_token=refresh_token,
                    expires_at=expires_at,
                    updated_at=datetime.utcnow()
                )

                logger.info("Token refreshed successfully")
                return new_token
            else:
                logger.error(f"Error refreshing token: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error while refreshing token: {e}")
            return None
        except KeyError as e:
            logger.error(f"Missing key in response: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error refreshing token: {e}")
            return None

    def get_initial_token(self, authorization_code: str, redirect_uri: Optional[str] = None) -> Optional[DropboxToken]:
        """
        Get initial access token using authorization code.
        This is used for first-time setup.
        """
        try:
            uri = redirect_uri or settings.DROPBOX_REDIRECT_URI
            logger.info(f"Using redirect_uri for token exchange: {uri}")
            
            data = {
                "grant_type": "authorization_code",
                "code": authorization_code,
                "redirect_uri": uri,
            }

            # Autenticación recomendada por Dropbox: Basic Auth con app_key/app_secret
            response = requests.post(
                self.token_url,
                data=data,
                auth=(self.app_key, self.app_secret),
                timeout=10,
            )

            if response.status_code == 200:
                token_data = response.json()

                expires_in = token_data.get("expires_in", 14400)
                expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

                new_token = DropboxToken(
                    access_token=token_data["access_token"],
                    refresh_token=token_data["refresh_token"],
                    expires_at=expires_at,
                    created_at=datetime.utcnow(),
                )

                logger.info("Initial token obtained successfully")
                return new_token
            else:
                logger.error(
                    f"Error getting initial token: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Error getting initial token: {e}")
            return None

