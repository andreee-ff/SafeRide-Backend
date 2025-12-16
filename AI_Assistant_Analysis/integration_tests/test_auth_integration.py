"""
Integration tests for Authentication endpoints
Tests real database operations and JWT token generation
"""
import pytest

@pytest.mark.asyncio
class TestAuthEndpoints:
    """Test authentication with real database"""
    
    async def test_login_success(self, client):
        """Test successful login with correct credentials"""
        # Create user
        user_data = {
            "username": "loginuser",
            "password": "mypassword123"
        }
        await client.post("/users/", json=user_data)
        
        # Login
        login_data = {
            "username": "loginuser",
            "password": "mypassword123"
        }
        
        response = await client.post("/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
    
    async def test_login_wrong_password(self, client):
        """Test login with incorrect password"""
        # Create user
        user_data = {
            "username": "wrongpass",
            "password": "correctpass"
        }
        await client.post("/users/", json=user_data)
        
        # Try login with wrong password
        login_data = {
            "username": "wrongpass",
            "password": "wrongpassword"
        }
        
        response = await client.post("/auth/login", data=login_data)
        assert response.status_code == 401
    
    async def test_login_nonexistent_user(self, client):
        """Test login with username that doesn't exist"""
        login_data = {
            "username": "nonexistent",
            "password": "anypass"
        }
        
        response = await client.post("/auth/login", data=login_data)
        assert response.status_code == 401
    
    async def test_get_current_user(self, client, auth_headers):
        """Test getting current user profile with valid token"""
        response = await client.get("/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert "id" in data
    
    async def test_get_current_user_no_token(self, client):
        """Test getting current user without authentication"""
        response = await client.get("/auth/me")
        assert response.status_code == 401
    
    async def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalidtoken123"}
        response = await client.get("/auth/me", headers=headers)
        assert response.status_code == 401
