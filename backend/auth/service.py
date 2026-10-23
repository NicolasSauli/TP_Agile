"""
Authentication service - Business logic for user authentication
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
from jwt import PyJWTError
import uuid

from .models import (
    UserCreate, UserPublic, UserInDB, Token, TokenData,
    LoginRequest, LoginResponse, MessageResponse
)
from .database import UserRepository, TokenRepository, SessionRepository
from .hash import get_password_hash, verify_password
from .config import get_settings


class AuthService:
    """Service for handling authentication business logic"""
    
    @staticmethod
    def create_user(user_data: UserCreate) -> UserPublic:
        """
        Create a new user in the database.
        
        Args:
            user_data: UserCreate model with username, email, password, etc.
            
        Returns:
            UserPublic model with user information (no password)
            
        Raises:
            ValueError: If username or email already exists
        """
        # Check if username already exists
        if UserRepository.get_by_username(user_data.username):
            raise ValueError(f"Username '{user_data.username}' already exists")
        
        # Check if email already exists
        if UserRepository.get_by_email(user_data.email):
            raise ValueError(f"Email '{user_data.email}' already registered")
        
        # Hash the password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user dictionary
        user_dict = {
            'username': user_data.username,
            'email': user_data.email,
            'full_name': user_data.full_name,
            'hashed_password': hashed_password,
            'is_active': True,
            'is_superuser': False
        }
        
        # Create user in database
        created_user = UserRepository.create(user_dict)
        
        # Convert to UserPublic model
        return UserPublic(
            id=created_user['id'],
            username=created_user['username'],
            email=created_user['email'],
            full_name=created_user['full_name'],
            is_active=bool(created_user['is_active']),
            is_superuser=bool(created_user['is_superuser']),
            created_at=datetime.fromisoformat(created_user['created_at'])
        )
    
    @staticmethod
    def authenticate_user(login_data: LoginRequest) -> Optional[UserInDB]:
        """
        Authenticate a user with username and password.
        
        Args:
            login_data: LoginRequest with username and password
            
        Returns:
            UserInDB if authentication successful, None otherwise
        """
        user = UserRepository.get_by_username(login_data.username)
        
        if user is None:
            return None
        
        # Convert user dict to UserInDB
        user_in_db = UserInDB(
            id=user['id'],
            username=user['username'],
            email=user['email'],
            full_name=user['full_name'],
            is_active=bool(user['is_active']),
            is_superuser=bool(user['is_superuser']),
            hashed_password=user['hashed_password'],
            created_at=datetime.fromisoformat(user['created_at']),
            updated_at=datetime.fromisoformat(user['updated_at']) if user['updated_at'] else None
        )
        
        # Verify password
        if not verify_password(login_data.password, user_in_db.hashed_password):
            return None
        
        # Check if user is active
        if not user_in_db.is_active:
            return None
        
        return user_in_db
    
    @staticmethod
    def create_access_token(user: UserInDB, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token for the user.
        
        Args:
            user: UserInDB model
            expires_delta: Optional timedelta for token expiration
            
        Returns:
            JWT token as string
        """
        settings = get_settings()
        
        if expires_delta is None:
            expires_delta = timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        expire = datetime.utcnow() + expires_delta
        
        # Create token payload
        token_data = TokenData(
            username=user.username,
            user_id=user.id,
            email=user.email
        )
        
        # Add expiration to payload
        payload = token_data.dict()
        payload['exp'] = expire
        payload['iat'] = datetime.utcnow()
        payload['jti'] = str(uuid.uuid4())  # Unique token identifier
        payload['type'] = 'access'
        
        # Generate JWT token
        token = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return token
    
    @staticmethod
    def create_refresh_token(user: UserInDB, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT refresh token for the user.
        
        Args:
            user: UserInDB model
            expires_delta: Optional timedelta for token expiration
            
        Returns:
            JWT token as string
        """
        settings = get_settings()
        
        if expires_delta is None:
            expires_delta = timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
        
        expire = datetime.utcnow() + expires_delta
        
        # Create token payload
        token_data = TokenData(
            username=user.username,
            user_id=user.id,
            email=user.email
        )
        
        # Add expiration to payload
        payload = token_data.dict()
        payload['exp'] = expire
        payload['iat'] = datetime.utcnow()
        payload['jti'] = str(uuid.uuid4())
        payload['type'] = 'refresh'
        
        # Generate JWT token
        token = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        return token
    
    @staticmethod
    def decode_token(token: str) -> Optional[TokenData]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            TokenData if valid, None otherwise
        """
        settings = get_settings()
        
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            # Check if token is blacklisted
            if TokenRepository.is_token_blacklisted(token):
                return None
            
            # Create TokenData from payload
            token_data = TokenData(
                username=payload.get('username'),
                user_id=payload.get('user_id'),
                email=payload.get('email')
            )
            
            return token_data
            
        except PyJWTError as e:
            print(f"Token decode error: {e}")
            return None
    
    @staticmethod
    def verify_access_token(token: str) -> Optional[UserPublic]:
        """
        Verify an access token and return the user if valid.
        
        Args:
            token: JWT access token
            
        Returns:
            UserPublic if token is valid, None otherwise
        """
        token_data = AuthService.decode_token(token)
        
        if token_data is None:
            return None
        
        # Get user from database
        user = UserRepository.get_by_id(token_data.user_id)
        
        if user is None:
            return None
        
        # Check if user is active
        if not user['is_active']:
            return None
        
        # Convert to UserPublic
        return UserPublic(
            id=user['id'],
            username=user['username'],
            email=user['email'],
            full_name=user['full_name'],
            is_active=bool(user['is_active']),
            is_superuser=bool(user['is_superuser']),
            created_at=datetime.fromisoformat(user['created_at'])
        )
    
    @staticmethod
    def login(login_data: LoginRequest, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Optional[LoginResponse]:
        """
        Authenticate user and create session with tokens.
        
        Args:
            login_data: LoginRequest with username and password
            ip_address: Optional IP address of the client
            user_agent: Optional user agent string
            
        Returns:
            LoginResponse with user and tokens, or None if authentication failed
        """
        # Authenticate user
        user = AuthService.authenticate_user(login_data)
        
        if user is None:
            return None
        
        # Create tokens
        access_token = AuthService.create_access_token(user)
        refresh_token = AuthService.create_refresh_token(user)
        
        # Create session
        settings = get_settings()
        expires_at = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
        SessionRepository.create_session(
            user_id=user.id,
            token=access_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at
        )
        
        # Create UserPublic from UserInDB
        user_public = UserPublic(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at
        )
        
        # Create response
        return LoginResponse(
            user=user_public,
            token=Token(access_token=access_token, token_type="bearer")
        )
    
    @staticmethod
    def logout(token: str) -> bool:
        """
        Invalidate a user session and blacklist the token.
        
        Args:
            token: JWT token to invalidate
            
        Returns:
            True if logout successful, False otherwise
        """
        settings = get_settings()
        
        # Get token expiration
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                options={'verify_exp': False}  # Don't verify expiration yet
            )
            expire = datetime.fromtimestamp(payload['exp'])
        except PyJWTError:
            return False
        
        # Blacklist the token
        TokenRepository.blacklist_token(token, expire)
        
        # Delete the session
        SessionRepository.delete_session(token)
        
        return True
    
    @staticmethod
    def refresh_token(refresh_token: str) -> Optional[str]:
        """
        Refresh an access token using a refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token if refresh successful, None otherwise
        """
        token_data = AuthService.decode_token(refresh_token)
        
        if token_data is None:
            return None
        
        # Get user from database
        user = UserRepository.get_by_id(token_data.user_id)
        
        if user is None or not user['is_active']:
            return None
        
        # Convert to UserInDB
        user_in_db = UserInDB(
            id=user['id'],
            username=user['username'],
            email=user['email'],
            full_name=user['full_name'],
            is_active=bool(user['is_active']),
            is_superuser=bool(user['is_superuser']),
            hashed_password=user['hashed_password'],
            created_at=datetime.fromisoformat(user['created_at']),
            updated_at=datetime.fromisoformat(user['updated_at']) if user['updated_at'] else None
        )
        
        # Create new access token
        return AuthService.create_access_token(user_in_db)
    
    @staticmethod
    def get_current_user(token: str) -> Optional[UserPublic]:
        """
        Get the current user from a JWT token.
        
        Args:
            token: JWT access token
            
        Returns:
            UserPublic if token is valid, None otherwise
        """
        return AuthService.verify_access_token(token)
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[UserPublic]:
        """
        Get a user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            UserPublic if user exists, None otherwise
        """
        user = UserRepository.get_by_id(user_id)
        
        if user is None:
            return None
        
        return UserPublic(
            id=user['id'],
            username=user['username'],
            email=user['email'],
            full_name=user['full_name'],
            is_active=bool(user['is_active']),
            is_superuser=bool(user['is_superuser']),
            created_at=datetime.fromisoformat(user['created_at'])
        )
    
    @staticmethod
    def list_users(limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        List all users with pagination.
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            Dictionary with users list and total count
        """
        users = UserRepository.list_all(limit, offset)
        total = UserRepository.count()
        
        user_publics = [
            UserPublic(
                id=user['id'],
                username=user['username'],
                email=user['email'],
                full_name=user['full_name'],
                is_active=bool(user['is_active']),
                is_superuser=bool(user['is_superuser']),
                created_at=datetime.fromisoformat(user['created_at'])
            )
            for user in users
        ]
        
        return {
            'users': user_publics,
            'total': total,
            'limit': limit,
            'offset': offset
        }
    
    @staticmethod
    def update_user(user_id: int, update_data: Dict[str, Any]) -> Optional[UserPublic]:
        """
        Update user information.
        
        Args:
            user_id: User ID to update
            update_data: Dictionary with fields to update
            
        Returns:
            Updated UserPublic, or None if user not found
        """
        # Remove password from update data (use separate method for password change)
        update_data.pop('password', None)
        update_data.pop('hashed_password', None)
        
        user = UserRepository.update(user_id, update_data)
        
        if user is None:
            return None
        
        return UserPublic(
            id=user['id'],
            username=user['username'],
            email=user['email'],
            full_name=user['full_name'],
            is_active=bool(user['is_active']),
            is_superuser=bool(user['is_superuser']),
            created_at=datetime.fromisoformat(user['created_at'])
        )
    
    @staticmethod
    def change_password(user_id: int, current_password: str, new_password: str) -> bool:
        """
        Change a user's password.
        
        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            True if password changed successfully, False otherwise
        """
        user = UserRepository.get_by_id(user_id)
        
        if user is None:
            return False
        
        # Verify current password
        if not verify_password(current_password, user['hashed_password']):
            return False
        
        # Hash new password
        new_hashed_password = get_password_hash(new_password)
        
        # Update password
        update_data = {'hashed_password': new_hashed_password}
        UserRepository.update(user_id, update_data)
        
        # Invalidate all user sessions
        SessionRepository.delete_user_sessions(user_id)
        
        return True
    
    @staticmethod
    def deactivate_user(user_id: int) -> bool:
        """
        Deactivate a user account.
        
        Args:
            user_id: User ID to deactivate
            
        Returns:
            True if user deactivated, False if not found
        """
        update_data = {'is_active': False}
        user = UserRepository.update(user_id, update_data)
        
        if user is None:
            return False
        
        # Invalidate all user sessions
        SessionRepository.delete_user_sessions(user_id)
        
        return True
    
    @staticmethod
    def cleanup_expired() -> Dict[str, int]:
        """
        Cleanup expired tokens and sessions.
        
        Returns:
            Dictionary with cleanup statistics
        """
        blacklisted_deleted = TokenRepository.cleanup_expired()
        sessions_deleted = SessionRepository.cleanup_expired_sessions()
        
        return {
            'blacklisted_tokens_deleted': blacklisted_deleted,
            'sessions_deleted': sessions_deleted
        }
