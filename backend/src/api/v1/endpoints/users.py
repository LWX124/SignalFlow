"""User endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.api.deps import get_current_user, get_user_service
from src.services.user_service import UserService
from src.domain.entities.user import UserEntity

router = APIRouter(prefix="/users")


class UserResponse(BaseModel):
    id: str
    email: str
    nickname: str | None
    avatar_url: str | None
    role: str
    tier: str
    tier_expires_at: str | None
    is_active: bool
    created_at: str | None


class UpdateProfileRequest(BaseModel):
    nickname: str | None = None
    avatar_url: str | None = None
    phone: str | None = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[UserEntity, Depends(get_current_user)],
):
    """Get current user information."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        nickname=current_user.nickname,
        avatar_url=current_user.avatar_url,
        role=current_user.role.value,
        tier=current_user.tier.value,
        tier_expires_at=current_user.tier_expires_at.isoformat() if current_user.tier_expires_at else None,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None,
    )


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: Annotated[UserEntity, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """Update current user profile."""
    updated = await user_service.update_profile(
        user_id=current_user.id,
        nickname=request.nickname,
        avatar_url=request.avatar_url,
        phone=request.phone,
    )

    return UserResponse(
        id=str(updated.id),
        email=updated.email,
        nickname=updated.nickname,
        avatar_url=updated.avatar_url,
        role=updated.role.value,
        tier=updated.tier.value,
        tier_expires_at=updated.tier_expires_at.isoformat() if updated.tier_expires_at else None,
        is_active=updated.is_active,
        created_at=updated.created_at.isoformat() if updated.created_at else None,
    )


@router.post("/me/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: Annotated[UserEntity, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """Change current user password."""
    await user_service.change_password(
        user_id=current_user.id,
        old_password=request.old_password,
        new_password=request.new_password,
    )
    return {"message": "Password changed successfully"}
