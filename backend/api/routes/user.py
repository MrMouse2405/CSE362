from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlmodel import select

from auth import allow_admin, allow_authorized, allow_root, allow_student, allow_teacher
from auth.password import verify_password
from auth.session import create_session, delete_session
from models import make_db_session
from models.users import User

router = APIRouter(
    prefix="/user",
    tags=["User"],
)

HTTP401Unauthorized = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


@router.post(
    "/login",
    summary="Login as an user",
    description="Returns a session cookie once authentication is successful",
)
async def login(username: str, password: str, response: Response):
    with make_db_session() as session:
        user = session.exec(select(User).where(User.username == username)).first()

        if not user:
            raise HTTP401Unauthorized

        if not verify_password(user.password_hash, password):
            raise HTTP401Unauthorized

        session_with_token = await create_session(user.id)
        response.set_cookie(
            key="session_token",
            value=session_with_token.token,
            httponly=True,
            secure=True,
            samesite="lax",
        )
        return {"message": "Login successful"}


@router.post(
    "/logout",
    summary="Logout",
    description="Deletes the session cookie",
)
async def logout(response: Response, session_token: str | None = Cookie(default=None)):
    if session_token:
        try:
            session_id = session_token.split(".")[0]
            await delete_session(session_id)
        except IndexError:
            # The token is malformed, but we should still delete the cookie
            pass
    response.delete_cookie(key="session_token")
    return {"message": "Logout successful"}


# Only if user is authenticated as root and above
@router.get(
    "/root",
    summary="Root route",
    description="This route is only accessible to users with the 'root' role.",
)
async def root_route(user=Depends(allow_root)):
    return {"message": "Root route"}
