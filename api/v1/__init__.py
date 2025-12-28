from litestar import Router

from api.v1.routers import auth, products, cart, users

router = Router(
    path="/v1", route_handlers=[auth.router, products.router, cart.router, users.router]
)
