"""Authentication service for validating requests."""
import hashlib
import hmac
import logging
from typing import Optional

from ..core.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling authentication and authorization."""

    def __init__(self):
        """Initialize authentication service."""
        self.secret_key = settings.API_SECRET_KEY

    def validate_signature(self, signature: str) -> bool:
        """
        Validate the request signature.

        Args:
            signature: The signature to validate

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Option 1: Simple secret key validation
            if settings.AUTH_MODE == "simple":
                is_valid = signature == self.secret_key
                if is_valid:
                    logger.info("Signature validated successfully (simple mode)")
                else:
                    logger.warning("Invalid signature (simple mode)")
                return is_valid

            # Option 2: HMAC-based validation
            elif settings.AUTH_MODE == "hmac":
                return self._validate_hmac_signature(signature)

            else:
                logger.error(f"Unknown auth mode: {settings.AUTH_MODE}")
                return False

        except Exception as e:
            logger.error(f"Error validating signature: {e}")
            return False

    def _validate_hmac_signature(self, signature: str) -> bool:
        """
        Validate HMAC signature.

        Args:
            signature: The signature to validate

        Returns:
            True if valid
        """
        try:
            # In a real scenario, you would include timestamp and other data
            # For now, we'll validate against allowed signatures list
            allowed_signatures = settings.ALLOWED_SIGNATURES

            is_valid = signature in allowed_signatures
            if is_valid:
                logger.info("HMAC signature validated successfully")
            else:
                logger.warning("Invalid HMAC signature")

            return is_valid

        except Exception as e:
            logger.error(f"Error in HMAC validation: {e}")
            return False

    def generate_signature(self, data: str) -> str:
        """
        Generate HMAC signature for data.

        Args:
            data: Data to sign

        Returns:
            HMAC signature
        """
        try:
            signature = hmac.new(
                self.secret_key.encode(),
                data.encode(),
                hashlib.sha256
            ).hexdigest()

            return signature

        except Exception as e:
            logger.error(f"Error generating signature: {e}")
            raise

    def is_authorized(self, signature: str, service: str = "dropbox") -> bool:
        """
        Check if request is authorized.

        Args:
            signature: Request signature
            service: Service being requested

        Returns:
            True if authorized
        """
        # Validate signature
        if not self.validate_signature(signature):
            return False

        # Additional authorization logic can be added here
        # For example, checking if the signature has access to specific services

        logger.info(f"Request authorized for service: {service}")
        return True
