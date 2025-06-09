"""Tests for client API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestClientAPI:
    """Test client API endpoints."""
    
    def test_create_client(self, client: TestClient):
        """Test creating a client via API."""
        client_data = {
            "name": "Test Client Sp. z o.o.",
            "nip": "1234563224",
            "street": "ul. Kliencka 1",
            "city": "Kraków",
            "postal_code": "30-001",
            "email": "client@test.pl",
            "business_activity": "Software development"
        }
        
        response = client.post("/api/v1/clients/", json=client_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Client Sp. z o.o."
        assert data["nip"] == "1234563224"
        assert data["city"] == "Kraków"
        assert data["is_active"] is True
        assert data["id"] is not None
        assert data["created_at"] is not None
    
    def test_create_client_invalid_nip(self, client: TestClient):
        """Test creating client with invalid NIP."""
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",  # Invalid NIP
            "street": "ul. Kliencka 1",
            "city": "Kraków",
            "postal_code": "30-001"
        }
        
        response = client.post("/api/v1/clients/", json=client_data)
        
        assert response.status_code == 400
        assert "Invalid NIP number" in response.json()["detail"]
    
    def test_create_client_without_nip(self, client: TestClient):
        """Test creating client without NIP."""
        client_data = {
            "name": "Individual Client",
            "street": "ul. Prywatna 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        response = client.post("/api/v1/clients/", json=client_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Individual Client"
        assert data["nip"] is None
    
    def test_get_clients_empty(self, client: TestClient):
        """Test getting clients when none exist."""
        response = client.get("/api/v1/clients/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["clients"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["per_page"] == 20
        assert data["total_pages"] == 1
    
    def test_get_clients_with_data(self, client: TestClient):
        """Test getting clients with data."""
        # Create a client first
        client_data = {
            "name": "Test Client",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        create_response = client.post("/api/v1/clients/", json=client_data)
        assert create_response.status_code == 201
        
        # Get clients
        response = client.get("/api/v1/clients/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["clients"]) == 1
        assert data["total"] == 1
        assert data["clients"][0]["name"] == "Test Client"
    
    def test_get_clients_with_pagination(self, client: TestClient):
        """Test getting clients with pagination."""
        # Create multiple clients
        for i in range(5):
            client_data = {
                "name": f"Client {i+1}",
                "street": f"ul. Test {i+1}",
                "city": "Warszawa",
                "postal_code": "00-001"
            }
            response = client.post("/api/v1/clients/", json=client_data)
            assert response.status_code == 201
        
        # Get first page
        response = client.get("/api/v1/clients/?page=1&per_page=3")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["clients"]) == 3
        assert data["total"] == 5
        assert data["total_pages"] == 2
    
    def test_get_clients_with_search(self, client: TestClient):
        """Test searching clients."""
        # Create test clients
        client_data_1 = {
            "name": "ABC Company",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        client_data_2 = {
            "name": "XYZ Corporation",
            "street": "ul. Test 2",
            "city": "Kraków",
            "postal_code": "30-001"
        }
        
        client.post("/api/v1/clients/", json=client_data_1)
        client.post("/api/v1/clients/", json=client_data_2)
        
        # Search by name
        response = client.get("/api/v1/clients/?search=ABC")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["clients"]) == 1
        assert data["clients"][0]["name"] == "ABC Company"
    
    def test_get_client_by_id(self, client: TestClient):
        """Test getting a specific client by ID."""
        # Create a client first
        client_data = {
            "name": "Test Client",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        create_response = client.post("/api/v1/clients/", json=client_data)
        created_client = create_response.json()
        
        # Get the client
        response = client.get(f"/api/v1/clients/{created_client['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_client["id"]
        assert data["name"] == "Test Client"
    
    def test_get_client_by_id_not_found(self, client: TestClient):
        """Test getting non-existent client."""
        response = client.get("/api/v1/clients/999")
        
        assert response.status_code == 404
        assert "Client not found" in response.json()["detail"]
    
    def test_update_client(self, client: TestClient):
        """Test updating a client."""
        # Create a client first
        client_data = {
            "name": "Original Name",
            "street": "ul. Original 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        create_response = client.post("/api/v1/clients/", json=client_data)
        created_client = create_response.json()
        
        # Update the client
        update_data = {
            "name": "Updated Name",
            "email": "updated@test.pl"
        }
        
        response = client.put(f"/api/v1/clients/{created_client['id']}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["email"] == "updated@test.pl"
        assert data["street"] == "ul. Original 1"  # Should remain unchanged
    
    def test_update_client_not_found(self, client: TestClient):
        """Test updating non-existent client."""
        update_data = {"name": "New Name"}
        
        response = client.put("/api/v1/clients/999", json=update_data)
        
        assert response.status_code == 404
        assert "Client not found" in response.json()["detail"]
    
    def test_delete_client(self, client: TestClient):
        """Test deleting a client."""
        # Create a client first
        client_data = {
            "name": "To Delete",
            "street": "ul. Delete 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        create_response = client.post("/api/v1/clients/", json=client_data)
        created_client = create_response.json()
        
        # Delete the client
        response = client.delete(f"/api/v1/clients/{created_client['id']}")
        
        assert response.status_code == 204
        
        # Verify client is soft deleted (still exists but inactive)
        get_response = client.get(f"/api/v1/clients/{created_client['id']}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["is_active"] is False
    
    def test_delete_client_not_found(self, client: TestClient):
        """Test deleting non-existent client."""
        response = client.delete("/api/v1/clients/999")
        
        assert response.status_code == 404
        assert "Client not found" in response.json()["detail"]
    
    def test_get_clients_summary(self, client: TestClient):
        """Test getting clients summary."""
        # Create test clients
        client_data_1 = {
            "name": "Active Client",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        client_data_2 = {
            "name": "Inactive Client",
            "street": "ul. Test 2",
            "city": "Kraków",
            "postal_code": "30-001",
            "is_active": False
        }
        
        client.post("/api/v1/clients/", json=client_data_1)
        client.post("/api/v1/clients/", json=client_data_2)
        
        # Get summary (should only include active clients)
        response = client.get("/api/v1/clients/summary/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Active Client"
    
    def test_search_client_by_nip(self, client: TestClient):
        """Test searching client by NIP."""
        # Create a client with NIP
        client_data = {
            "name": "NIP Client",
            "nip": "1234563224",
            "street": "ul. NIP 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client.post("/api/v1/clients/", json=client_data)
        
        # Search by NIP
        response = client.get("/api/v1/clients/search/nip/1234563224")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "NIP Client"
        assert data["nip"] == "1234563224"
        
        # Search by non-existent NIP
        response = client.get("/api/v1/clients/search/nip/9999999999")
        
        assert response.status_code == 200
        assert response.json() is None
