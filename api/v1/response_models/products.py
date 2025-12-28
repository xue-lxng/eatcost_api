from typing import List, Dict, Any

import msgspec


class ProductAttribute(msgspec.Struct, omit_defaults=True):
    class AttributeTerms(msgspec.Struct, omit_defaults=True):
        id: int
        name: str
        slug: str

    id: int
    name: str
    taxonomy: str | None
    has_variations: bool
    terms: List[AttributeTerms]


class ProductVariation(msgspec.Struct, omit_defaults=True):
    class VariationAttribute(msgspec.Struct, omit_defaults=True):
        name: str
        value: str

    id: int
    attributes: List[VariationAttribute]


class ProductItem(msgspec.Struct, omit_defaults=True):
    id: int
    name: str
    slug: str
    permalink: str
    date_created: str
    date_modified: str
    type: str
    status: str
    price: float
    regular_price: float
    sale_price: float
    stock_status: str
    categories: List[Dict[str, Any]]
    images: List[str]
    attributes: List[ProductAttribute]


class CategoryProducts(msgspec.Struct, omit_defaults=True):
    category_name: str
    items: List[ProductItem]


class Category(msgspec.Struct, omit_defaults=True):
    category_id: int
    category_name: str
    image: str
