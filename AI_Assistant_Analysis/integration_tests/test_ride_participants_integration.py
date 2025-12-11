"""
Integration tests for GET /rides/{ride_id}/participants endpoint
Tests retrieving participant list with user information
"""
import pytest
from datetime import datetime, timezone, timedelta


class TestRideParticipantsEndpoint:
    """Test GET /rides/{ride_id}/participants endpoint"""
    
    def test_get_participants_empty_list(self, client, auth_headers):
        """Test getting participants for a ride with no participants"""
        # Create a ride
        ride_data = {
            "title": "Empty Ride",
            "description": "No participants yet",
            "start_time": (datetime.now() + timedelta(hours=2)).isoformat()
        }
        ride_response = client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_id = ride_response.json()["id"]
        
        # Get participants
        response = client.get(f"/rides/{ride_id}/participants")
        
        assert response.status_code == 200
        data = response.json()
        assert data == []
    
    def test_get_participants_single_user(self, client, auth_headers):
        """Test getting participants when one user has joined"""
        # Create a ride
        ride_data = {
            "title": "Single Participant Ride",
            "description": "One person joining",
            "start_time": (datetime.now() + timedelta(hours=2)).isoformat()
        }
        ride_response = client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_code = ride_response.json()["code"]
        ride_id = ride_response.json()["id"]
        
        # Join the ride
        participation_data = {"ride_code": ride_code}
        client.post("/participations/", json=participation_data, headers=auth_headers)
        
        # Get participants
        response = client.get(f"/rides/{ride_id}/participants")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        
        participant = data[0]
        assert "id" in participant
        assert "user_id" in participant
        assert "username" in participant
        assert "joined_at" in participant
        assert participant["latitude"] is None
        assert participant["longitude"] is None
        assert participant["location_timestamp"] is None
    
    def test_get_participants_multiple_users(self, client, auth_headers, second_user_headers):
        """Test getting participants when multiple users have joined"""
        # Create a ride
        ride_data = {
            "title": "Multi Participant Ride",
            "description": "Multiple people joining",
            "start_time": (datetime.now() + timedelta(hours=3)).isoformat()
        }
        ride_response = client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_code = ride_response.json()["code"]
        ride_id = ride_response.json()["id"]
        
        # Both users join
        participation_data = {"ride_code": ride_code}
        client.post("/participations/", json=participation_data, headers=auth_headers)
        client.post("/participations/", json=participation_data, headers=second_user_headers)
        
        # Get participants
        response = client.get(f"/rides/{ride_id}/participants")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Check both participants have usernames
        usernames = [p["username"] for p in data]
        assert len(usernames) == 2
        assert all(isinstance(username, str) for username in usernames)
    
    def test_get_participants_with_location_data(self, client, auth_headers):
        """Test getting participants with GPS location data"""
        # Create ride and join
        ride_data = {
            "title": "Location Test Ride",
            "description": "Test with GPS",
            "start_time": (datetime.now() + timedelta(hours=2)).isoformat()
        }
        ride_response = client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_code = ride_response.json()["code"]
        ride_id = ride_response.json()["id"]
        
        participation_data = {"ride_code": ride_code}
        participation_response = client.post("/participations/", json=participation_data, headers=auth_headers)
        participation_id = participation_response.json()["id"]
        
        # Update location
        location_data = {
            "latitude": 55.7558,
            "longitude": 37.6173,
            "location_timestamp": (datetime.now(timezone.utc) - timedelta(seconds=30)).isoformat()
        }
        client.put(f"/participations/{participation_id}", json=location_data, headers=auth_headers)
        
        # Get participants
        response = client.get(f"/rides/{ride_id}/participants")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        
        participant = data[0]
        assert participant["latitude"] == 55.7558
        assert participant["longitude"] == 37.6173
        assert participant["location_timestamp"] is not None
    
    def test_get_participants_includes_username(self, client, auth_headers):
        """Test that participant response includes username from user table"""
        # Create ride
        ride_data = {
            "title": "Username Test Ride",
            "description": "Test username inclusion",
            "start_time": (datetime.now() + timedelta(hours=2)).isoformat()
        }
        ride_response = client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_code = ride_response.json()["code"]
        ride_id = ride_response.json()["id"]
        
        # Join ride
        participation_data = {"ride_code": ride_code}
        client.post("/participations/", json=participation_data, headers=auth_headers)
        
        # Get current user info
        user_response = client.get("/auth/me", headers=auth_headers)
        current_username = user_response.json()["username"]
        
        # Get participants
        response = client.get(f"/rides/{ride_id}/participants")
        
        assert response.status_code == 200
        data = response.json()
        participant = data[0]
        assert participant["username"] == current_username
    
    def test_get_participants_nonexistent_ride(self, client):
        """Test getting participants for a ride that doesn't exist"""
        response = client.get("/rides/99999/participants")
        
        assert response.status_code == 200
        data = response.json()
        assert data == []
    
    def test_get_participants_invalid_ride_id(self, client):
        """Test getting participants with invalid ride ID format"""
        response = client.get("/rides/invalid/participants")
        
        assert response.status_code == 422
    
    def test_get_participants_field_types(self, client, auth_headers):
        """Test that all fields have correct types in response"""
        # Create ride and join
        ride_data = {
            "title": "Field Type Test",
            "description": "Test field types",
            "start_time": (datetime.now() + timedelta(hours=2)).isoformat()
        }
        ride_response = client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_code = ride_response.json()["code"]
        ride_id = ride_response.json()["id"]
        
        participation_data = {"ride_code": ride_code}
        participation_response = client.post("/participations/", json=participation_data, headers=auth_headers)
        participation_id = participation_response.json()["id"]
        
        # Update with location
        location_data = {
            "latitude": 48.1351,
            "longitude": 11.5820,
            "location_timestamp": datetime.now(timezone.utc).isoformat()
        }
        client.put(f"/participations/{participation_id}", json=location_data, headers=auth_headers)
        
        # Get participants
        response = client.get(f"/rides/{ride_id}/participants")
        
        assert response.status_code == 200
        participant = response.json()[0]
        
        # Verify types
        assert isinstance(participant["id"], int)
        assert isinstance(participant["user_id"], int)
        assert isinstance(participant["username"], str)
        assert isinstance(participant["joined_at"], str)  # ISO datetime string
        assert isinstance(participant["latitude"], float)
        assert isinstance(participant["longitude"], float)
        assert isinstance(participant["location_timestamp"], str)  # ISO datetime string
    
    def test_get_participants_joined_at_timestamp(self, client, auth_headers):
        """Test that joined_at field contains valid timestamp"""
        # Create ride and join
        ride_data = {
            "title": "Timestamp Test",
            "description": "Test joined_at",
            "start_time": (datetime.now() + timedelta(hours=2)).isoformat()
        }
        ride_response = client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_code = ride_response.json()["code"]
        ride_id = ride_response.json()["id"]
        
        participation_data = {"ride_code": ride_code}
        client.post("/participations/", json=participation_data, headers=auth_headers)
        
        # Get participants
        response = client.get(f"/rides/{ride_id}/participants")
        
        participant = response.json()[0]
        
        # Verify joined_at is a valid ISO datetime
        joined_at = participant["joined_at"]
        assert "T" in joined_at
        # Should be parseable as datetime
        datetime.fromisoformat(joined_at.replace("+00:00", "+00:00"))
