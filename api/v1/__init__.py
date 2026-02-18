from litestar import Router

from api.v1.routers import auth, products, cart, users, addresses, callbacks, payments

router = Router(
    path="/v1",
    route_handlers=[
        auth.router,
        products.router,
        cart.router,
        users.router,
        addresses.router,
        callbacks.router,
        payments.router,
    ],
)
