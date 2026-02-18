from litestar import Router, post, Request
from litestar.exceptions import HTTPException
from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)

from api.v1.request_models.payments import CheckoutRequest
from api.v1.response_models.payments import PaymentResponse
from api.v1.response_models.users import (
    UserMembershipPurchaseResponse,
)
from api.v1.services.auth import AuthService
from api.v1.services.payments import PaymentService


@post("/membership", status_code=HTTP_200_OK)
async def buy_user_membership(
    request: Request,
) -> UserMembershipPurchaseResponse:
    """
    Get payment link for subscription
    """
    jwt_token = request.headers.get("Authorization", None)
    if jwt_token is None:
        raise HTTPException(status_code=401, detail="Authorization token is missing")
    if "Bearer " not in jwt_token:
        raise HTTPException(
            status_code=401, detail="Invalid authorization token format"
        )
    try:
        user = AuthService.decode_jwt_token(jwt_token.replace("Bearer ", ""))
        user_id = user.get("id")

        membership_data = await PaymentService.get_user_membership_payment_url(
            user_id, jwt_token
        )
        return membership_data
    except Exception as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))


@post("/checkout", status_code=HTTP_200_OK)
async def checkout(
    data: CheckoutRequest,
    request: Request,
) -> PaymentResponse:
    """
    Get checkout payment link
    """
    jwt_token = request.headers.get("Authorization", None)
    if jwt_token is None:
        raise HTTPException(status_code=401, detail="Authorization token is missing")
    if "Bearer " not in jwt_token:
        raise HTTPException(
            status_code=401, detail="Invalid authorization token format"
        )
    try:
        user = AuthService.decode_jwt_token(jwt_token.replace("Bearer ", ""))
        user_id = user.get("id")

        membership_data = await PaymentService.create_checkout(
            user_id, jwt_token, data.delivery_type
        )
        return membership_data
    except Exception as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))


router = Router(
    path="/payments",
    tags=["Payments"],
    security=[{"Authentication": ["Bearer"]}],
    route_handlers=[
        checkout,
        buy_user_membership,
    ],
)
