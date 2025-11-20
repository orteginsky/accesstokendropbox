"""API routes for token management."""
import logging
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from ..models.token import TokenRequest, TokenResponse
from ..services.token_service import TokenService
from ..services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_auth_service() -> AuthService:
    """Dependency injection for AuthService."""
    return AuthService()


def get_token_service() -> TokenService:
    """Dependency injection for TokenService."""
    return TokenService()


@router.post(
    "/token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Get valid Dropbox access token",
    description="Retrieve a valid Dropbox access token. If the current token is expired, it will be automatically refreshed."
)
async def get_token(
    request: TokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
    token_service: TokenService = Depends(get_token_service)
) -> TokenResponse:
    """
    Get a valid Dropbox access token.

    Args:
        request: TokenRequest with signature
        auth_service: Authentication service (injected)
        token_service: Token service (injected)

    Returns:
        TokenResponse with valid access token

    Raises:
        HTTPException: If authentication fails or token cannot be retrieved
    """
    try:
        # Validate signature
        if not auth_service.is_authorized(request.signature, request.service):
            logger.warning(f"Unauthorized access attempt with signature: {request.signature[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature or unauthorized access"
            )

        # Get valid token
        token_response = token_service.get_valid_token()

        logger.info(f"Token provided successfully (refreshed: {token_response.refreshed})")
        return token_response

    except ValueError as e:
        logger.error(f"Value error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while retrieving token"
        )


@router.post(
    "/token/initialize",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize token with authorization code",
    description="Initialize the Dropbox token for the first time using an OAuth authorization code."
)
async def initialize_token(
    authorization_code: str,
    signature: str,
    auth_service: AuthService = Depends(get_auth_service),
    token_service: TokenService = Depends(get_token_service)
) -> TokenResponse:
    """
    Initialize token for first-time setup.

    Args:
        authorization_code: OAuth authorization code from Dropbox
        signature: Authentication signature
        auth_service: Authentication service (injected)
        token_service: Token service (injected)

    Returns:
        TokenResponse with new token
    """
    try:
        # Validate signature
        if not auth_service.validate_signature(signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )

        # Initialize token
        token_response = token_service.initialize_token(authorization_code)

        logger.info("Token initialized successfully")
        return token_response

    except Exception as e:
        logger.error(f"Error initializing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initializing token: {str(e)}"
        )


@router.post(
    "/token/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Force refresh token",
    description="Force refresh the Dropbox access token regardless of its current state."
)
async def refresh_token(
    signature: str,
    auth_service: AuthService = Depends(get_auth_service),
    token_service: TokenService = Depends(get_token_service)
) -> TokenResponse:
    """
    Force refresh the access token.

    Args:
        signature: Authentication signature
        auth_service: Authentication service (injected)
        token_service: Token service (injected)

    Returns:
        TokenResponse with refreshed token
    """
    try:
        # Validate signature
        if not auth_service.validate_signature(signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )

        # Force refresh
        token_response = token_service.force_refresh_token()

        logger.info("Token force refreshed successfully")
        return token_response

    except ValueError as e:
        logger.error(f"Value error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error refreshing token: {str(e)}"
        )


@router.get(
    "/token/info",
    status_code=status.HTTP_200_OK,
    summary="Get token information",
    description="Get information about the current stored token (requires authentication)."
)
async def get_token_info(
    signature: str,
    auth_service: AuthService = Depends(get_auth_service),
    token_service: TokenService = Depends(get_token_service)
):
    """
    Get information about the current token.

    Args:
        signature: Authentication signature
        auth_service: Authentication service (injected)
        token_service: Token service (injected)

    Returns:
        Token information
    """
    try:
        # Validate signature
        if not auth_service.validate_signature(signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )

        # Get token info
        token_info = token_service.get_token_info()

        return JSONResponse(content=token_info)

    except Exception as e:
        logger.error(f"Error getting token info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting token info: {str(e)}"
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check if the service is running."
)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "accesstokendropbox"
    }
