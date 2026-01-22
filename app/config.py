import os

from dotenv import load_dotenv
from loguru import logger

"""

Environment Variables

"""

# The .env file is in the parent directory
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if not os.path.exists(dotenv_path):
    raise FileNotFoundError(f"Error: .env file not found at {dotenv_path}")
else:
    load_dotenv(dotenv_path=dotenv_path)


def get_var(name: str) -> str:
    value = os.getenv(name)
    assert value is not None, f"{name} is not set"
    logger.info(f"Loaded environment variable {name}")
    return value


SECRET_KEY: str = get_var("SECRET_KEY")
ROOT_USER_NAME: str = get_var("ROOT_USER_NAME")
ROOT_USER_PASSWORD: str = get_var("ROOT_USER_PASSWORD")
DATABASE_URL: str = get_var("DATABASE_URL")
