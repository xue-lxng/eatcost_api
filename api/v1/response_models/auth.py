from typing import Optional

import msgspec


class UserRegistrationRequest(msgspec.Struct, omit_defaults=True):
    """Request model for user registration."""

    email: str
    password: str
    username: Optional[str] = None


class UserLoginRequest(msgspec.Struct, omit_defaults=True):
    """Request model for user login."""

    email: str
    password: str


class AuthResponse(msgspec.Struct, omit_defaults=True):
    """Response model for authentication (JWT token)."""

    jwt: str


class RefreshTokenResponse(msgspec.Struct, omit_defaults=True):
    """Response model for token refresh."""

    jwt: str


class ErrorResponse(msgspec.Struct, omit_defaults=True):
    """Error response model."""

    error: str
    message: str
