"""
Password hashing utilities using passlib
"""
from passlib.context import CryptContext
from passlib.hash import pbkdf2_sha256
import bcrypt

# Configuration for password hashing
# Using bcrypt as the default algorithm
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated=["auto"],
    bcrypt__rounds=12,
)


def get_password_hash(password: str) -> str:
    """
    Hash a password for storing in the database.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        The hashed password as a string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against the hashed version.
    
    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password from the database
        
    Returns:
        True if the password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def check_password_strength(password: str) -> dict:
    """
    Check password strength and return validation result.
    
    Args:
        password: The password to check
        
    Returns:
        Dictionary with validation results
    """
    result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'score': 0
    }
    
    # Check minimum length
    if len(password) < 8:
        result['valid'] = False
        result['errors'].append('Password must be at least 8 characters long')
    else:
        result['score'] += 1
    
    # Check maximum length
    if len(password) > 100:
        result['valid'] = False
        result['errors'].append('Password must be less than 100 characters')
    
    # Check for uppercase
    if not any(c.isupper() for c in password):
        result['warnings'].append('Consider adding uppercase letters')
    else:
        result['score'] += 1
    
    # Check for lowercase
    if not any(c.islower() for c in password):
        result['warnings'].append('Consider adding lowercase letters')
    else:
        result['score'] += 1
    
    # Check for digits
    if not any(c.isdigit() for c in password):
        result['warnings'].append('Consider adding numbers')
    else:
        result['score'] += 1
    
    # Check for special characters
    if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?~' for c in password):
        result['warnings'].append('Consider adding special characters')
    else:
        result['score'] += 1
    
    # Check for common patterns (simple check)
    common_passwords = ['password', '123456', 'qwerty', 'letmein', 'welcome']
    if password.lower() in common_passwords:
        result['valid'] = False
        result['errors'].append('Password is too common')
    
    # Check for username-like patterns (if username is provided in the future)
    # This is a placeholder for future enhancement
    
    return result


def needs_rehash(hashed_password: str) -> bool:
    """
    Check if a password needs to be rehashed (e.g., if the algorithm is outdated).
    
    Args:
        hashed_password: The hashed password to check
        
    Returns:
        True if the password should be rehashed, False otherwise
    """
    return pwd_context.needs_update(hashed_password)


def rehash_password(plain_password: str, old_hashed_password: str) -> str:
    """
    Rehash a password if needed.
    
    Args:
        plain_password: The plain text password
        old_hashed_password: The old hashed password
        
    Returns:
        The new hashed password if rehashing was needed, otherwise the old one
    """
    if needs_rehash(old_hashed_password):
        return get_password_hash(plain_password)
    return old_hashed_password
