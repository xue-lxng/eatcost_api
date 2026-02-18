from typing import Dict, Any

from litestar import Router, get, put, delete, post, Request
from litestar.exceptions import HTTPException
from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_401_UNAUTHORIZED,
)

from api.v1.request_models.users import UserUpdateRequest
from api.v1.response_models.users import (
    UserWithMembershipResponse,
    UserQrResponse as UserQrResponseModel,
    UserMembershipResponse,
    CardOutput,
    UserMembershipPurchaseResponse,
)
from api.v1.services.auth import AuthService
from api.v1.services.cards import CardsService
from api.v1.services.users import UsersService


@get("/profile", status_code=HTTP_200_OK)
async def get_current_user_profile(
    request: Request,
) -> UserWithMembershipResponse:
    """
    Get current user profile
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

        if not user_id:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST, detail="User ID not found in token"
            )

        return await UsersService.get_user_by_id(user_id)
    except Exception as e:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=str(e))


@put("/profile", status_code=HTTP_200_OK)
async def update_current_user_profile(
    user_update: UserUpdateRequest,
    token: str = "Bearer",  # Will be extracted from dependency injection
) -> Dict[str, Any]:
    """
    Update current user profile
    """
    try:
        user = AuthService.decode_jwt_token(token.replace("Bearer ", ""))
        user_id = user.get("id")

        if not user_id:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST, detail="User ID not found in token"
            )

        update_data = user_update.to_dict(exclude_unset=True)
        user_data = await UsersService.update_user(user_id, update_data)
        return {"data": user_data, "message": "User profile updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail={"error": "update_failed", "message": str(e)},
        )


@get("/membership", status_code=HTTP_200_OK)
async def get_user_membership(
    request: Request,
) -> UserMembershipResponse:
    """
    Get user membership details
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

        membership_data = await UsersService.get_user_membership(user_id)
        return membership_data
    except Exception as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))


@post("/membership", status_code=HTTP_200_OK)
async def buy_user_membership(
    request: Request,
) -> UserMembershipPurchaseResponse:
    """
    Get user membership details
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

        membership_data = await UsersService.get_user_membership_payment_url(
            user_id, jwt_token
        )
        return membership_data
    except Exception as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))


@get("/membership_qr", status_code=HTTP_200_OK)
async def get_user_qr(
    request: Request,
) -> UserQrResponseModel:
    """
    Get user QR code for membership
    """
    jwt_token = request.headers.get("Authorization", None)
    if jwt_token is None:
        raise HTTPException(status_code=401, detail="Authorization token is missing")
    if "Bearer " not in jwt_token:
        raise HTTPException(
            status_code=401, detail="Invalid authorization token format"
        )
    try:
        qr_data = await UsersService.get_user_qr(jwt_token)
        return qr_data
    except Exception as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))


@get("/cards", status_code=HTTP_200_OK)
async def get_users_cards(
    request: Request,
) -> CardOutput:
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
        cards_data = await CardsService.get_users_cards(user_id)
        return cards_data
    except Exception as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))


@post("/cards/connect", status_code=HTTP_200_OK)
async def connect_new_card(
    request: Request,
) -> Dict[str, Any]:
    """
    Get URL to connect new card to user's account
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

        if not user_id:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST, detail="User ID not found in token"
            )

        connect_url = await CardsService.get_url_to_connect_new_card(user_id)
        return {
            "data": {"connect_url": connect_url},
            "message": "Card connection URL generated successfully",
        }
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@delete("/cards/{card_id:str}", status_code=HTTP_200_OK)
async def remove_user_card(
    request: Request,
    card_id: str,
) -> Dict[str, Any]:
    """
    Remove card from user's account
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

        if not user_id:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST, detail="User ID not found in token"
            )

        result = await CardsService.remove_card_from_user(user_id, card_id)
        return {"data": result, "message": "Card removed successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


router = Router(
    path="/users",
    tags=["Users"],
    security=[{"Authentication": ["Bearer"]}],
    route_handlers=[
        get_current_user_profile,
        update_current_user_profile,
        get_user_membership,
        get_user_qr,
        get_users_cards,
        connect_new_card,
        remove_user_card,
    ],
)
