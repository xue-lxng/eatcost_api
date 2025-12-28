import msgspec


class UpdateCartRequest(msgspec.Struct, omit_defaults=True):
    key: str
    quantity: int


class AddToCartRequest(msgspec.Struct, omit_defaults=True):
    product_id: int
    quantity: int


class RemoveFromCartRequest(msgspec.Struct, omit_defaults=True):
    product_key: str
