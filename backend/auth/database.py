"""
Database configuration and models for SQLite
"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import os

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "auth.db"


def get_db_path() -> Path:
    """Get or create database directory and return path"""
    db_dir = DB_PATH.parent
    if not db_dir.exists():
        db_dir.mkdir(parents=True, exist_ok=True)
    return DB_PATH


def get_connection() -> sqlite3.Connection:
    """Get a new SQLite connection"""
    conn = sqlite3.connect(str(get_db_path()), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize database tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT,
            hashed_password TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            is_superuser BOOLEAN DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT
        )
    """)
    
    # Create tokens blacklist table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blacklisted_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            expired_at TEXT NOT NULL
        )
    """)
    
    # Create sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Create indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tokens_token ON blacklisted_tokens(token)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)")
    
    conn.commit()
    conn.close()


def reset_db() -> None:
    """Reset all database tables (for development only)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS sessions")
    cursor.execute("DROP TABLE IF EXISTS blacklisted_tokens")
    cursor.execute("DROP TABLE IF EXISTS users")
    
    conn.commit()
    conn.close()
    init_db()


class UserRepository:
    """Repository for user operations"""
    
    @staticmethod
    def get_by_id(user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None
    
    @staticmethod
    def get_by_username(username: str) -> Optional[Dict]:
        """Get user by username"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None
    
    @staticmethod
    def get_by_email(email: str) -> Optional[Dict]:
        """Get user by email"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None
    
    @staticmethod
    def create(user_data: Dict) -> Dict:
        """Create a new user"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (username, email, full_name, hashed_password, is_active, is_superuser)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_data['username'],
            user_data['email'],
            user_data.get('full_name'),
            user_data['hashed_password'],
            user_data.get('is_active', True),
            user_data.get('is_superuser', False)
        ))
        
        user_id = cursor.lastrowid
        conn.commit()
        
        # Fetch the created user
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        return dict(result)
    
    @staticmethod
    def update(user_id: int, user_data: Dict) -> Optional[Dict]:
        """Update user information"""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Build update query dynamically
        set_clause = ", ".join([f"{k} = ?" for k in user_data.keys()])
        query = f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        
        values = list(user_data.values())
        values.append(user_id)
        
        cursor.execute(query, values)
        conn.commit()
        
        # Fetch updated user
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        return dict(result) if result else None
    
    @staticmethod
    def delete(user_id: int) -> bool:
        """Delete a user"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    
    @staticmethod
    def list_all(limit: int = 100, offset: int = 0) -> List[Dict]:
        """List all users with pagination"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users LIMIT ? OFFSET ?", (limit, offset))
        results = cursor.fetchall()
        conn.close()
        return [dict(row) for row in results]
    
    @staticmethod
    def count() -> int:
        """Count all users"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0


class TokenRepository:
    """Repository for token blacklist operations"""
    
    @staticmethod
    def blacklist_token(token: str, expired_at: datetime) -> bool:
        """Add token to blacklist"""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO blacklisted_tokens (token, expired_at) VALUES (?, ?)",
                (token, expired_at.isoformat())
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    @staticmethod
    def is_token_blacklisted(token: str) -> bool:
        """Check if token is blacklisted"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM blacklisted_tokens WHERE token = ?", (token,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    @staticmethod
    def cleanup_expired() -> int:
        """Remove expired tokens from blacklist"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM blacklisted_tokens WHERE expired_at < CURRENT_TIMESTAMP")
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted


class SessionRepository:
    """Repository for session management"""
    
    @staticmethod
    def create_session(user_id: int, token: str, ip_address: Optional[str], user_agent: Optional[str], expires_at: datetime) -> Dict:
        """Create a new session"""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sessions (user_id, token, ip_address, user_agent, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, token, ip_address, user_agent, expires_at.isoformat()))
        
        session_id = cursor.lastrowid
        conn.commit()
        
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        result = cursor.fetchone()
        conn.close()
        
        return dict(result)
    
    @staticmethod
    def get_session_by_token(token: str) -> Optional[Dict]:
        """Get session by token"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE token = ?", (token,))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None
    
    @staticmethod
    def delete_session(token: str) -> bool:
        """Delete a session by token"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    
    @staticmethod
    def delete_user_sessions(user_id: int) -> int:
        """Delete all sessions for a user"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted
    
    @staticmethod
    def cleanup_expired_sessions() -> int:
        """Remove expired sessions"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP")
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted


# Initialize database on module load
init_db()
