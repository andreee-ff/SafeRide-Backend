"""
Integration tests for Participation endpoints
Tests real database operations for ride participation
"""
import pytest
from datetime import datetime, timedelta

@pytest.mark.asyncio
class TestParticipationEndpoints:
    """Test participation creation, retrieval, and updates with real database"""
    
    async def test_create_participation(self, client, auth_headers, second_user_headers):
        """Test joining a ride (user 2 joins user 1's ride)"""
        # Create a ride first (User 1)
        ride_data = {
            "title": "Test Ride",
            "description": "Ride for participation test",
            "start_time": (datetime.now() + timedelta(hours=2)).isoformat()
        }
        
        ride_response = await client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_code = ride_response.json()["code"]
        
        # Create participation (User 2)
        participation_data = {
            "ride_code": ride_code
        }
        
        # User 2 joins
        response = await client.post("/participations/", json=participation_data, headers=second_user_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert "ride_id" in data
        assert "id" in data
        assert "user_id" in data
    
    async def test_create_participation_unauthorized(self, client, auth_headers):
        """Test creating participation without authentication"""
        # Create a ride
        ride_data = {
            "title": "Test Ride",
            "description": "Test",
            "start_time": datetime.now().isoformat()
        }
        
        ride_response = await client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_code = ride_response.json()["code"]
        
        # Try to participate without auth
        participation_data = {"ride_code": ride_code}
        response = await client.post("/participations/", json=participation_data)
        
        assert response.status_code == 401
    
    async def test_create_participation_nonexistent_ride(self, client, auth_headers):
        """Test joining a ride that doesn't exist"""
        participation_data = {"ride_code": "NOCODE"}
        
        response = await client.post("/participations/", json=participation_data, headers=auth_headers)
        assert response.status_code == 404
    
    async def test_get_all_participations(self, client, auth_headers, second_user_headers):
        """Test retrieving all participations"""
        # Create a ride
        ride_data = {
            "title": "Popular Ride",
            "description": "Many people joining",
            "start_time": (datetime.now() + timedelta(hours=4)).isoformat()
        }
        
        ride_response = await client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_code = ride_response.json()["code"]
        ride_id = ride_response.json()["id"]
        
        # Multiple users join
        participation_data = {"ride_code": ride_code}
        
        # User 1 (creator) already joined.
        # User 2 joins.
        response2 = await client.post("/participations/", json=participation_data, headers=second_user_headers)
        assert response2.status_code == 201
        
        # Get all participations
        response = await client.get("/participations/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        ride_ids = [p["ride_id"] for p in data]
        assert ride_id in ride_ids
    
    async def test_get_participation_by_id(self, client, auth_headers, second_user_headers):
        """Test retrieving participation by ID"""
        # Create ride and participation
        ride_data = {
            "title": "Single Participation Ride",
            "description": "Test",
            "start_time": (datetime.now() + timedelta(hours=1)).isoformat()
        }
        
        ride_response = await client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_code = ride_response.json()["code"]
        
        participation_data = {"ride_code": ride_code}
        participation_response = await client.post("/participations/", json=participation_data, headers=second_user_headers)
        participation_id = participation_response.json()["id"]
        
        # Get participation by ID
        response = await client.get(f"/participations/{participation_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == participation_id
    
    async def test_get_nonexistent_participation(self, client):
        """Test getting participation that doesn't exist"""
        response = await client.get("/participations/99999")
        assert response.status_code == 404
    
    async def test_update_participation_location(self, client, auth_headers, second_user_headers):
        """Test updating participation location"""
        # Create ride and participation
        ride_data = {
            "title": "Location Update Ride",
            "description": "Test location change",
            "start_time": (datetime.now() + timedelta(hours=3)).isoformat()
        }
        
        ride_response = await client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_code = ride_response.json()["code"]
        
        participation_data = {"ride_code": ride_code}
        participation_response = await client.post("/participations/", json=participation_data, headers=second_user_headers)
        participation_id = participation_response.json()["id"]
        
        # Update location
        update_data = {
            "latitude": 55.7558,
            "longitude": 37.6173,
            "location_timestamp": (datetime.now() - timedelta(seconds=10)).isoformat()
        }
        response = await client.put(f"/participations/{participation_id}", json=update_data, headers=second_user_headers)
        
        assert response.status_code == 200, f"Response: {response.status_code}, Body: {response.text}"
        data = response.json()
        assert data["latitude"] == 55.7558
        assert data["longitude"] == 37.6173
    
    async def test_update_participation_unauthorized(self, client, auth_headers):
        """Test updating participation without authentication"""
        # Create ride and participation
        ride_data = {
            "title": "Auth Test Ride",
            "description": "Test",
            "start_time": datetime.now().isoformat()
        }
        
        ride_response = await client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_code = ride_response.json()["code"]
        
        participation_data = {"ride_code": ride_code}
        
        # Creator is already joined, get their participation ID
        participants_resp = await client.get(f"/rides/{ride_response.json()['id']}/participants")
        participation_id = participants_resp.json()[0]["id"]
        
        # Try to update without auth
        update_data = {
            "latitude": 55.0,
            "longitude": 37.0,
            "location_timestamp": datetime.now().isoformat()
        }
        response = await client.put(f"/participations/{participation_id}", json=update_data)
        
        assert response.status_code == 401
    
    async def test_update_nonexistent_participation(self, client, auth_headers):
        """Test updating participation that doesn't exist"""
        update_data = {
            "latitude": 55.0,
            "longitude": 37.0,
            "location_timestamp": (datetime.now() - timedelta(seconds=10)).isoformat()
        }
        response = await client.put("/participations/99999", json=update_data, headers=auth_headers)
        
        assert response.status_code == 404
    
    async def test_multiple_users_same_ride(self, client, auth_headers, second_user_headers):
        """Test that multiple users can join the same ride"""
        # Create ride
        ride_data = {
            "title": "Carpool Ride",
            "description": "Multiple seats available",
            "start_time": (datetime.now() + timedelta(hours=5)).isoformat()
        }
        
        ride_response = await client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_code = ride_response.json()["code"]
        ride_id = ride_response.json()["id"]
        
        # User 1 (Creator) joins automatically
        user1_participation_id = (await client.get(f"/rides/{ride_id}/participants")).json()[0]["id"]
        
        # User 2 joins same ride
        participation_data = {"ride_code": ride_code}
        response2 = await client.post("/participations/", json=participation_data, headers=second_user_headers)
        assert response2.status_code == 201
        user2_participation_id = response2.json()["id"]
        
        # Verify both participations exist and are different
        assert user1_participation_id != user2_participation_id
        
        get_response = await client.get("/participations/")
        participations = get_response.json()
        ride_participations = [p for p in participations if p["ride_id"] == ride_id]
        assert len(ride_participations) >= 2
