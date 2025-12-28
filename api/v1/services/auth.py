from typing import Dict, Any

import jwt

from api.v1.response_models.auth import AuthResponse, ErrorResponse
from config import (
    CONSUMER_KEY,
    CONSUMER_SECRET,
    BASE_URL,
    logger,
    JWT_SECRET,
    JWT_ALGORITHM,
)
from core.utils.woocommerce import WooCommerceUtils


class AuthService:
    """Authentication service for user registration and login."""

    @staticmethod
    async def register_user(
        email: str, password: str, username: str = None
    ) -> Dict[str, Any]:
        """
        Register a new user using WooCommerce Simple JWT Login.

        Args:
            email: User email
            password: User password
            username: Optional username (not currently used by WooCommerce Simple JWT Login)

        Returns:
            Dict with JWT token on success or error information on failure

        Raises:
            ValueError: If WooCommerceUtils raises ValueError
            RuntimeError: If WooCommerceUtils raises RuntimeError
        """
        logger.info(f"AuthService: Registering user - Email: {email}")

        try:
            async with WooCommerceUtils(CONSUMER_KEY, CONSUMER_SECRET, BASE_URL) as wc:
                result = await wc.register_user(email, password)
                if result and result.get("jwt"):
                    logger.info(
                        f"AuthService: User registered successfully - Email: {email}"
                    )
                    return result
                else:
                    error_msg = "Registration failed: WooCommerce returned no result"
                    logger.error(f"AuthService: {error_msg} - Email: {email}")
                    return {"error": "Registration failed", "message": error_msg}

        except ValueError as e:
            error_msg = f"Registration validation error: {str(e)}"
            logger.error(f"AuthService: {error_msg} - Email: {email}")
            return {"error": "Registration failed", "message": error_msg}
        except RuntimeError as e:
            error_msg = f"Runtime error during registration: {str(e)}"
            logger.error(f"AuthService: {error_msg} - Email: {email}")
            return {"error": "Registration failed", "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error during registration: {str(e)}"
            logger.error(f"AuthService: {error_msg} - Email: {email}")
            return {"error": "Registration error", "message": error_msg}

    @staticmethod
    async def login_user(email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user using WooCommerce Simple JWT Login.

        Args:
            email: User email
            password: User password

        Returns:
            Dict with JWT token on success or error information on failure

        Raises:
            ValueError: If WooCommerceUtils raises ValueError
            RuntimeError: If WooCommerceUtils raises RuntimeError
        """
        logger.info(f"AuthService: Authenticating user - Email: {email}")

        try:
            async with WooCommerceUtils(CONSUMER_KEY, CONSUMER_SECRET, BASE_URL) as wc:
                result = await wc.login_user(email, password)
                if result and result.get("jwt"):
                    logger.info(
                        f"AuthService: User authenticated successfully - Email: {email}"
                    )
                    return result
                else:
                    error_msg = "Authentication failed: Invalid credentials or no JWT token returned"
                    logger.warning(f"AuthService: {error_msg} - Email: {email}")
                    return {"error": "Authentication failed", "message": error_msg}

        except ValueError as e:
            error_msg = f"Authentication validation error: {str(e)}"
            logger.error(f"AuthService: {error_msg} - Email: {email}")
            return {"error": "Authentication failed", "message": error_msg}
        except RuntimeError as e:
            error_msg = f"Runtime error during authentication: {str(e)}"
            logger.error(f"AuthService: {error_msg} - Email: {email}")
            return {"error": "Authentication failed", "message": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error during authentication: {str(e)}"
            logger.error(f"AuthService: {error_msg} - Email: {email}")
            return {"error": "Authentication error", "message": error_msg}

    @staticmethod
    def format_auth_response(jwt_token: str) -> AuthResponse:
        """Format JWT token as AuthResponse."""
        return AuthResponse(jwt=jwt_token)

    @staticmethod
    def format_error_response(error: str, message: str) -> ErrorResponse:
        """Format error as ErrorResponse."""
        return ErrorResponse(error=error, message=message)

    @staticmethod
    async def refresh_token(jwt_token: str) -> str:
        """
        Refresh JWT token using WooCommerce Simple JWT Login.

        Args:
            jwt_token: Current JWT token

        Returns:
            New JWT token

        Raises:
            ValueError: If token refresh fails
        """
        logger.info("AuthService: Refreshing JWT token")

        try:
            async with WooCommerceUtils(CONSUMER_KEY, CONSUMER_SECRET, BASE_URL) as wc:
                result = await wc.refresh_token(jwt_token)
                if result:
                    logger.info("AuthService: Token refreshed successfully")
                    return result
                else:
                    error_msg = "Token refresh failed: No new token returned"
                    logger.error(f"AuthService: {error_msg}")
                    raise ValueError(error_msg)

        except ValueError as e:
            error_msg = f"Token refresh validation error: {str(e)}"
            logger.error(f"AuthService: {error_msg}")
            raise ValueError(error_msg)
        except RuntimeError as e:
            error_msg = f"Runtime error during token refresh: {str(e)}"
            logger.error(f"AuthService: {error_msg}")
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during token refresh: {str(e)}"
            logger.error(f"AuthService: {error_msg}")
            raise ValueError(error_msg)

    @staticmethod
    async def reset_password(jwt_token: str, email: str, password: str) -> bool:
        """
        Reset user password using WooCommerce Simple JWT Login.

        Args:
            jwt_token: JWT token for authorization
            email: User email
            password: New password

        Returns:
            True if password reset successful

        Raises:
            ValueError: If password reset fails
        """
        logger.info(f"AuthService: Resetting password for user - Email: {email}")

        try:
            async with WooCommerceUtils(CONSUMER_KEY, CONSUMER_SECRET, BASE_URL) as wc:
                result = await wc.reset_password(jwt_token, email, password)
                if result:
                    logger.info(
                        f"AuthService: Password reset successful - Email: {email}"
                    )
                    return result
                else:
                    error_msg = "Password reset failed: WooCommerce returned no success"
                    logger.error(f"AuthService: {error_msg} - Email: {email}")
                    raise ValueError(error_msg)

        except ValueError as e:
            error_msg = f"Password reset validation error: {str(e)}"
            logger.error(f"AuthService: {error_msg} - Email: {email}")
            raise ValueError(error_msg)
        except RuntimeError as e:
            error_msg = f"Runtime error during password reset: {str(e)}"
            logger.error(f"AuthService: {error_msg} - Email: {email}")
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during password reset: {str(e)}"
            logger.error(f"AuthService: {error_msg} - Email: {email}")
            raise ValueError(error_msg)

    @staticmethod
    def decode_jwt_token(token: str) -> dict:
        """
        Decodes a JWT token into a dictionary.

        :param token: JWT token string
        :return: Decoded token payload as dictionary
        """
        try:
            decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return decoded
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")
        except Exception as e:
            raise ValueError(f"Token decoding failed: {str(e)}")
