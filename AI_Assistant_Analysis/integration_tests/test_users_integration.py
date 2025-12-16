"""
Integration tests for User endpoints
Tests real database operations without mocking
"""
import pytest

@pytest.mark.asyncio
class TestUserEndpoints:
    """Test user creation and retrieval with real database"""
    
    async def test_create_user(self, client):
        """Test creating a new user in database"""
        user_data = {
            "username": "john_doe",
            "password": "securepass123"
        }
        
        response = await client.post("/users/", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "john_doe"
        assert "id" in data
        assert "password" not in data  # Password should not be returned
    
    async def test_create_duplicate_username(self, client):
        """Test that duplicate usernames are rejected"""
        user_data = {
            "username": "duplicate_user",
            "password": "pass123"
        }
        
        # Create first user
        response1 = await client.post("/users/", json=user_data)
        assert response1.status_code == 201
        
        # Try to create second user with same username
        response2 = await client.post("/users/", json=user_data)
        assert response2.status_code == 409
    
    async def test_get_user_by_id(self, client):
        """Test retrieving user by ID"""
        # Create user
        user_data = {
            "username": "jane_doe",
            "password": "pass456"
        }
        
        create_response = await client.post("/users/", json=user_data)
        user_id = create_response.json()["id"]
        
        # Get user by ID
        response = await client.get(f"/users/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["username"] == "jane_doe"
    
    async def test_get_nonexistent_user(self, client):
        """Test getting user that doesn't exist"""
        # Use await for client.get
        response = await client.get("/users/99999")
        assert response.status_code == 404
    
    async def test_get_all_users(self, client):
        """Test retrieving all users"""
        # Create multiple users
        users = [
            {"username": "user1", "password": "pass1"},
            {"username": "user2", "password": "pass2"},
            {"username": "user3", "password": "pass3"},
        ]
        
        for user in users:
            response = await client.post("/users/", json=user)
            assert response.status_code == 201
        
        # Get all users
        response = await client.get("/users/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        usernames = [u["username"] for u in data]
        assert "user1" in usernames
        assert "user2" in usernames
        assert "user3" in usernames
