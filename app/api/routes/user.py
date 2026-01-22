from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Form, HTTPException, Response, status
from pydantic.dataclasses import dataclass
from sqlmodel import select
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from app.auth import allow_admin, allow_authorized
from app.auth.password import hash_password, verify_password
from app.auth.session import create_session, delete_session
from app.models import make_db_session
from app.models.users import Role, User

router = APIRouter(
    prefix="/user",
    tags=["User"],
)

HTTP401Unauthorized = HTTPException(
    status_code=HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


@dataclass
class UserData:
    id: int
    username: str
    role: str


@router.get(
    "/me",
    summary="Get current user",
    description="Returns the user info of currently logged in user",
)
async def get_current_user(user: User = Depends(allow_authorized)):
    return UserData(id=user.id, username=user.username, role=user.role)


@router.get(
    "/get/{id}",
    summary="Get user info",
    description="Returns information about requested user",
)
async def get_user_info(id: int, _: User = Depends(allow_authorized)):
    with make_db_session() as session:
        user = session.exec(select(User).where(User.id == id)).first()
        if not user:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND)
        return UserData(id=user.id, username=user.username, role=user.role)


@router.post(
    "/login",
    summary="Login as an user",
    description="Returns a session cookie once authentication is successful",
)
async def login(
    response: Response,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
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
        return {
            "message": "Login successful",
            "user": UserData(id=user.id, username=user.username, role=user.role),
        }


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
@router.post(
    "/create",
    summary="Create User",
    description="Only users with the admin and above role can create users",
)
async def create_user(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    role: Annotated[Role, Form()],
    user=Depends(allow_admin),
):
    with make_db_session() as session:
        if session.exec(select(User).where(User.username == username)).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Username already exists"
            )

        if role == Role.ROOT and user.role != Role.ROOT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="only root users can create root users",
            )

        user = User(username=username, password_hash=hash_password(password), role=role)
        session.add(user)
        session.commit()
        return {
            "message": "User created successfully",
            "user": UserData(id=user.id, username=user.username, role=user.role),
        }


@router.delete(
    "/delete/{id}",
    summary="Delete user",
    description="Only users with the admin and above role can delete users",
)
async def delete_user(id: int, _: User = Depends(allow_admin)):
    with make_db_session() as session:
        user = session.exec(select(User).where(User.id == id)).first()
        if not user:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND)
        if user.role == Role.ROOT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete root user"
            )
        session.delete(user)
        session.commit()
        return {"message": "User deleted successfully"}


@router.patch(
    "/update/name/{id}",
    summary="Update user name",
    description="Updates a username by ID",
)
async def update_user_name(
    id: int,
    username: Annotated[str, Form()],
    requesting_user: User = Depends(allow_admin),
):
    with make_db_session() as session:
        user = session.exec(select(User).where(User.id == id)).first()
        if not user:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND)

        if user.role == Role.ROOT and requesting_user.role != Role.ROOT:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="only root users can rank users to root",
            )

        user.username = username
        session.commit()
        return {
            "message": "username updated successfully",
            "user": UserData(id=user.id, username=user.username, role=user.role),
        }


@router.patch(
    "/update/role/{id}",
    summary="Update user role",
    description="Updates a user role by ID",
)
async def update_user_role(
    id: int,
    role: Annotated[Role, Form()],
    requesting_user: User = Depends(allow_admin),
):
    with make_db_session() as session:
        user = session.exec(select(User).where(User.id == id)).first()
        if not user:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND)

        if user.role == Role.ROOT and requesting_user.role != Role.ROOT:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="only root users can rank users to root",
            )
        user.role = role
        session.commit()
        return {
            "message": "role updated successfully",
            "user": UserData(id=user.id, username=user.username, role=user.role),
        }


@router.patch(
    "/update/password/",
    summary="Update current user password",
    description="Updates current user password",
)
async def update_password(
    id: int,
    current_password: Annotated[str, Form()],
    new_password: Annotated[str, Form()],
    requesting_user: User = Depends(allow_admin),
):
    with make_db_session() as session:
        user = session.exec(select(User).where(User.id == id)).first()
        if not user:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND)

        if not verify_password(user.password_hash, current_password):
            raise HTTP401Unauthorized

        user.password_hash = hash_password(new_password)
        session.commit()
        return {
            "message": "password updated successfully",
            "user": UserData(id=user.id, username=user.username, role=user.role),
        }
