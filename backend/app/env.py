import os

import dotenv
from loguru import logger

dotenv.load_dotenv()


_SUPER_USER_NAME = os.getenv("SUPER_USER_NAME")
_SUPER_USER_EMAIL = os.getenv("SUPER_USER_EMAIL")
_SUPER_USER_PASSWORD = os.getenv("SUPER_USER_PASSWORD")
_JWT_SECRET = os.getenv("JWT_SECRET")
_DATABASE_URL = os.getenv("DATABASE_URL")

assert _SUPER_USER_NAME is not None
assert _SUPER_USER_EMAIL is not None
assert _SUPER_USER_PASSWORD is not None
assert _JWT_SECRET is not None
assert _DATABASE_URL is not None

logger.info("Environment Variables Loaded")


def get_super_user_name() -> str:
    return _SUPER_USER_NAME  # type: ignore


def get_super_user_email() -> str:
    return _SUPER_USER_EMAIL  # type: ignore


def get_super_user_password() -> str:
    return _SUPER_USER_PASSWORD  # type: ignore


def get_jwt_secret() -> str:
    return _JWT_SECRET  # type: ignore


def get_database_url() -> str:
    return _DATABASE_URL  # type: ignore
