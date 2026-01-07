"""
User API routes.

Provides endpoints for user management.
In production, users would be created via OAuth flow.
"""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.user import UserCreate, UserRead
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create User",
    description="Create a new user. In production, this would be handled by OAuth.",
)
def create_user(
    db: DbSession,
    user_in: UserCreate,
) -> UserRead:
    """
    Create a new user.
    
    This is a stub endpoint for testing. In production,
    users would be created automatically via Google OAuth.
    """
    # Check if email already exists
    existing = user_service.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    user = user_service.create_user(db, user_in)
    return UserRead.model_validate(user)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get Current User",
    description="Get the currently authenticated user's information.",
)
def get_current_user_info(
    current_user: CurrentUser,
) -> UserRead:
    """
    Get current user information.
    
    Requires authentication (X-User-Id header in stub mode).
    """
    return UserRead.model_validate(current_user)
