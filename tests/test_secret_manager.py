import os
from google.cloud import secretmanager
from app.core.config import settings

def setup_credentials():
    # Si viene configurado en Settings, lo pasamos al entorno
    if settings.GOOGLE_APPLICATION_CREDENTIALS:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS

def test_access_secret_manager():
    setup_credentials()

    client = secretmanager.SecretManagerServiceClient()

    name = f"projects/{settings.GCP_PROJECT_ID}/secrets/{settings.SECRET_NAME}/versions/latest"
    response = client.access_secret_version(request={"name": name})

    payload = response.payload.data.decode("utf-8")
    print(f"✅ Secret leído correctamente: {payload}")

    assert payload  # simple check


if __name__ == "__main__":
    test_access_secret_manager()
