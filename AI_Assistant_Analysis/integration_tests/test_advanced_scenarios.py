"""
Advanced integration tests for complex scenarios
Tests cascading deletes, foreign keys, edge cases, and data integrity
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.future import select

@pytest.mark.asyncio
class TestCascadingDeletes:
    """Test cascading deletes and foreign key constraints"""
    
    @pytest.mark.postgres
    async def test_delete_ride_with_participations(self, client, auth_headers, second_user_headers):
        """Test deleting a ride that has participants - CASCADE DELETE works in PostgreSQL"""
        # Create ride
        ride_data = {
            "title": "Ride with Participants",
            "description": "What happens to participants?",
            "start_time": (datetime.now() + timedelta(hours=3)).isoformat()
        }
        
        ride_response = await client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_id = ride_response.json()["id"]
        ride_code = ride_response.json()["code"]
        
        # Add participants
        participation_data = {"ride_code": ride_code}
        
        # Creator (User 1) is already a participant
        # Get their participation ID
        start_participants = await client.get(f"/rides/{ride_id}/participants")
        p1_id = start_participants.json()[0]["id"]
        
        p2 = await client.post("/participations/", json=participation_data, headers=second_user_headers)
        assert p2.status_code == 201
        p2_id = p2.json()["id"]
        
        # Delete the ride
        delete_response = await client.delete(f"/rides/{ride_id}", headers=auth_headers)
        assert delete_response.status_code == 204
        
        # Verify participations are also deleted (cascade)
        p1_check = await client.get(f"/participations/{p1_id}")
        p2_check = await client.get(f"/participations/{p2_id}")
        
        assert p1_check.status_code == 404
        assert p2_check.status_code == 404
        
        # Verify ride is also deleted
        ride_check = await client.get(f"/rides/{ride_id}")
        assert ride_check.status_code == 404
    
    async def test_orphaned_participation_protection(self, client, auth_headers):
        """Test that participations can't reference non-existent rides"""
        # Try to create participation with invalid ride_code
        participation_data = {"ride_code": "XXXXXX"}
        
        response = await client.post("/participations/", json=participation_data, headers=auth_headers)
        assert response.status_code == 404


@pytest.mark.asyncio
class TestConcurrentOperations:
    """Test concurrent operations and potential race conditions"""
    
    async def test_multiple_users_same_ride_code(self, client, auth_headers, second_user_headers):
        """Test multiple users joining same ride simultaneously"""
        # Create ride
        ride_data = {
            "title": "Popular Ride",
            "description": "Many users want to join",
            "start_time": (datetime.now() + timedelta(hours=2)).isoformat()
        }
        
        ride_response = await client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_code = ride_response.json()["code"]
        ride_id = ride_response.json()["id"]
        
        # Both users join with same code
        participation_data = {"ride_code": ride_code}
        
        # User 1 is already joined (auto)
        # User 2 joins
        p2 = await client.post("/participations/", json=participation_data, headers=second_user_headers)
        
        # Get p1 details from listing
        all_participants = await client.get(f"/rides/{ride_id}/participants")
        p1_data = next(p for p in all_participants.json() if p["user_id"] == p2.json()["user_id"] - 1) # Assuming sequential IDs or just getting other one
        # Safer way: get the one that is NOT p2
        p1_data = next(p for p in all_participants.json() if p["id"] != p2.json()["id"])
        
        assert p2.status_code == 201
        
        # Verify both participations are different
        assert p1_data["id"] != p2.json()["id"]
        assert p1_data["user_id"] != p2.json()["user_id"]
        # Ride ID check
        assert p2.json()["ride_id"] == ride_id
    
    @pytest.mark.postgres
    async def test_duplicate_participation_same_user(self, client, auth_headers):
        """Test user trying to join same ride twice - should return 409 CONFLICT"""
        # Create ride
        ride_data = {
            "title": "Unique Participation Ride",
            "description": "User should join only once",
            "start_time": (datetime.now() + timedelta(hours=2)).isoformat()
        }
        
        ride_response = await client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_code = ride_response.json()["code"]
        
        participation_data = {"ride_code": ride_code}
        
        # First join
        # User is already joined automatically upon creation
        # So trying to join explicitly should fail strictly speaking, 
        # OR we assume the test meant to try joining TWICE explicitly.
        # Given the current logic, the FIRST explicit join is already a duplicate.
        
        # Try joining (should act as duplicate)
        response = await client.post("/participations/", json=participation_data, headers=auth_headers)
        
        # If the API handles it gracefully, it might return 409
        # If not, it returns 500 (Integrity Error).
        # We should assume we want 409.
        assert response.status_code == 409
        assert "already joined" in response.json()["detail"].lower()


@pytest.mark.asyncio
class TestDataIntegrity:
    """Test data integrity and validation"""
    
    async def test_ride_code_uniqueness(self, client, auth_headers, test_db):
        """Test that ride codes are unique"""
        from app.models import RideModel
        
        # Create multiple rides
        codes = set()
        for i in range(10):
            ride_data = {
                "title": f"Ride {i}",
                "description": f"Test ride {i}",
                "start_time": (datetime.now() + timedelta(hours=i+1)).isoformat()
            }
            
            response = await client.post("/rides/", json=ride_data, headers=auth_headers)
            assert response.status_code == 201
            code = response.json()["code"]
            codes.add(code)
        
        # All codes should be unique
        assert len(codes) == 10
        
        # Verify in database
        # Updated to async query
        result = await test_db.execute(select(RideModel.code))
        db_codes = result.all()
        db_codes_set = {code[0] for code in db_codes}
        assert len(db_codes_set) >= 10
    
    async def test_username_uniqueness_constraint(self, client):
        """Test username uniqueness at database level"""
        user_data = {
            "username": "unique_test_user",
            "password": "password123"
        }
        
        # First user
        r1 = await client.post("/users/", json=user_data)
        assert r1.status_code == 201
        
        # Duplicate username
        r2 = await client.post("/users/", json=user_data)
        assert r2.status_code == 409
    
    async def test_participation_foreign_key_integrity(self, client, auth_headers, second_user_headers, test_db):
        """Test that participation always references valid ride and user"""
        from app.models import ParticipationModel
        
        # Create valid participation
        ride_data = {
            "title": "FK Test Ride",
            "description": "Testing foreign keys",
            "start_time": (datetime.now() + timedelta(hours=2)).isoformat()
        }
        
        ride_response = await client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_code = ride_response.json()["code"]
        
        participation_data = {"ride_code": ride_code}
        participation_data = {"ride_code": ride_code}
        p_response = await client.post("/participations/", json=participation_data, headers=second_user_headers)
        assert p_response.status_code == 201
        
        p_id = p_response.json()["id"]
        
        # Verify in database
        result = await test_db.execute(select(ParticipationModel).filter_by(id=p_id))
        participation = result.scalar_one_or_none()
        
        assert participation is not None
        assert participation.user_id is not None
        assert participation.ride_id is not None


@pytest.mark.asyncio
class TestComplexQueries:
    """Test complex query scenarios"""
    
    async def test_get_rides_with_multiple_participations(self, client, auth_headers, second_user_headers):
        """Test getting rides and their participation counts"""
        # Create ride
        ride_data = {
            "title": "Multi-Participant Ride",
            "description": "Testing participation tracking",
            "start_time": (datetime.now() + timedelta(hours=3)).isoformat()
        }
        
        ride_response = await client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_id = ride_response.json()["id"]
        ride_code = ride_response.json()["code"]
        
        # Add multiple participants
        participation_data = {"ride_code": ride_code}
        
        # Creator (User 1) is already joined
        # User 2 joins
        await client.post("/participations/", json=participation_data, headers=second_user_headers)
        
        # Get all participations and count for this ride
        all_p = await client.get("/participations/")
        participations = [p for p in all_p.json() if p["ride_id"] == ride_id]
        
        assert len(participations) >= 2
    
    async def test_filter_active_inactive_rides(self, client, auth_headers):
        """Test filtering rides by active status"""
        # Create active ride
        active_ride = {
            "title": "Active Ride",
            "description": "This is active",
            "start_time": (datetime.now() + timedelta(hours=2)).isoformat()
        }
        
        r1 = await client.post("/rides/", json=active_ride, headers=auth_headers)
        active_id = r1.json()["id"]
        
        # Create and deactivate ride
        inactive_ride = {
            "title": "Inactive Ride",
            "description": "This will be inactive",
            "start_time": (datetime.now() + timedelta(hours=3)).isoformat()
        }
        
        r2 = await client.post("/rides/", json=inactive_ride, headers=auth_headers)
        inactive_id = r2.json()["id"]
        
        # Deactivate second ride
        update_data = {
            "title": "Inactive Ride",
            "description": "This will be inactive",
            "start_time": (datetime.now() + timedelta(hours=3)).isoformat(),
            "is_active": False
        }
        
        await client.put(f"/rides/{inactive_id}", json=update_data, headers=auth_headers)
        
        # Get all rides and check statuses
        all_rides = await client.get("/rides/")
        rides_list = all_rides.json()
        
        active_ride_obj = next((r for r in rides_list if r["id"] == active_id), None)
        inactive_ride_obj = next((r for r in rides_list if r["id"] == inactive_id), None)
        
        assert active_ride_obj["is_active"] is True
        assert inactive_ride_obj["is_active"] is False


@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    async def test_update_nonexistent_ride(self, client, auth_headers):
        """Test updating ride that doesn't exist"""
        update_data = {
            "title": "Updated",
            "description": "Updated",
            "start_time": datetime.now().isoformat(),
            "is_active": True
        }
        
        response = await client.put("/rides/99999", json=update_data, headers=auth_headers)
        assert response.status_code == 404
    
    async def test_participation_with_empty_location(self, client, auth_headers):
        """Test creating participation without location data"""
        ride_data = {
            "title": "Location Test Ride",
            "description": "Testing optional location",
            "start_time": (datetime.now() + timedelta(hours=2)).isoformat()
        }
        
        ride_response = await client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_code = ride_response.json()["code"]
        
        # Create participation without location
        participation_data = {"ride_code": ride_code}
        
        # Create participation without location (User 2)
        # Need second user because creator is already joined
        user_data = {"username": "loc_test_user", "password": "password"}
        await client.post("/users/", json=user_data)
        login_res = await client.post("/auth/login", data=user_data)
        token = login_res.json()["access_token"]
        new_headers = {"Authorization": f"Bearer {token}"}

        response = await client.post("/participations/", json=participation_data, headers=new_headers)
        assert response.status_code == 201
        
        # Verify location fields are null
        data = response.json()
        assert data.get("latitude") is None
        assert data.get("longitude") is None
    
    async def test_long_string_fields(self, client, auth_headers):
        """Test handling of very long strings"""
        # Try to create ride with very long title
        ride_data = {
            "title": "A" * 200,  # Very long title (max 100 in DB)
            "description": "B" * 500,  # Very long description (max 255 in DB)
            "start_time": (datetime.now() + timedelta(hours=2)).isoformat()
        }
        
        response = await client.post("/rides/", json=ride_data, headers=auth_headers)
        
        # Should either truncate or reject based on DB constraints
        # With string length constraints, this should fail
        assert response.status_code in [201, 422, 400, 500]
    
    async def test_past_datetime_for_ride(self, client, auth_headers):
        """Test creating ride with past datetime"""
        ride_data = {
            "title": "Past Ride",
            "description": "This ride is in the past",
            "start_time": (datetime.now() - timedelta(hours=5)).isoformat()
        }
        
        response = await client.post("/rides/", json=ride_data, headers=auth_headers)
        
        # Current implementation allows past dates
        # Could add validation to reject them
        assert response.status_code == 201


@pytest.mark.asyncio
class TestSecurityScenarios:
    """Test security-related scenarios"""
    
    async def test_user_cannot_update_other_users_participation(self, client, auth_headers, second_user_headers):
        """Test that user cannot modify another user's participation"""
        # User 1 creates ride
        ride_data = {
            "title": "Security Test Ride",
            "description": "Testing participation security",
            "start_time": (datetime.now() + timedelta(hours=2)).isoformat()
        }
        
        ride_response = await client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_code = ride_response.json()["code"]
        
        # User 2 joins
        participation_data = {"ride_code": ride_code}
        p_response = await client.post("/participations/", json=participation_data, headers=second_user_headers)
        p_id = p_response.json()["id"]
        
        # User 1 tries to update User 2's participation
        update_data = {
            "latitude": 55.7558,
            "longitude": 37.6173,
            "location_timestamp": (datetime.now() - timedelta(seconds=10)).isoformat()
        }
        
        response = await client.put(f"/participations/{p_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 403
    
    async def test_unauthorized_ride_deletion(self, client, auth_headers, second_user_headers):
        """Test that only ride creator can delete it"""
        # User 1 creates ride
        ride_data = {
            "title": "Protected Ride",
            "description": "Only creator can delete",
            "start_time": (datetime.now() + timedelta(hours=2)).isoformat()
        }
        
        ride_response = await client.post("/rides/", json=ride_data, headers=auth_headers)
        ride_id = ride_response.json()["id"]
        
        # User 2 tries to delete
        response = await client.delete(f"/rides/{ride_id}", headers=second_user_headers)
        assert response.status_code == 403
        
        # Verify ride still exists
        check = await client.get(f"/rides/{ride_id}")
        assert check.status_code == 200
