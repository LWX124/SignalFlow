"""Authentication endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from src.api.deps import get_user_service
from src.services.user_service import UserService
from src.core.exceptions import EmailAlreadyExistsError, InvalidCredentialsError

router = APIRouter(prefix="/auth")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    nickname: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    nickname: str | None
    role: str
    tier: str


class AuthResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse


@router.post("/register", response_model=AuthResponse)
async def register(
    request: RegisterRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """Register a new user."""
    try:
        user = await user_service.register(
            email=request.email,
            password=request.password,
            nickname=request.nickname,
        )

        user_entity, access_token, refresh_token = await user_service.authenticate(
            email=request.email,
            password=request.password,
        )

        return AuthResponse(
            user=UserResponse(
                id=str(user_entity.id),
                email=user_entity.email,
                nickname=user_entity.nickname,
                role=user_entity.role.value,
                tier=user_entity.tier.value,
            ),
            tokens=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
            ),
        )
    except EmailAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """Login with email and password."""
    try:
        user, access_token, refresh_token = await user_service.authenticate(
            email=request.email,
            password=request.password,
        )

        return AuthResponse(
            user=UserResponse(
                id=str(user.id),
                email=user.email,
                nickname=user.nickname,
                role=user.role.value,
                tier=user.tier.value,
            ),
            tokens=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
            ),
        )
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """Refresh access token using refresh token."""
    from src.core.security import verify_refresh_token, create_access_token, create_refresh_token

    payload = verify_refresh_token(request.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = payload.get("sub")
    user = await user_service.get_by_id(user_id)

    access_token = create_access_token({"sub": str(user.id), "email": user.email})
    new_refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.post("/logout")
async def logout():
    """Logout current user. Client should discard tokens."""
    return {"message": "Successfully logged out"}
