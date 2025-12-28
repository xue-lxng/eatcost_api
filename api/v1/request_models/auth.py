import msgspec


class RefreshTokenRequest(msgspec.Struct, omit_defaults=True):
    """Request model for token refresh."""

    jwt: str


class ResetPasswordRequest(msgspec.Struct, omit_defaults=True):
    """Request model for password reset."""

    jwt: str
    email: str
    password: str
