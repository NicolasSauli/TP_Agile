"""
Authentication router - FastAPI routes for authentication
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional
from datetime import datetime

from .models import (
    UserCreate, UserPublic, LoginRequest, LoginResponse,
    MessageResponse, Token
)
from .service import AuthService
from .dependencies import (
    get_current_user, get_current_active_user, get_current_superuser,
    get_optional_user, settings
)

# Create router
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """
    Register a new user.
    
    Args:
        user_data: UserCreate model with username, email, password
        
    Returns:
        UserPublic model with created user information
        
    Raises:
        HTTPException: If username or email already exists
    """
    try:
        user = AuthService.create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    request: Request,
    login_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Authenticate user and return JWT tokens.
    
    This endpoint accepts form data with username and password.
    
    Args:
        request: FastAPI request for IP and user agent
        login_data: OAuth2 password request form with username and password
        
    Returns:
        LoginResponse with user information and access token
        
    Raises:
        HTTPException: If authentication fails
    """
    # Convert OAuth2 form to LoginRequest
    login_request = LoginRequest(
        username=login_data.username,
        password=login_data.password
    )
    
    # Get client info
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Authenticate
    login_response = AuthService.login(
        login_request,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if login_response is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return login_response


@router.post("/login/json", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login_json(
    request: Request,
    login_data: LoginRequest
):
    """
    Authenticate user with JSON body.
    
    Alternative to /login that accepts JSON instead of form data.
    
    Args:
        request: FastAPI request for IP and user agent
        login_data: LoginRequest with username and password
        
    Returns:
        LoginResponse with user information and access token
        
    Raises:
        HTTPException: If authentication fails
    """
    # Get client info
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Authenticate
    login_response = AuthService.login(
        login_data,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if login_response is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return login_response


@router.post("/logout", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def logout(request: Request):
    """
    Invalidate the current user session.
    
    Args:
        request: FastAPI request containing the authorization header
        
    Returns:
        MessageResponse with logout confirmation
        
    Raises:
        HTTPException: If not authenticated or logout fails
    """
    auth_header = request.headers.get("Authorization")
    
    if auth_header is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Remove "Bearer " prefix
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    else:
        token = auth_header
    
    success = AuthService.logout(token)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Logout failed"
        )
    
    return MessageResponse(message="Successfully logged out")


@router.post("/refresh", response_model=Token, status_code=status.HTTP_200_OK)
async def refresh_token(request: Request):
    """
    Refresh access token using a refresh token.
    
    Args:
        request: FastAPI request containing the refresh token in body
        
    Returns:
        Token with new access token
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    # Get refresh token from request body
    request_data = await request.json()
    refresh_token = request_data.get("refresh_token")
    
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token is required"
        )
    
    new_token = AuthService.refresh_token(refresh_token)
    
    if new_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return Token(access_token=new_token, token_type="bearer")


@router.get("/me", response_model=UserPublic, status_code=status.HTTP_200_OK)
async def get_current_user_endpoint(
    current_user: UserPublic = Depends(get_current_user)
):
    """
    Get the current authenticated user.
    
    Args:
        current_user: User from dependency injection
        
    Returns:
        UserPublic model with current user information
    """
    return current_user


@router.get("/users", response_model=dict, status_code=status.HTTP_200_OK)
async def list_users(
    limit: int = 100,
    offset: int = 0,
    current_user: UserPublic = Depends(get_current_superuser)
):
    """
    List all users (requires superuser privileges).
    
    Args:
        limit: Maximum number of users to return
        offset: Number of users to skip
        current_user: Superuser from dependency injection
        
    Returns:
        Dictionary with users list and pagination info
    """
    return AuthService.list_users(limit=limit, offset=offset)


@router.get("/users/{user_id}", response_model=UserPublic, status_code=status.HTTP_200_OK)
async def get_user(
    user_id: int,
    current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Get a specific user by ID.
    
    Args:
        user_id: ID of the user to retrieve
        current_user: Authenticated user from dependency injection
        
    Returns:
        UserPublic model
        
    Raises:
        HTTPException: If user not found
    """
    user = AuthService.get_user_by_id(user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if current user is superuser or requesting their own info
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user"
        )
    
    return user


@router.patch("/users/{user_id}", response_model=UserPublic, status_code=status.HTTP_200_OK)
async def update_user(
    user_id: int,
    update_data: dict,
    current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Update user information.
    
    Args:
        user_id: ID of the user to update
        update_data: Dictionary with fields to update
        current_user: Authenticated user from dependency injection
        
    Returns:
        Updated UserPublic model
        
    Raises:
        HTTPException: If user not found or not authorized
    """
    # Check if user exists
    user = AuthService.get_user_by_id(user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check authorization
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    # Prevent updating to superuser unless current user is superuser
    if 'is_superuser' in update_data and update_data['is_superuser'] is True:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superusers can grant superuser privileges"
            )
    
    updated_user = AuthService.update_user(user_id, update_data)
    
    if updated_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return updated_user


@router.post("/users/{user_id}/change-password", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def change_password(
    user_id: int,
    data: dict,
    current_user: UserPublic = Depends(get_current_active_user)
):
    """
    Change a user's password.
    
    Args:
        user_id: ID of the user to change password for
        data: Dictionary with current_password and new_password
        current_user: Authenticated user from dependency injection
        
    Returns:
        MessageResponse with success message
        
    Raises:
        HTTPException: If not authorized or password change fails
    """
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    
    if current_password is None or new_password is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both current_password and new_password are required"
        )
    
    # Check authorization
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to change this user's password"
        )
    
    success = AuthService.change_password(user_id, current_password, new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password change failed. Current password may be incorrect."
        )
    
    return MessageResponse(message="Password changed successfully")


@router.delete("/users/{user_id}", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: int,
    current_user: UserPublic = Depends(get_current_superuser)
):
    """
    Delete a user (requires superuser privileges).
    
    Args:
        user_id: ID of the user to delete
        current_user: Superuser from dependency injection
        
    Returns:
        MessageResponse with success message
        
    Raises:
        HTTPException: If user not found or cannot delete self
    """
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Deactivate user instead of deleting (soft delete)
    success = AuthService.deactivate_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return MessageResponse(message="User deactivated successfully")


@router.post("/cleanup", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def cleanup_expired(
    current_user: UserPublic = Depends(get_current_superuser)
):
    """
    Cleanup expired tokens and sessions (requires superuser privileges).
    
    Args:
        current_user: Superuser from dependency injection
        
    Returns:
        MessageResponse with cleanup statistics
    """
    stats = AuthService.cleanup_expired()
    
    message = f"Cleaned up {stats['blacklisted_tokens_deleted']} expired tokens and {stats['sessions_deleted']} expired sessions"
    
    return MessageResponse(message=message, detail=str(stats))


# Router for protected endpoints
protected_router = APIRouter(prefix="/api/protected", tags=["Protected"])


@protected_router.get("/", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def protected_endpoint(
    current_user: UserPublic = Depends(get_current_user)
):
    """
    Example protected endpoint that requires authentication.
    
    Args:
        current_user: User from dependency injection
        
    Returns:
        MessageResponse with welcome message
    """
    return MessageResponse(
        message=f"Hello, {current_user.username}! You are authenticated.",
        detail=f"User ID: {current_user.id}, Email: {current_user.email}"
    )


@protected_router.get("/admin", response_model=MessageResponse, status_code=status.HTTP_200_OK)
async def admin_endpoint(
    current_user: UserPublic = Depends(get_current_superuser)
):
    """
    Example admin endpoint that requires superuser privileges.
    
    Args:
        current_user: Superuser from dependency injection
        
    Returns:
        MessageResponse with admin message
    """
    return MessageResponse(
        message=f"Hello, {current_user.username}! You are a superuser.",
        detail="Welcome to the admin area"
    )
