from typing import Literal

import msgspec


class CheckoutRequest(msgspec.Struct, omit_defaults=True):
    delivery_type: Literal["delivery", "pickup"]
