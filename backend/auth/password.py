import hashlib
import hmac

from passlib.hash import argon2

from config import SECRET_KEY


def pepper(password: str) -> str:
    """
    Peppering significantly raises the security bar by making a stolen database much less
    useful to an attacker. However, it also means that if an attacker compromises your
    application server (gaining access to your environment variables or config files),
    they will likely get both the database access and the pepper, rendering it ineffective.

    It shifts the critical point of failure from the database alone to the application's runtime environment"""
    return hmac.new(SECRET_KEY.encode(), password.encode(), hashlib.sha256).hexdigest()


def hash_password(password: str) -> str:
    """
    We always store the peppered password hash in the database, not the raw password.
    This ensures that even if the database is compromised, the attacker cannot use the
    password to log in directly.
    """
    return argon2.hash(pepper(password))


def verify_password(hash: str, password: str) -> bool:
    """
    Constant time comparison to prevent timing attacks.
    """
    return argon2.verify(pepper(password), hash)
