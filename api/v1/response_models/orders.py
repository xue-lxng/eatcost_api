import msgspec
from typing import List, Optional


class OrderLineItem(msgspec.Struct):
    id: int
    product_id: int
    name: str
    quantity: int
    total: str


class OrderShippingLine(msgspec.Struct):
    method_id: str
    method_title: str
    total: str


class OrderBilling(msgspec.Struct):
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    address_1: Optional[str]


class OrderResponse(msgspec.Struct):
    id: int
    status: str
    date_created: Optional[str]
    date_modified: Optional[str]
    total: str
    currency: str
    payment_method: Optional[str]
    payment_method_title: Optional[str]
    transaction_id: Optional[str]
    billing: OrderBilling
    line_items: List[OrderLineItem]
    shipping_lines: List[OrderShippingLine]


class UserOrdersResponse(msgspec.Struct):
    orders: List[OrderResponse]
    count: int
