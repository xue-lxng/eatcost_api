import msgspec


class PaymentResponse(msgspec.Struct, omit_defaults=True):
    payment_url: str
