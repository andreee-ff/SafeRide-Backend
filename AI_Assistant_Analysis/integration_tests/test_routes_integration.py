"""
Integration tests for Route endpoints
Tests real database operations for route management
"""
import pytest
from fastapi import status

@pytest.mark.asyncio
class TestRouteEndpoints:
    """Test route creation, retrieval, update, and deletion with real database"""

    async def test_create_route_success(self, client, auth_headers):
        """Test creating a new GPX route"""
        route_data = {
            "title": "Mountain Trail",
            "description": "A scenic mountain bike trail",
            "gpx_data": "<gpx>...</gpx>"
        }
        
        response = await client.post("/routes/", json=route_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "Mountain Trail"
        assert data["description"] == "A scenic mountain bike trail"
        assert "id" in data
        assert data["distance_meters"] == 0.0  # Currently default

    async def test_get_all_routes(self, client, auth_headers):
        """Test retrieving all routes in system"""
        # Create routes by different users
        await client.post("/routes/", json={"title": "Route 1", "gpx_data": "data1"}, headers=auth_headers)
        
        response = await client.get("/routes/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert any(r["title"] == "Route 1" for r in data)

    async def test_get_owned_routes(self, client, auth_headers, second_user_headers):
        """Test retrieving only routes owned by current user"""
        # User 1 creates a route
        await client.post("/routes/", json={"title": "User1 Route", "gpx_data": "data1"}, headers=auth_headers)
        
        # User 2 creates a route
        await client.post("/routes/", json={"title": "User2 Route", "gpx_data": "data2"}, headers=second_user_headers)
        
        # Check User 1 routes
        response = await client.get("/routes/owned", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        titles = [r["title"] for r in data]
        assert "User1 Route" in titles
        assert "User2 Route" not in titles

    async def test_get_route_by_id(self, client, auth_headers):
        """Test retrieving a specific route by ID"""
        create_resp = await client.post("/routes/", json={"title": "Find Me", "gpx_data": "data"}, headers=auth_headers)
        route_id = create_resp.json()["id"]
        
        response = await client.get(f"/routes/{route_id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["title"] == "Find Me"

    async def test_update_route_success(self, client, auth_headers):
        """Test owner can update their route"""
        create_resp = await client.post("/routes/", json={"title": "Old Title", "gpx_data": "data"}, headers=auth_headers)
        route_id = create_resp.json()["id"]
        
        update_data = {"title": "New Title", "description": "Updated description"}
        response = await client.put(f"/routes/{route_id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["title"] == "New Title"
        assert response.json()["description"] == "Updated description"

    async def test_update_route_unauthorized(self, client, auth_headers, second_user_headers):
        """Test non-owner cannot update a route"""
        # User 1 creates route
        create_resp = await client.post("/routes/", json={"title": "U1 Route", "gpx_data": "data"}, headers=auth_headers)
        route_id = create_resp.json()["id"]
        
        # User 2 tries to update
        response = await client.put(f"/routes/{route_id}", json={"title": "Hacked"}, headers=second_user_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_delete_route_success(self, client, auth_headers):
        """Test owner can delete their route"""
        create_resp = await client.post("/routes/", json={"title": "Delete Me", "gpx_data": "data"}, headers=auth_headers)
        route_id = create_resp.json()["id"]
        
        response = await client.delete(f"/routes/{route_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify gone
        get_resp = await client.get(f"/routes/{route_id}")
        assert get_resp.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_route_unauthorized(self, client, auth_headers, second_user_headers):
        """Test non-owner cannot delete a route"""
        # User 1 creates route
        create_resp = await client.post("/routes/", json={"title": "U1 Route", "gpx_data": "data"}, headers=auth_headers)
        route_id = create_resp.json()["id"]
        
        # User 2 tries to delete
        response = await client.delete(f"/routes/{route_id}", headers=second_user_headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN
