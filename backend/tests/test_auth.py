"""
Tests for authentication service
"""
import pytest
from fastapi.testclient import TestClient
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.main import app
from backend.auth.database import UserRepository, init_db, reset_db
from backend.auth.hash import get_password_hash, verify_password

# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Reset database before and after each test"""
    reset_db()
    yield
    reset_db()


class TestPasswordHashing:
    """Test password hashing utilities"""
    
    def test_password_hashing(self):
        """Test that password hashing works correctly"""
        password = "my_secure_password123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)
    
    def test_different_passwords_have_different_hashes(self):
        """Test that different passwords produce different hashes"""
        password1 = "password1"
        password2 = "password2"
        
        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)
        
        assert hash1 != hash2


class TestUserRegistration:
    """Test user registration"""
    
    def test_register_new_user(self):
        """Test registering a new user"""
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "password" not in data
        assert "id" in data
    
    def test_register_duplicate_username(self):
        """Test that duplicate username is rejected"""
        # First registration
        client.post("/api/auth/register", json={
            "username": "duplicate_user",
            "email": "first@example.com",
            "password": "password123"
        })
        
        # Second registration with same username
        response = client.post("/api/auth/register", json={
            "username": "duplicate_user",
            "email": "second@example.com",
            "password": "password456"
        })
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_register_duplicate_email(self):
        """Test that duplicate email is rejected"""
        # First registration
        client.post("/api/auth/register", json={
            "username": "user1",
            "email": "duplicate@example.com",
            "password": "password123"
        })
        
        # Second registration with same email
        response = client.post("/api/auth/register", json={
            "username": "user2",
            "email": "duplicate@example.com",
            "password": "password456"
        })
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_register_with_invalid_password(self):
        """Test registration with too short password"""
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "short"
        })
        
        assert response.status_code == 422  # Validation error


class TestUserLogin:
    """Test user login"""
    
    def test_login_success(self):
        """Test successful login"""
        # First register a user
        client.post("/api/auth/register", json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "loginpassword123"
        })
        
        # Then login
        response = client.post("/api/auth/login", data={
            "username": "loginuser",
            "password": "loginpassword123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["token"]
        assert data["token"]["token_type"] == "bearer"
        assert data["user"]["username"] == "loginuser"
    
    def test_login_with_json(self):
        """Test login with JSON body"""
        # First register a user
        client.post("/api/auth/register", json={
            "username": "jsonloginuser",
            "email": "jsonlogin@example.com",
            "password": "jsonpassword123"
        })
        
        # Then login with JSON
        response = client.post("/api/auth/login/json", json={
            "username": "jsonloginuser",
            "password": "jsonpassword123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["token"]
    
    def test_login_wrong_password(self):
        """Test login with wrong password"""
        # First register a user
        client.post("/api/auth/register", json={
            "username": "wrongpassuser",
            "email": "wrongpass@example.com",
            "password": "correctpassword"
        })
        
        # Then login with wrong password
        response = client.post("/api/auth/login", data={
            "username": "wrongpassuser",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self):
        """Test login with nonexistent user"""
        response = client.post("/api/auth/login", data={
            "username": "nonexistent",
            "password": "anypassword"
        })
        
        assert response.status_code == 401


class TestProtectedEndpoints:
    """Test protected endpoints"""
    
    def test_access_protected_endpoint_without_auth(self):
        """Test accessing protected endpoint without authentication"""
        response = client.get("/api/protected/")
        
        assert response.status_code == 401
    
    def test_access_protected_endpoint_with_auth(self):
        """Test accessing protected endpoint with authentication"""
        # First register and login
        client.post("/api/auth/register", json={
            "username": "protecteduser",
            "email": "protected@example.com",
            "password": "protected123"
        })
        
        login_response = client.post("/api/auth/login", data={
            "username": "protecteduser",
            "password": "protected123"
        })
        
        token = login_response.json()["token"]["access_token"]
        
        # Then access protected endpoint
        response = client.get(
            "/api/protected/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert "protecteduser" in response.json()["message"]
    
    def test_access_admin_endpoint_without_superuser(self):
        """Test accessing admin endpoint without superuser privileges"""
        # First register and login as regular user
        client.post("/api/auth/register", json={
            "username": "regularuser",
            "email": "regular@example.com",
            "password": "regular123"
        })
        
        login_response = client.post("/api/auth/login", data={
            "username": "regularuser",
            "password": "regular123"
        })
        
        token = login_response.json()["token"]["access_token"]
        
        # Then try to access admin endpoint
        response = client.get(
            "/api/protected/admin",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403


class TestUserManagement:
    """Test user management endpoints"""
    
    def test_get_current_user(self):
        """Test getting current user information"""
        # First register and login
        client.post("/api/auth/register", json={
            "username": "meuser",
            "email": "me@example.com",
            "password": "me123"
        })
        
        login_response = client.post("/api/auth/login", data={
            "username": "meuser",
            "password": "me123"
        })
        
        token = login_response.json()["token"]["access_token"]
        
        # Then get current user
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["username"] == "meuser"
        assert response.json()["email"] == "me@example.com"
    
    def test_list_users_as_superuser(self):
        """Test listing users as superuser"""
        # First create a superuser
        # Note: In a real application, you'd need a way to create the first superuser
        # For testing, we'll manually create one in the database
        from backend.auth.hash import get_password_hash
        
        hashed_password = get_password_hash("superpassword123")
        
        # Manually insert superuser into database
        import sqlite3
        from backend.auth.database import get_db_path
        
        conn = sqlite3.connect(str(get_db_path()))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, hashed_password, is_superuser) VALUES (?, ?, ?, ?)",
            ("superuser", "super@example.com", hashed_password, True)
        )
        conn.commit()
        conn.close()
        
        # Login as superuser
        login_response = client.post("/api/auth/login", data={
            "username": "superuser",
            "password": "superpassword123"
        })
        
        token = login_response.json()["token"]["access_token"]
        
        # List users
        response = client.get(
            "/api/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert "users" in response.json()
        assert len(response.json()["users"]) >= 1


class TestLogout:
    """Test logout functionality"""
    
    def test_logout_success(self):
        """Test successful logout"""
        # First register and login
        client.post("/api/auth/register", json={
            "username": "logoutuser",
            "email": "logout@example.com",
            "password": "logout123"
        })
        
        login_response = client.post("/api/auth/login", data={
            "username": "logoutuser",
            "password": "logout123"
        })
        
        token = login_response.json()["token"]["access_token"]
        
        # Then logout
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert "logged out" in response.json()["message"]
    
    def test_logout_then_access_protected(self):
        """Test that accessing protected endpoint fails after logout"""
        # First register and login
        client.post("/api/auth/register", json={
            "username": "logouttestuser",
            "email": "logouttest@example.com",
            "password": "logouttest123"
        })
        
        login_response = client.post("/api/auth/login", data={
            "username": "logouttestuser",
            "password": "logouttest123"
        })
        
        token = login_response.json()["token"]["access_token"]
        
        # Logout
        client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Try to access protected endpoint
        response = client.get(
            "/api/protected/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # The token should now be invalid
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
