import os
from pathlib import Path

import dotenv
from loguru import logger

dotenv.load_dotenv()


logger.remove()  # Remove default handler

# Add only console handler
logger.add(
    sink=lambda msg: print(msg, end=""),  # Console output
    level="INFO",
    format="{time:HH:mm:ss} | {level} | {message}",
)

CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
BASE_URL = os.getenv("BASE_URL")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
REDIS_URL = os.getenv("REDIS_URL")
AUTH_KEY = os.getenv("AUTH_KEY")
TERMINAL_ID = os.getenv("TERMINAL_ID")
TERMINAL_PASSWORD = os.getenv("TERMINAL_PASSWORD")

Path("logs").mkdir(exist_ok=True)
