"""API response models for v1."""

from .auth import (
    UserRegistrationRequest,
    UserLoginRequest,
    AuthResponse,
    ErrorResponse,
)
from .products import (
    ProductItem,
    CategoryProducts,
)
from .search import (
    CategoryInfo,
    AttributeInfo,
    AggregatedProduct,
    SearchResponse,
    AutocompleteSuggestion,
    AutocompleteResponse,
)

__all__ = [
    # Auth models
    "UserRegistrationRequest",
    "UserLoginRequest",
    "AuthResponse",
    "ErrorResponse",
    # Product models
    "ProductItem",
    "CategoryProducts",
    # Search models
    "CategoryInfo",
    "AttributeInfo",
    "AggregatedProduct",
    "SearchResponse",
    "AutocompleteSuggestion",
    "AutocompleteResponse",
]
