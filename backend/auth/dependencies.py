"""
FastAPI dependencies for authentication
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Callable
import jwt
from jwt import PyJWTError
from functools import wraps

from .config import Settings, get_settings, settings
from .models import UserPublic, TokenData
from .service import AuthService


# Security scheme for Bearer token
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserPublic:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        UserPublic model
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    # Remove "Bearer " prefix if present
    if token.startswith("Bearer "):
        token = token[7:]
    
    user = AuthService.verify_access_token(token)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: UserPublic = Depends(get_current_user)
) -> UserPublic:
    """
    Dependency to ensure current user is active.
    
    Args:
        current_user: User from get_current_user dependency
        
    Returns:
        UserPublic model
        
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return current_user


async def get_current_superuser(
    current_user: UserPublic = Depends(get_current_active_user)
) -> UserPublic:
    """
    Dependency to ensure current user is a superuser.
    
    Args:
        current_user: User from get_current_active_user dependency
        
    Returns:
        UserPublic model
        
    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires superuser privileges"
        )
    
    return current_user


async def get_optional_user(
    request: Request
) -> Optional[UserPublic]:
    """
    Dependency to get the current user if authenticated, None otherwise.
    
    Args:
        request: FastAPI request
        
    Returns:
        UserPublic if authenticated, None otherwise
    """
    auth_header = request.headers.get("Authorization")
    
    if auth_header is None:
        return None
    
    # Remove "Bearer " prefix
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    else:
        return None
    
    user = AuthService.verify_access_token(token)
    
    if user is None:
        return None
    
    return user


def requires_auth(func: Callable) -> Callable:
    """
    Decorator to require authentication for a route.
    
    Args:
        func: Route function to protect
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get('request') or args[0]
        
        auth_header = request.headers.get("Authorization")
        
        if auth_header is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Remove "Bearer " prefix
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication header",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = AuthService.verify_access_token(token)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        kwargs['current_user'] = user
        return await func(*args, **kwargs)
    
    return wrapper


def requires_superuser(func: Callable) -> Callable:
    """
    Decorator to require superuser privileges.
    
    Args:
        func: Route function to protect
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get('request') or args[0]
        
        auth_header = request.headers.get("Authorization")
        
        if auth_header is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Remove "Bearer " prefix
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication header",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = AuthService.verify_access_token(token)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        if not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation requires superuser privileges"
            )
        
        kwargs['current_user'] = user
        return await func(*args, **kwargs)
    
    return wrapper
