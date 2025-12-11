"""
Integration tests for Ride endpoints
Tests real database operations for ride management
"""
import pytest
from datetime import datetime, timedelta


class TestRideEndpoints:
    def test_owned_rides_empty(self, client, auth_headers):
        """Test /rides/owned returns empty list if user has no rides"""
        response = client.get("/rides/owned", headers=auth_headers)
        assert response.status_code == 404 or (response.status_code == 200 and response.json() == [])

    def test_owned_rides_not_visible_to_others(self, client, auth_headers, second_user_headers):
        """Test user cannot see rides owned by another user via /rides/owned"""
        ride = {
            "title": "Private Ride",
            "description": "Should not be visible",
            "start_time": (datetime.now() + timedelta(hours=1)).isoformat()
        }
        client.post("/rides/", json=ride, headers=auth_headers)
        response = client.get("/rides/owned", headers=second_user_headers)
        assert response.status_code == 404 or (response.status_code == 200 and all(r["title"] != "Private Ride" for r in response.json()))

    def test_joined_rides_empty(self, client, second_user_headers):
        """Test /rides/joined returns empty list if user is not a participant"""
        response = client.get("/rides/joined", headers=second_user_headers)
        assert response.status_code == 404 or (response.status_code == 200 and response.json() == [])

    def test_joined_rides_only_participating(self, client, auth_headers, second_user_headers):
        """Test /rides/joined returns only rides where user is a participant"""
        # User 1 creates two rides
        ride1 = {
            "title": "Group Ride 1",
            "description": "First group",
            "start_time": (datetime.now() + timedelta(hours=1)).isoformat()
        }
        ride2 = {
            "title": "Group Ride 2",
            "description": "Second group",
            "start_time": (datetime.now() + timedelta(hours=2)).isoformat()
        }
        r1 = client.post("/rides/", json=ride1, headers=auth_headers).json()
        r2 = client.post("/rides/", json=ride2, headers=auth_headers).json()
        # User 2 joins only the first ride
        join_payload = {"ride_code": r1["code"]}
        join_response = client.post(f"/participations/", json=join_payload, headers=second_user_headers)
        assert join_response.status_code == 201

        response = client.get("/rides/joined", headers=second_user_headers)
        assert response.status_code == 200
        titles = [r["title"] for r in response.json()]
        assert "Group Ride 1" in titles
        assert "Group Ride 2" not in titles

    def test_joined_rides_after_leaving(self, client, auth_headers, second_user_headers):
        """Test /rides/joined does not return ride after user leaves participation"""
        # User 1 creates ride
        ride = {
            "title": "Leave Test Ride",
            "description": "Will leave",
            "start_time": (datetime.now() + timedelta(hours=1)).isoformat()
        }
        r = client.post("/rides/", json=ride, headers=auth_headers).json()
        # User 2 joins
        join_payload = {"ride_code": r["code"]}
        join_response = client.post(f"/participations/", json=join_payload, headers=second_user_headers)
        assert join_response.status_code == 201
        participation_id = join_response.json()["id"]

        # User 2 leaves
        leave_response = client.delete(f"/participations/{participation_id}", headers=second_user_headers)
        assert leave_response.status_code in [200, 204]
        # Check joined rides
        response = client.get("/rides/joined", headers=second_user_headers)
        assert response.status_code == 404 or (response.status_code == 200 and all(rr["title"] != "Leave Test Ride" for rr in response.json()))

    def test_owned_rides_deleted_not_returned(self, client, auth_headers):
        """Test /rides/owned does not return deleted rides"""
        ride = {
            "title": "To Delete",
            "description": "Will be deleted",
            "start_time": (datetime.now() + timedelta(hours=1)).isoformat()
        }
        r = client.post("/rides/", json=ride, headers=auth_headers).json()
        client.delete(f"/rides/{r['id']}", headers=auth_headers)
        response = client.get("/rides/owned", headers=auth_headers)
        assert response.status_code == 404 or (response.status_code == 200 and all(rr["title"] != "To Delete" for rr in response.json()))

    def test_owned_and_joined_requires_auth(self, client):
        """Test /rides/owned and /rides/joined require authentication"""
        response_owned = client.get("/rides/owned")
        response_joined = client.get("/rides/joined")
        assert response_owned.status_code == 401
        assert response_joined.status_code == 401

    def test_get_owned_rides(self, client, auth_headers, second_user_headers):
        """Test /rides/owned returns only rides created by current user"""
        # User 1 creates two rides
        ride1 = {
            "title": "User1 Ride 1",
            "description": "First ride",
            "start_time": (datetime.now() + timedelta(hours=1)).isoformat()
        }
        ride2 = {
            "title": "User1 Ride 2",
            "description": "Second ride",
            "start_time": (datetime.now() + timedelta(hours=2)).isoformat()
        }
        client.post("/rides/", json=ride1, headers=auth_headers)
        client.post("/rides/", json=ride2, headers=auth_headers)

        # User 2 creates one ride
        ride3 = {
            "title": "User2 Ride",
            "description": "Other user's ride",
            "start_time": (datetime.now() + timedelta(hours=3)).isoformat()
        }
        client.post("/rides/", json=ride3, headers=second_user_headers)

        # User 1 requests /rides/owned
        response = client.get("/rides/owned", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        titles = [r["title"] for r in data]
        assert "User1 Ride 1" in titles
        assert "User1 Ride 2" in titles
        assert "User2 Ride" not in titles

    def test_get_joined_rides(self, client, auth_headers, second_user_headers):
        """Test /rides/joined returns only rides where user is a participant"""
        # User 1 creates a ride
        ride = {
            "title": "Group Ride",
            "description": "Ride for joining",
            "start_time": (datetime.now() + timedelta(hours=1)).isoformat()
        }
        create_response = client.post("/rides/", json=ride, headers=auth_headers)
        ride_code = create_response.json()["code"]

        # User 2 joins the ride (simulate participation)
        join_payload = {"ride_code": ride_code}
        join_response = client.post(f"/participations/", json=join_payload, headers=second_user_headers)
        assert join_response.status_code in [200, 201]

        # User 2 requests /rides/joined

        response = client.get("/rides/joined", headers=second_user_headers)
        assert response.status_code == 200
        data = response.json()
        titles = [r["title"] for r in data]
        assert "Group Ride" in titles
    """Test ride creation, retrieval, update, and deletion with real database"""
    
    def test_create_ride(self, client, auth_headers):
        """Test creating a new ride"""
        ride_data = {
            "title": "Trip to Airport",
            "description": "Need a ride to the airport",
            "start_time": (datetime.now() + timedelta(hours=2)).isoformat()
        }
        
        response = client.post("/rides/", json=ride_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Trip to Airport"
        assert data["description"] == "Need a ride to the airport"
        assert "id" in data
        assert "code" in data
        assert len(data["code"]) == 6
        assert data["is_active"] is True
    
    def test_create_ride_unauthorized(self, client):
        """Test creating ride without authentication"""
        ride_data = {
            "title": "Trip to Airport",
            "description": "Need a ride",
            "start_time": datetime.now().isoformat()
        }
        
        response = client.post("/rides/", json=ride_data)
        assert response.status_code == 401
    
    def test_get_all_rides(self, client, auth_headers):
        """Test retrieving all rides"""
        # Create multiple rides
        rides = [
            {
                "title": "Morning Ride",
                "description": "Early bird",
                "start_time": (datetime.now() + timedelta(hours=1)).isoformat()
            },
            {
                "title": "Evening Ride",
                "description": "Night owl",
                "start_time": (datetime.now() + timedelta(hours=8)).isoformat()
            }
        ]
        
        for ride in rides:
            response = client.post("/rides/", json=ride, headers=auth_headers)
            assert response.status_code == 201
        
        # Get all rides
        response = client.get("/rides/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        titles = [r["title"] for r in data]
        assert "Morning Ride" in titles
        assert "Evening Ride" in titles
    
    def test_get_ride_by_id(self, client, auth_headers):
        """Test retrieving ride by ID"""
        # Create ride
        ride_data = {
            "title": "Beach Trip",
            "description": "Going to the beach",
            "start_time": (datetime.now() + timedelta(days=1)).isoformat()
        }
        
        create_response = client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_id = create_response.json()["id"]
        
        # Get ride by ID
        response = client.get(f"/rides/{ride_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == ride_id
        assert data["title"] == "Beach Trip"
    
    def test_get_ride_by_code(self, client, auth_headers):
        """Test retrieving ride by code"""
        # Create ride
        ride_data = {
            "title": "Code Test Ride",
            "description": "Test code lookup",
            "start_time": (datetime.now() + timedelta(hours=3)).isoformat()
        }
        
        create_response = client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_code = create_response.json()["code"]
        
        # Get ride by code
        response = client.get(f"/rides/code/{ride_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == ride_code
        assert data["title"] == "Code Test Ride"
    
    def test_get_nonexistent_ride(self, client):
        """Test getting ride that doesn't exist"""
        response = client.get("/rides/99999")
        assert response.status_code == 404
    
    def test_update_ride_by_owner(self, client, auth_headers):
        """Test updating ride by its creator"""
        # Create ride
        ride_data = {
            "title": "Original Title",
            "description": "Original description",
            "start_time": (datetime.now() + timedelta(hours=5)).isoformat()
        }
        
        create_response = client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_id = create_response.json()["id"]
        
        # Update ride
        update_data = {
            "title": "Updated Title",
            "description": "Updated description",
            "start_time": (datetime.now() + timedelta(hours=6)).isoformat(),
            "is_active": False
        }
        
        response = client.put(f"/rides/{ride_id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "Updated description"
        assert data["is_active"] is False
    
    def test_update_ride_by_non_owner(self, client, auth_headers, second_user_headers):
        """Test that non-owner cannot update ride"""
        # User 1 creates ride
        ride_data = {
            "title": "User 1 Ride",
            "description": "Created by user 1",
            "start_time": (datetime.now() + timedelta(hours=2)).isoformat()
        }
        
        create_response = client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_id = create_response.json()["id"]
        
        # User 2 tries to update
        update_data = {
            "title": "Hacked Title",
            "description": "Trying to hack",
            "start_time": datetime.now().isoformat(),
            "is_active": True
        }
        
        response = client.put(f"/rides/{ride_id}", json=update_data, headers=second_user_headers)
        
        assert response.status_code == 403
    
    def test_delete_ride_by_owner(self, client, auth_headers):
        """Test deleting ride by its creator"""
        # Create ride
        ride_data = {
            "title": "To Be Deleted",
            "description": "This ride will be deleted",
            "start_time": (datetime.now() + timedelta(hours=1)).isoformat()
        }
        
        create_response = client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_id = create_response.json()["id"]
        
        # Delete ride
        response = client.delete(f"/rides/{ride_id}", headers=auth_headers)
        
        assert response.status_code == 204
        
        # Verify ride is deleted
        get_response = client.get(f"/rides/{ride_id}")
        assert get_response.status_code == 404
    
    def test_delete_ride_by_non_owner(self, client, auth_headers, second_user_headers):
        """Test that non-owner cannot delete ride"""
        # User 1 creates ride
        ride_data = {
            "title": "Protected Ride",
            "description": "Cannot be deleted by others",
            "start_time": (datetime.now() + timedelta(hours=3)).isoformat()
        }
        
        create_response = client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_id = create_response.json()["id"]
        
        # User 2 tries to delete
        response = client.delete(f"/rides/{ride_id}", headers=second_user_headers)
        
        assert response.status_code == 403
        
        # Verify ride still exists
        get_response = client.get(f"/rides/{ride_id}")
        assert get_response.status_code == 200
    
    def test_delete_nonexistent_ride(self, client, auth_headers):
        """Test deleting ride that doesn't exist"""
        response = client.delete("/rides/99999", headers=auth_headers)
        assert response.status_code == 404
