"""Repository for Google Cloud Secret Manager operations."""
import json
import logging
from typing import Optional
from google.cloud import secretmanager
from google.api_core import exceptions as gcp_exceptions

from ..models.token import DropboxToken
from ..core.config import settings

logger = logging.getLogger(__name__)


class SecretManagerRepository:
    """Repository for managing secrets in Google Cloud Secret Manager."""

    def __init__(self):
        """Initialize Secret Manager client."""
        self.client = secretmanager.SecretManagerServiceClient()
        self.project_id = settings.GCP_PROJECT_ID
        self.secret_id = settings.SECRET_NAME

    def get_token(self) -> Optional[DropboxToken]:
        """
        Retrieve token from Secret Manager.

        Returns:
            DropboxToken if found, None otherwise
        """
        try:
            name = f"projects/{self.project_id}/secrets/{self.secret_id}/versions/latest"
            response = self.client.access_secret_version(request={"name": name})
            payload = response.payload.data.decode("UTF-8")

            token_data = json.loads(payload)
            logger.info(f"Token retrieved successfully from Secret Manager: {self.secret_id}")

            return DropboxToken(**token_data)

        except gcp_exceptions.NotFound:
            logger.warning(f"Secret {self.secret_id} not found in Secret Manager")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding token JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving token from Secret Manager: {e}")
            raise

    def save_token(self, token: DropboxToken) -> bool:
        """
        Save or update token in Secret Manager.

        Args:
            token: DropboxToken to save

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert token to JSON
            token_dict = token.model_dump(mode='json')
            payload = json.dumps(token_dict, default=str).encode("UTF-8")

            parent = f"projects/{self.project_id}/secrets/{self.secret_id}"

            # Add new version to the secret
            response = self.client.add_secret_version(
                request={
                    "parent": parent,
                    "payload": {"data": payload}
                }
            )

            logger.info(f"Token saved successfully to Secret Manager: {response.name}")
            return True

        except gcp_exceptions.NotFound:
            # Secret doesn't exist, create it
            logger.info(f"Secret {self.secret_id} not found, creating new secret")
            return self._create_secret_and_add_version(payload)
        except Exception as e:
            logger.error(f"Error saving token to Secret Manager: {e}")
            raise

    def _create_secret_and_add_version(self, payload: bytes) -> bool:
        """
        Create a new secret and add initial version.

        Args:
            payload: Encoded secret data

        Returns:
            True if successful
        """
        try:
            parent = f"projects/{self.project_id}"

            # Create the secret
            secret = self.client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": self.secret_id,
                    "secret": {
                        "replication": {"automatic": {}}
                    }
                }
            )

            logger.info(f"Secret created: {secret.name}")

            # Add the first version
            version = self.client.add_secret_version(
                request={
                    "parent": secret.name,
                    "payload": {"data": payload}
                }
            )

            logger.info(f"Initial version added: {version.name}")
            return True

        except Exception as e:
            logger.error(f"Error creating secret: {e}")
            raise

    def delete_token(self) -> bool:
        """
        Delete token from Secret Manager.

        Returns:
            True if successful
        """
        try:
            name = f"projects/{self.project_id}/secrets/{self.secret_id}"
            self.client.delete_secret(request={"name": name})

            logger.info(f"Secret {self.secret_id} deleted successfully")
            return True

        except gcp_exceptions.NotFound:
            logger.warning(f"Secret {self.secret_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error deleting secret: {e}")
            raise
