import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Cookie, Depends, HTTPException, status

from app.auth.utils import generateSecureRandomString
from app.models import make_db_session
from app.models.users import Role, Session, SessionWithToken, User

session_expires_in_seconds = 60 * 60 * 24  # 1 day

"""

    Implementing User Sessions

    Refer to Lucia Auth.

    Session Token Format: <SESSION_ID>.<SESSION_SECRET>

"""


async def create_session(user_id: int) -> SessionWithToken:
    """
    # Creating sessions

    The secret is hashed using SHA-256. While SHA-256 is unsuitable for user passwords,
    because the secret has 120 bits of entropy and already unguessable as is, we can
    use a fast hashing algorithm here. Even using the fastest or most efficient
    hardware available, an offline brute-force attack is impossible.
    """
    id = generateSecureRandomString()
    secret = generateSecureRandomString()
    secret_hash = hashlib.sha256(secret.encode()).hexdigest()
    now = datetime.now(timezone.utc)
    session: Session = Session(
        session_id=id, user_id=user_id, secret_hash=secret_hash, created_at=now
    )
    token = f"{id}.{secret}"

    # save session in DB
    with make_db_session() as sql_session:
        sql_session.add(session)
        sql_session.commit()

    return SessionWithToken(session=session, token=token)


invalid_session_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid session token",
    headers={"WWW-Authenticate": "Bearer"},
)


async def validate_session_token(token: str) -> Session:
    """
    # Validating session tokens
    To validate a sessions token, parse out the ID and secret,
    get the session with the ID, check the expiration, and compare the secret against the hash.
    Use constant-time comparison for checking secrets and derived hashes.
    """
    token_parts = token.split(".")
    if len(token_parts) != 2:
        raise invalid_session_exception

    session_id, secret = token_parts
    with make_db_session() as sql_session:
        session = sql_session.get(Session, session_id)
        if not session:
            raise invalid_session_exception

        # Make the naive datetime object from the DB aware of its UTC timezone
        created_at_aware = session.created_at.replace(tzinfo=timezone.utc)

        # Check for expiration
        expiration_time = created_at_aware + timedelta(
            seconds=session_expires_in_seconds
        )
        if datetime.now(timezone.utc) > expiration_time:
            sql_session.delete(session)
            sql_session.commit()
            raise invalid_session_exception

        # Hash the secret from the token
        secret_hash = hashlib.sha256(secret.encode()).hexdigest()

        # Compare hashes in constant time to prevent timing attacks
        if not secrets.compare_digest(secret_hash, session.secret_hash):
            raise invalid_session_exception

        return session


async def delete_session(session_id: str):
    with make_db_session() as sql_session:
        session = sql_session.get(Session, session_id)
        if not session:
            raise invalid_session_exception

        sql_session.delete(session)
        sql_session.commit()


async def get_current_user(
    session_token: str | None = Cookie(default=None),
) -> User:
    if session_token is None:
        raise invalid_session_exception

    session = await validate_session_token(session_token)

    with make_db_session() as sql_session:
        user = sql_session.get(User, session.user_id)
        if not user:
            # This case should ideally not happen if session exists for a user
            raise invalid_session_exception
        return user


class RoleChecker:
    def __init__(self, allowed_roles: list[Role]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)):
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted"
            )
        return user
