"""Token management service - Business logic layer."""
import logging
from typing import Optional
from datetime import datetime

from ..models.token import DropboxToken, TokenResponse
from ..repositories.secret_manager_repository import SecretManagerRepository
from ..repositories.dropbox_repository import DropboxRepository

logger = logging.getLogger(__name__)


class TokenService:
    """Service for managing Dropbox tokens."""

    def __init__(
        self,
        secret_manager_repo: Optional[SecretManagerRepository] = None,
        dropbox_repo: Optional[DropboxRepository] = None
    ):
        """
        Initialize token service.

        Args:
            secret_manager_repo: Repository for Secret Manager (injected for testing)
            dropbox_repo: Repository for Dropbox API (injected for testing)
        """
        self.secret_manager_repo = secret_manager_repo or SecretManagerRepository()
        self.dropbox_repo = dropbox_repo or DropboxRepository()

    def get_valid_token(self) -> TokenResponse:
        """
        Get a valid access token.

        This method:
        1. Retrieves token from Secret Manager
        2. Validates if token is still active
        3. If not active, refreshes the token
        4. Updates Secret Manager with new token
        5. Returns the valid token

        Returns:
            TokenResponse with valid access token

        Raises:
            Exception if unable to get valid token
        """
        logger.info("Starting token retrieval process")

        # Step 1: Get token from Secret Manager
        stored_token = self.secret_manager_repo.get_token()

        if not stored_token:
            error_msg = "No token found in Secret Manager. Please initialize token first."
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Step 2: Check if token is expired or about to expire
        if stored_token.is_about_to_expire(minutes=10):
            logger.info("Token is expired or about to expire, refreshing...")
            return self._refresh_and_update_token(stored_token)

        # Step 3: Validate token with Dropbox API
        is_valid = self.dropbox_repo.validate_token(stored_token.access_token)

        if is_valid:
            logger.info("Token is valid, returning existing token")
            return TokenResponse(
                access_token=stored_token.access_token,
                expires_at=stored_token.expires_at,
                refreshed=False
            )
        else:
            logger.info("Token validation failed, refreshing...")
            return self._refresh_and_update_token(stored_token)

    def _refresh_and_update_token(self, old_token: DropboxToken) -> TokenResponse:
        """
        Refresh token and update Secret Manager.

        Args:
            old_token: The expired or invalid token

        Returns:
            TokenResponse with new token

        Raises:
            Exception if refresh fails
        """
        # Refresh the token
        new_token = self.dropbox_repo.refresh_access_token(old_token.refresh_token)

        if not new_token:
            error_msg = "Failed to refresh token from Dropbox"
            logger.error(error_msg)
            raise Exception(error_msg)

        # Preserve the original refresh_token if not returned
        if not new_token.refresh_token:
            new_token.refresh_token = old_token.refresh_token

        # Update Secret Manager
        success = self.secret_manager_repo.save_token(new_token)

        if not success:
            logger.error("Failed to update token in Secret Manager")
            raise Exception("Failed to update token in Secret Manager")

        logger.info("Token refreshed and updated successfully")

        return TokenResponse(
            access_token=new_token.access_token,
            expires_at=new_token.expires_at,
            refreshed=True
        )

    def initialize_token(self, authorization_code: str) -> TokenResponse:
        """
        Initialize token for first-time setup using authorization code.

        Args:
            authorization_code: OAuth authorization code

        Returns:
            TokenResponse with new token

        Raises:
            Exception if initialization fails
        """
        logger.info("Initializing new token with authorization code")

        # Get initial token from Dropbox
        new_token = self.dropbox_repo.get_initial_token(authorization_code)

        if not new_token:
            error_msg = "Failed to get initial token from Dropbox"
            logger.error(error_msg)
            raise Exception(error_msg)

        # Save to Secret Manager
        success = self.secret_manager_repo.save_token(new_token)

        if not success:
            error_msg = "Failed to save initial token to Secret Manager"
            logger.error(error_msg)
            raise Exception(error_msg)

        logger.info("Token initialized successfully")

        return TokenResponse(
            access_token=new_token.access_token,
            expires_at=new_token.expires_at,
            refreshed=False
        )

    def force_refresh_token(self) -> TokenResponse:
        """
        Force refresh the token regardless of its current state.

        Returns:
            TokenResponse with refreshed token

        Raises:
            Exception if refresh fails
        """
        logger.info("Force refreshing token")

        stored_token = self.secret_manager_repo.get_token()

        if not stored_token:
            error_msg = "No token found in Secret Manager"
            logger.error(error_msg)
            raise ValueError(error_msg)

        return self._refresh_and_update_token(stored_token)

    def get_token_info(self) -> dict:
        """
        Get information about the current token.

        Returns:
            Dictionary with token information
        """
        stored_token = self.secret_manager_repo.get_token()

        if not stored_token:
            return {
                "exists": False,
                "message": "No token found"
            }

        is_expired = stored_token.is_expired()
        is_about_to_expire = stored_token.is_about_to_expire(minutes=10)

        return {
            "exists": True,
            "created_at": stored_token.created_at.isoformat() if stored_token.created_at else None,
            "updated_at": stored_token.updated_at.isoformat() if stored_token.updated_at else None,
            "expires_at": stored_token.expires_at.isoformat() if stored_token.expires_at else None,
            "is_expired": is_expired,
            "is_about_to_expire": is_about_to_expire,
            "status": "expired" if is_expired else ("expiring_soon" if is_about_to_expire else "valid")
        }
