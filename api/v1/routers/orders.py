from litestar import Router, get, Request
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_200_OK, HTTP_400_BAD_REQUEST
from typing import Optional

from api.v1.response_models.orders import UserOrdersResponse
from api.v1.services.auth import AuthService
from api.v1.services.orders import OrderService


@get("/", status_code=HTTP_200_OK)
async def get_user_orders(
    request: Request,
    status: Optional[str] = "any",
    page: int = 1,
    per_page: int = 20,
) -> UserOrdersResponse:
    """
    Get all orders for the authenticated user
    """
    jwt_token = request.headers.get("Authorization", None)
    if jwt_token is None:
        raise HTTPException(status_code=401, detail="Authorization token is missing")
    if "Bearer " not in jwt_token:
        raise HTTPException(status_code=401, detail="Invalid authorization token format")

    try:
        user = AuthService.decode_jwt_token(jwt_token.replace("Bearer ", ""))
        user_id = user.get("id")
        result = await OrderService.get_user_orders(
            user_id=user_id,
            status=status,
            page=page,
            per_page=per_page,
        )
        return UserOrdersResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))


router = Router(
    path="/orders",
    tags=["Orders"],
    security=[{"Authentication": ["Bearer"]}],
    route_handlers=[get_user_orders],
)
