from typing import List

import msgspec


class AddressSuggestions(msgspec.Struct, omit_defaults=True):
    text: str


class AddressDelivery(msgspec.Struct, omit_defaults=True):
    name: str
    key: str
    is_available: bool


class AddressCheckResponse(msgspec.Struct, omit_defaults=True):
    address: str
    delivery_types: List[AddressDelivery]
