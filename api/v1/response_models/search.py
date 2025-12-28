from typing import Optional, List

import msgspec


class CategoryInfo(msgspec.Struct, omit_defaults=True):
    """Category information for products."""

    id: int
    name: str


class AttributeInfo(msgspec.Struct, omit_defaults=True):
    """Product attribute information."""

    name: str
    options: List[str]


class AggregatedProduct(msgspec.Struct, omit_defaults=True):
    """Aggregated product data from WooCommerce."""

    id: int
    name: str
    slug: str
    permalink: str
    type: str
    status: str
    price: float
    regular_price: float
    sale_price: float
    on_sale: bool
    purchasable: bool
    stock_status: str
    categories: List[CategoryInfo]
    attributes: List[AttributeInfo]
    description: Optional[str] = None
    short_description: Optional[str] = None
    average_rating: Optional[float] = None
    rating_count: int = 0
    image: Optional[str] = None
    featured: bool = False


class SearchResponse(msgspec.Struct, omit_defaults=True):
    """Response model for product search."""

    query: str
    count: int
    results: List[AggregatedProduct]


class AutocompleteSuggestion(msgspec.Struct, omit_defaults=True):
    """Single autocomplete suggestion item."""

    text: str
    display: str
    type: str  # "full" or "next_word"


class AutocompleteResponse(msgspec.Struct, omit_defaults=True):
    """Response model for search autocomplete."""

    suggestions: List[AutocompleteSuggestion]
    query: str
    mode: str  # "full" or "next_word"
    prefix: str
