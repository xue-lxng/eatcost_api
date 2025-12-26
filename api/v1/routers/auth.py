import asyncio

from litestar import Router, post, put, Request, status_codes
from litestar.exceptions import HTTPException

from api.v1.response_models.auth import UserRegistrationRequest, UserLoginRequest, AuthResponse, RefreshTokenResponse, ErrorResponse
from api.v1.request_models.auth import RefreshTokenRequest, ResetPasswordRequest
from api.v1.services.auth import AuthService
from api.v1.services.cards import CardsService
from config import logger


@post("/register", status_code=status_codes.HTTP_201_CREATED, tags=["Auth"])
async def register_user(
    request: Request,
    data: UserRegistrationRequest
) -> AuthResponse | ErrorResponse:
    """
    Register a new user using WooCommerce Simple JWT Login.

    Args:
        request: The incoming request object
        data: Registration data containing email, password, and optional username

    Returns:
        AuthResponse with JWT token on success
        ErrorResponse with details on failure

    Raises:
        HTTPException: If registration fails with appropriate status codes
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Auth Router: Registration attempt - Email: {data.email}, IP: {client_ip}")

    try:
        result = await AuthService.register_user(
            email=data.email,
            password=data.password,
            username=data.username
        )

        if "jwt" in result:
            logger.info(f"Auth Router: Registration successful - Email: {data.email}, IP: {client_ip}")
            user = AuthService.decode_jwt_token(result["jwt"].replace("Bearer ", ""))
            user_id = user.get("id")
            asyncio.create_task(CardsService.create_customer(user_id))
            return AuthService.format_auth_response(result["jwt"])
        else:
            error = result.get("error", "Registration failed")
            message = result.get("message", "Unknown error occurred")
            logger.error(f"Auth Router: Registration failed - Email: {data.email}, Error: {error}, Message: {message}, IP: {client_ip}")
            raise HTTPException(
                status_code=status_codes.HTTP_400_BAD_REQUEST,
                detail=AuthService.format_error_response(error, message).__repr__()
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth Router: Unexpected error during registration - Email: {data.email}, Error: {str(e)}, IP: {client_ip}")
        raise HTTPException(
            status_code=status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=AuthService.format_error_response("Internal Server Error", "An unexpected error occurred").__repr__()
        )


@post("/login", status_code=status_codes.HTTP_200_OK, tags=["Auth"])
async def login_user(
    request: Request,
    data: UserLoginRequest
) -> AuthResponse | ErrorResponse:
    """
    Authenticate user and return JWT token using WooCommerce Simple JWT Login.

    Args:
        request: The incoming request object
        data: Login data containing email and password

    Returns:
        AuthResponse with JWT token on success
        ErrorResponse with details on failure

    Raises:
        HTTPException: If authentication fails with appropriate status codes
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Auth Router: Login attempt - Email: {data.email}, IP: {client_ip}")

    try:
        result = await AuthService.login_user(
            email=data.email,
            password=data.password
        )

        if "jwt" in result:
            logger.info(f"Auth Router: Login successful - Email: {data.email}, IP: {client_ip}")
            return AuthService.format_auth_response(result["jwt"])
        else:
            error = result.get("error", "Authentication failed")
            message = result.get("message", "Invalid email or password")
            logger.warning(f"Auth Router: Login failed - Email: {data.email}, Error: {error}, Message: {message}, IP: {client_ip}")
            raise HTTPException(
                status_code=status_codes.HTTP_401_UNAUTHORIZED,
                detail=AuthService.format_error_response(error, message).__repr__()
            )

    except HTTPException:
        # Re-raise HTTP exceptions as they are
        raise
    except Exception as e:
        logger.error(f"Auth Router: Unexpected error during login - Email: {data.email}, Error: {str(e)}, IP: {client_ip}")
        raise HTTPException(
            status_code=status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=AuthService.format_error_response("Internal Server Error", "An unexpected error occurred").__repr__()
        )


@post("/refresh", status_code=status_codes.HTTP_200_OK, tags=["Auth"])
async def refresh_token(
    request: Request,
    data: RefreshTokenRequest
) -> RefreshTokenResponse | ErrorResponse:
    """
    Refresh JWT token using WooCommerce Simple JWT Login.

    Args:
        request: The incoming request object
        data: Refresh token request containing current JWT token

    Returns:
        RefreshTokenResponse with new JWT token on success
        ErrorResponse with details on failure

    Raises:
        HTTPException: If token refresh fails with appropriate status codes
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Auth Router: Token refresh attempt - IP: {client_ip}")

    try:
        new_token = await AuthService.refresh_token(jwt_token=data.jwt)
        logger.info(f"Auth Router: Token refresh successful - IP: {client_ip}")
        return AuthService.format_refresh_token_response(new_token)

    except ValueError as e:
        error = "Token refresh failed"
        message = str(e)
        logger.error(f"Auth Router: Token refresh failed - Error: {error}, Message: {message}, IP: {client_ip}")
        raise HTTPException(
            status_code=status_codes.HTTP_400_BAD_REQUEST,
            detail=AuthService.format_error_response(error, message).__repr__()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth Router: Unexpected error during token refresh - Error: {str(e)}, IP: {client_ip}")
        raise HTTPException(
            status_code=status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=AuthService.format_error_response("Internal Server Error", "An unexpected error occurred").__repr__()
        )


@put("/reset-password", status_code=status_codes.HTTP_200_OK, tags=["Auth"])
async def reset_password(
    request: Request,
    data: ResetPasswordRequest
) -> bool | ErrorResponse:
    """
    Reset user password using WooCommerce Simple JWT Login.

    Args:
        request: The incoming request object
        data: Reset password request containing JWT token, email, and new password

    Returns:
        True if password reset successful
        ErrorResponse with details on failure

    Raises:
        HTTPException: If password reset fails with appropriate status codes
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Auth Router: Password reset attempt - Email: {data.email}, IP: {client_ip}")

    try:
        result = await AuthService.reset_password(
            jwt_token=data.jwt,
            email=data.email,
            password=data.password
        )

        if result:
            logger.info(f"Auth Router: Password reset successful - Email: {data.email}, IP: {client_ip}")
            return result
        else:
            error = "Password reset failed"
            message = "WooCommerce returned no success"
            logger.error(f"Auth Router: Password reset failed - Email: {data.email}, Error: {error}, Message: {message}, IP: {client_ip}")
            raise HTTPException(
                status_code=status_codes.HTTP_400_BAD_REQUEST,
                detail=AuthService.format_error_response(error, message).__repr__()
            )

    except ValueError as e:
        error = "Password reset failed"
        message = str(e)
        logger.error(f"Auth Router: Password reset failed - Email: {data.email}, Error: {error}, Message: {message}, IP: {client_ip}")
        raise HTTPException(
            status_code=status_codes.HTTP_400_BAD_REQUEST,
            detail=AuthService.format_error_response(error, message).__repr__()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth Router: Unexpected error during password reset - Email: {data.email}, Error: {str(e)}, IP: {client_ip}")
        raise HTTPException(
            status_code=status_codes.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=AuthService.format_error_response("Internal Server Error", "An unexpected error occurred").__repr__()
        )


router = Router(path="/auth", route_handlers=[register_user, login_user, refresh_token, reset_password])
