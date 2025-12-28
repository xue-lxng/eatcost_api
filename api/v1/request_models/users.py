from typing import Optional

import msgspec


class UserUpdateRequest(msgspec.Struct, omit_defaults=True):
    email: Optional[str]
    password: Optional[str]
    username: Optional[str]
