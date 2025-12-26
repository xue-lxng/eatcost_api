import asyncio
from typing import List, Dict, Any, Union

import aiohttp
from aiohttp import ClientError, ClientResponseError
from urllib.parse import unquote

from config import AUTH_KEY, logger

JsonType = Union[str, list, dict, int, float, bool, None]


class WooCommerceUtils:
    def __init__(self, consumer_key, consumer_secret, base_url):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.base_url = base_url
        self.session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures session is closed."""
        if self.session:
            await self.session.close()
        return False

    def __del__(self):
        """Fallback cleanup if context manager is not used."""
        if self.session and not self.session.closed:
            import asyncio
            try:
                asyncio.run(self.session.close())
            except RuntimeError:
                # Event loop already closed, session will be cleaned up by garbage collector
                pass

    def _decode_str_fields(self, data: JsonType) -> JsonType:
        match data:
            case str():
                return unquote(data)
            case list():
                return [self._decode_str_fields(item) for item in data]
            case dict():
                return {key: self._decode_str_fields(value) for key, value in data.items()}
            case _:
                return data

    @staticmethod
    def _to_float(val: Any, default: float = 0.0) -> float:
        """Convert value to float with fallback default."""
        if val in (None, "", False):
            return default
        try:
            return float(val)
        except (TypeError, ValueError):
            return default

    def _get_price(self, raw_value: Any, fallback: float) -> float:
        """Get price value, using fallback if empty."""
        return fallback if raw_value in ("", None) else self._to_float(raw_value, fallback)

    def aggregate_product_data(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate product data from WooCommerce API response.

        Args:
            product: Product data from WooCommerce API response.

        Returns:
            Aggregated product data as a dictionary.
        """
        price = self._to_float(product.get("price", 0) or 0)
        regular_price = self._get_price(product.get("regular_price"), price)
        sale_price = self._get_price(product.get("sale_price"), price)
        attributes = product.get("attributes", [])
        variations = product.get("variations", [])

        simplified_product = {
            "id": product.get("id"),
            "name": product.get("name") or "",
            "slug": product.get("slug") or "",
            "permalink": product.get("permalink") or "",
            "date_created": product.get("date_created") or "",
            "date_modified": product.get("date_modified") or "",
            "type": product.get("type") or "",
            "status": product.get("status") or "",
            "price": price,
            "regular_price": regular_price,
            "sale_price": sale_price,
            "stock_status": product.get("stock_status") or "",
            "categories": product.get("categories", []),
            "images": [image["src"] for image in product.get("images", [])],
            "attributes": attributes,
            "variations": variations,
        }
        return simplified_product

    async def get_products(self, category_id: str = None, page: int = 1):
        """
        Fetch WooCommerce products and organize them by category.

        Args:
            category_id: Optional category ID to filter products
            page: Pagination page number (default: 1)

        Returns:
            List of dictionaries with category_name and items (products)

        Raises:
            RuntimeError: If session is not initialized
            ClientResponseError: If API request fails
            ValueError: If response data is invalid
        """
        logger.info(f"Fetching products - Category: {category_id}, Page: {page}")

        if not self.session:
            error_msg = "Session not initialized. Use 'async with WooCommerceUtils(...) as wc:' to initialize."
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        try:
            async with self.session.get(
                f"{self.base_url}/wp-json/wc/store/v1/products",
                params={"per_page": 100, "category": category_id, "page": page},
                auth=aiohttp.BasicAuth(self.consumer_key, self.consumer_secret)
            ) as response:
                response.raise_for_status()
                raw_products = await response.json() if response.status == 200 else []
                logger.info(f"Retrieved {len(raw_products)} products from WooCommerce")

            if not raw_products:
                logger.warning("No products returned from WooCommerce API")
                return []

            products: List[Dict[str, Any]] = self._decode_str_fields(raw_products)
            categories_map: Dict[int, Dict[str, Any]] = {}

            for product in products:
                try:
                    simplified = self.aggregate_product_data(product)
                    categories = product.get("categories") or []

                    if not categories:
                        uncategorized_id = -1
                        if uncategorized_id not in categories_map:
                            categories_map[uncategorized_id] = {
                                "category_name": "Без категории",
                                "items": [],
                            }
                        categories_map[uncategorized_id]["items"].append(simplified)
                    else:
                        for cat in categories:
                            cat_id = cat.get("id")
                            if cat_id is None:
                                logger.warning(f"Product {product.get('id')} has category with no ID")
                                continue

                            cat_name = cat.get("name") or f"category_{cat_id}"

                            if cat_id not in categories_map:
                                categories_map[cat_id] = {
                                    "category_name": cat_name,
                                    "items": [],
                                }

                            categories_map[cat_id]["items"].append(simplified)
                except Exception as e:
                    logger.error(f"Error processing product {product.get('id')}: {str(e)}")
                    continue

            result = [
                {
                    "category_name": cat_data["category_name"],
                    "items": cat_data["items"],
                }
                for cat_data in categories_map.values()
            ]

            logger.info(f"Processed products into {len(result)} categories")
            return result

        except ClientResponseError as e:
            logger.error(f"WooCommerce API error (products): {e.status} - {e.message}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching products: {str(e)}")
            raise ValueError(f"Failed to fetch products: {str(e)}")

    async def search_products(self, search_query: str, page: int=1):
        """
        Search products by query.

        Args:
            search_query: Search query string
            page: Pagination page number (default: 1)

        Returns:
            List of product dictionaries matching the search query

        Raises:
            RuntimeError: If session is not initialized
            ClientResponseError: If API request fails
            ValueError: If response data is invalid
        """
        logger.info(f"Searching products - Query: {search_query}, Page: {page}")

        if not self.session:
            error_msg = "Session not initialized. Use 'async with WooCommerceUtils(...) as wc:' to initialize."
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        try:
            async with self.session.get(
                f"{self.base_url}/wp-json/wc/store/v1/products",
                params={"per_page": 100, "search": search_query, "page": page},
                auth=aiohttp.BasicAuth(self.consumer_key, self.consumer_secret)
            ) as response:
                response.raise_for_status()
                response_result = await response.json()

                if response.status != 200:
                    logger.warning(f"Search returned status {response.status}")
                    return []
                products = [self.aggregate_product_data(product) for product in response_result]
                logger.info(f"Found {len(products)} products matching query: {search_query}")
                return products

        except ClientResponseError as e:
            logger.error(f"WooCommerce API error (search): {e.status} - {e.message}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error searching products: {str(e)}")
            raise ValueError(f"Failed to search products: {str(e)}")

    async def request_categories(self, page: int) -> List[str]:
        async with self.session.get(
                f"{self.base_url}/wp-json/wc/v3/products/categories",
                params={"per_page": 100, "page": page},
                auth=aiohttp.BasicAuth(self.consumer_key, self.consumer_secret)
        ) as response:
            response.raise_for_status()
            result = await response.json()
            if response.status != 200:
                logger.warning(f"Categories returned status {response.status}")
                return []

            return result


    async def get_categories(self, simplified: bool = True) -> List[str]:
        """
        Fetch all product categories.

        Returns:
            List of category IDs

        Raises:
            RuntimeError: If session is not initialized
            ClientResponseError: If API request fails
            ValueError: If response data is invalid
        """
        logger.info("Fetching product categories")

        if not self.session:
            error_msg = "Session not initialized. Use 'async with WooCommerceUtils(...) as wc:' to initialize."
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        try:
            tasks = [
                self.request_categories(page) for page in range(1, 11)
            ]
            result = await asyncio.gather(
                *tasks
            )


            categories = []
            for cat in result:
                categories.extend(cat)

            if simplified:
                categories_formatted = [
                    item.get("id") for item in categories
                ]
            else:
                categories_formatted = [
                    {
                        "category_id": cat.get("id"),
                        "category_name": cat.get("name"),
                    }
                    for cat in categories
                ]
            logger.info(f"Retrieved {len(categories)} categories")
            return categories_formatted

        except ClientResponseError as e:
            logger.error(f"WooCommerce API error (categories): {e.status} - {e.message}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching categories: {str(e)}")
            raise ValueError(f"Failed to fetch categories: {str(e)}")

    async def register_user(self, email: str, password: str):
        """
        Register a new user using WooCommerce Simple JWT Login.

        Args:
            email: User email
            password: User password

        Returns:
            Dict with JWT token if successful

        Raises:
            RuntimeError: If session is not initialized
            ClientResponseError: If API request fails
            ValueError: If registration fails
        """
        logger.info(f"Registering user: {email}")

        if not self.session:
            error_msg = "Session not initialized. Use 'async with WooCommerceUtils(...) as wc:' to initialize."
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        try:
            async with self.session.post(
                f"{self.base_url}/?rest_route=/simple-jwt-login/v1/users&email={email}&password={password}&AUTH_KEY={AUTH_KEY}",
            ) as response:

                if response.status == 200:
                    result = await response.json()
                    logger.info(f"User registered successfully: {email}")
                    return {"jwt": result.get("jwt")}
                else:
                    error_text = await response.text()
                    logger.error(f"Registration failed for {email}: {response.status} - {error_text}")
                    raise ValueError(f"Registration failed: {response.status} - {error_text}")

        except ClientResponseError as e:
            logger.error(f"WooCommerce API error (registration): {e.status} - {e.message}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error registering user {email}: {str(e)}")
            raise ValueError(f"Failed to register user: {str(e)}")

    async def login_user(self, email: str, password: str):
        """
        Authenticate user using WooCommerce Simple JWT Login.

        Args:
            email: User email
            password: User password

        Returns:
            Dict with JWT token if successful

        Raises:
            RuntimeError: If session is not initialized
            ClientResponseError: If API request fails
            ValueError: If authentication fails
        """
        logger.info(f"Authenticating user: {email}")

        if not self.session:
            error_msg = "Session not initialized. Use 'async with WooCommerceUtils(...) as wc:' to initialize."
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        try:
            async with self.session.post(
                f"{self.base_url}/?rest_route=/simple-jwt-login/v1/auth",
                data={
                    "email": email,
                    "password": password,
                }
            ) as response:

                if response.status == 200:
                    result = await response.json()
                    jwt_token = result.get("data", {}).get("jwt")
                    if jwt_token:
                        logger.info(f"User authenticated successfully: {email}")
                        return {"jwt": jwt_token}
                    else:
                        logger.error(f"Login failed for {email}: No JWT token in response")
                        raise ValueError("Authentication failed: No JWT token returned")
                else:
                    error_text = await response.text()
                    logger.error(f"Authentication failed for {email}: {response.status} - {error_text}")
                    raise ValueError(f"Authentication failed: {response.status} - {error_text}")

        except ClientResponseError as e:
            logger.error(f"WooCommerce API error (login): {e.status} - {e.message}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error authenticating user {email}: {str(e)}")
            raise ValueError(f"Failed to authenticate user: {str(e)}")


    async def refresh_token(self, jwt_token: str) -> str:
        if not self.session:
            error_msg = "Session not initialized. Use 'async with WooCommerceUtils(...) as wc:' to initialize."
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        async with self.session.post(
            f"{self.base_url}/?rest_route=/simple-jwt-login/v1/token/refresh",
                headers={"Authorization": jwt_token}
            ) as response:
            response.raise_for_status()
            result = await response.json()
            return result.get("data", {}).get("jwt")


    async def reset_password(self, jwt_token: str, email: str, password: str) -> bool:
        if not self.session:
            error_msg = "Session not initialized. Use 'async with WooCommerceUtils(...) as wc:' to initialize."
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        async with self.session.put(
            f"{self.base_url}/?api-proxy.php?endpoint=simple-jwt-login/v1/user/reset_password",
                headers={"Authorization": jwt_token},
                json={
                    "email": email,
                    "new_password": password,
                    "AUTH_KEY": AUTH_KEY
                }
            ) as response:
            response.raise_for_status()
            result = await response.json()
            if result.get("success") and result.get("message") == "User Password has been changed.":
                return True
            return False


    def format_cart(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format WooCommerce Store API cart into a minimal structure.

        Ensures each item contains at least `id` and `key`, while keeping
        other practical fields commonly needed by clients.
        """
        try:
            items: List[Dict[str, Any]] = []
            for item in data.get("items", []) or []:
                # image can be a list of dicts with `src` or a list of strings
                image_src = None
                images = item.get("images") or []
                if images:
                    first_img = images[0]
                    if isinstance(first_img, dict):
                        image_src = first_img.get("src")
                    elif isinstance(first_img, str):
                        image_src = first_img

                prices = item.get("prices") or {}
                line_totals = item.get("totals") or {}

                items.append({
                    "key": item.get("key"),
                    "id": item.get("id"),
                    # Optional but useful
                    "name": item.get("name"),
                    "quantity": item.get("quantity"),
                    "type": item.get("type"),
                    "sku": item.get("sku"),
                    "permalink": item.get("permalink"),
                    "image": image_src,
                    # Prices
                    "price": prices.get("price"),
                    "regular_price": prices.get("regular_price"),
                    "sale_price": prices.get("sale_price"),
                    # Line totals
                    "line_total": line_totals.get("line_total"),
                })

            totals = data.get("totals") or {}

            # Simplify shipping packages and rates
            simplified_packages: List[Dict[str, Any]] = []
            for pkg in data.get("shipping_rates", []) or []:
                simplified_packages.append({
                    "package_id": pkg.get("package_id"),
                    "name": pkg.get("name"),
                    "items": [
                        {
                            "key": i.get("key"),
                            "name": i.get("name"),
                            "quantity": i.get("quantity"),
                        }
                        for i in (pkg.get("items") or [])
                    ],
                    "shipping_rates": [
                        {
                            "rate_id": r.get("rate_id"),
                            "name": r.get("name"),
                            "price": r.get("price"),
                            "selected": r.get("selected"),
                        }
                        for r in (pkg.get("shipping_rates") or [])
                    ],
                })

            formatted: Dict[str, Any] = {
                "items": items,
                "totals": {
                    "total_items": totals.get("total_items"),
                    "total_price": totals.get("total_price"),
                    "currency_code": totals.get("currency_code"),
                    "currency_symbol": totals.get("currency_symbol"),
                    "currency_suffix": totals.get("currency_suffix"),
                },
                "items_count": data.get("items_count"),
                "needs_payment": data.get("needs_payment"),
                "needs_shipping": data.get("needs_shipping"),
                "shipping_rates": simplified_packages,
                "payment_methods": data.get("payment_methods") or [],
            }

            return self._decode_str_fields(formatted)
        except Exception as e:
            logger.error(f"Error formatting cart: {str(e)}")
            fallback_items = []
            for item in data.get("items", []) or []:
                fallback_items.append({"key": item.get("key"), "id": item.get("id")})
            return {"items": fallback_items}

    async def get_user_cart(self, jwt_token: str):
        if not self.session:
            error_msg = "Session not initialized. Use 'async with WooCommerceUtils(...) as wc:' to initialize."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        async with self.session.get(
            f"{self.base_url}/wp-json/wc/store/v1/cart",
            headers={"Authorization": jwt_token}
        ) as response:
            response.raise_for_status()
            data = await response.json()
            logger.info(f"JWT Token: {jwt_token}")
            logger.info(f"Cart fetched successfully: {data}")
            cart_token = response.headers.get("Cart-Token")
            return {"items": self.format_cart(data), "cart_token": cart_token}

    async def add_item_to_cart(self, cart_token: str, product_id: int, quantity: int):
        if not self.session:
            error_msg = "Session not initialized. Use 'async with WooCommerceUtils(...) as wc:' to initialize."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        async with self.session.get(
            f"{self.base_url}/wp-json/wc/store/v1/cart",
            json={"id":str(product_id),"quantity":quantity, "cart_token": cart_token }
        ) as response:
            response.raise_for_status()
            data = await response.json()
            status = response.status
            return {"status": status, "data": data}


    async def update_item_in_cart(self, cart_token: str, item_key: str, quantity: int):
        if not self.session:
            error_msg = "Session not initialized. Use 'async with WooCommerceUtils(...) as wc:' to initialize."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        async with self.session.post(
            f"{self.base_url}/wp-json/wc/store/v1/cart/update-item",
            headers={"Cart-Token": cart_token},
            params={
                "key": item_key,
                "quantity": quantity,
            }
        ) as response:
            response.raise_for_status()
            data = await response.json()
            status = response.status
            return {"status": status, "data": data}


    async def delete_item_from_cart(self, cart_token: str, item_key: str, quantity: int):
        if not self.session:
            error_msg = "Session not initialized. Use 'async with WooCommerceUtils(...) as wc:' to initialize."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        async with self.session.post(
            f"{self.base_url}/wp-json/wc/store/v1/cart/remove-item",
            headers={"Cart-Token": cart_token},
            params={
                "key": item_key,
            }
        ) as response:
            response.raise_for_status()
            data = await response.json()
            status = response.status
            return {"status": status, "data": data}


    @staticmethod
    def aggregate_user_data(user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate user data from a product dictionary.
        :param user:
        :return:
        """
        user_data = {
            "email": user.get("email"),
            "first_name": user.get("first_name"),
            "last_name": user.get("last_name"),
            "address": user.get("billing", {}).get("address_1"),
        }
        return user_data


    async def get_user_data(self, user_id: int) -> Dict[str, Any]:
        if not self.session:
            error_msg = "Session not initialized. Use 'async with WooCommerceUtils(...) as wc:' to initialize."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        async with self.session.get(
            f"{self.base_url}/wp-json/wc/v3/customers/{user_id}",
            auth=aiohttp.BasicAuth(self.consumer_key, self.consumer_secret)
        ) as response:
            response.raise_for_status()
            result = await response.json()
            return self.aggregate_user_data(result)


    async def get_user_membership(self, user_id: int):
        if not self.session:
            error_msg = "Session not initialized. Use 'async with WooCommerceUtils(...) as wc:' to initialize."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        async with self.session.get(
            f"{self.base_url}/wp-json/wc/v3/memberships/members",
            params={"customer": user_id},
            auth=aiohttp.BasicAuth(self.consumer_key, self.consumer_secret)
        ) as response:
            response.raise_for_status()
            result = await response.json()
            user = result[0] if result else {}
            return {"plan_name": user.get("plan_name"), "status": user.get("status"), "end_date": user.get("end_date_gmt")}


    async def get_user_membership_qr(self, jwt_token: str):
        if not self.session:
            error_msg = "Session not initialized. Use 'async with WooCommerceUtils(...) as wc:' to initialize."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        async with self.session.get(
            f"{self.base_url}/wp-json/mqrv/v1/qr-code",
            headers={"Authorization": jwt_token}
        ) as response:
            response.raise_for_status()
            result = await response.json()
            return {"qr_code": result.get("qr_code"), "timestamp": result.get("timestamp"), "lifetime": result.get("lifetime")}

    async def reset_user_password(self, jwt_token: str, email: str, new_password: str):
        if not self.session:
            error_msg = "Session not initialized. Use 'async with WooCommerceUtils(...) as wc:' to initialize."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        async with self.session.get(
            f"{self.base_url}/?rest_route=/simple-jwt-login/v1/user/reset_password&email={email}&new_password={new_password}&AUTH_KEY={AUTH_KEY}",
            headers={"Authorization": jwt_token}
        ) as response:
            response.raise_for_status()
            result = await response.json()
            if result.get("success") and result.get("message") == "User Password has been changed.":
                return True
            return False


    async def close(self):
        """Manually close the session (optional if using context manager)."""
        if self.session:
            await self.session.close()