from datetime import datetime
from typing import Optional

import msgspec


class UserResponse(msgspec.Struct, omit_defaults=True):
    email: str
    first_name: str
    last_name: str
    address: str


class UserMembershipResponse(msgspec.Struct, omit_defaults=True):
    plan_name: str
    status: str
    end_date: datetime


class UserMembershipPurchaseResponse(msgspec.Struct, omit_defaults=True):
    payment_url: str


class UserWithMembershipResponse(UserResponse):
    membership: Optional[UserMembershipResponse]


class UserQrResponse(msgspec.Struct, omit_defaults=True):
    qr_code: str
    timestamp: int
    lifetime: int


class CardOutput(msgspec.Struct, omit_defaults=True):
    CardId: str
    Pan: str
    ExpDate: str
