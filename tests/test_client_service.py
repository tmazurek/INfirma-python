"""Tests for client service functions."""

import pytest
from datetime import datetime

from app.services.client_service import (
    create_client, 
    get_client_by_id, 
    get_clients,
    update_client,
    delete_client,
    get_active_clients_summary,
    search_clients_by_nip,
    calculate_pagination_info
)
from app.models.client_models import Client


class TestClientService:
    """Test client service functions."""
    
    @pytest.mark.asyncio
    async def test_create_client(self, test_session):
        """Test creating a client."""
        client_data = {
            "name": "Test Client Sp. z o.o.",
            "nip": "1234563224",
            "street": "ul. Kliencka 1",
            "city": "Kraków",
            "postal_code": "30-001",
            "email": "client@test.pl"
        }
        
        client = await create_client(test_session, client_data)
        
        assert client.id is not None
        assert client.name == "Test Client Sp. z o.o."
        assert client.nip == "1234563224"
        assert client.city == "Kraków"
        assert client.is_active is True
        assert client.created_at is not None
    
    @pytest.mark.asyncio
    async def test_create_client_invalid_nip(self, test_session):
        """Test creating client with invalid NIP."""
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",  # Invalid NIP
            "street": "ul. Kliencka 1",
            "city": "Kraków",
            "postal_code": "30-001"
        }
        
        with pytest.raises(ValueError, match="Invalid NIP number"):
            await create_client(test_session, client_data)
    
    @pytest.mark.asyncio
    async def test_create_client_without_nip(self, test_session):
        """Test creating client without NIP (should work)."""
        client_data = {
            "name": "Individual Client",
            "street": "ul. Prywatna 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client = await create_client(test_session, client_data)
        
        assert client.id is not None
        assert client.name == "Individual Client"
        assert client.nip is None
        assert client.is_active is True
    
    @pytest.mark.asyncio
    async def test_get_client_by_id(self, test_session):
        """Test getting client by ID."""
        # Create a client first
        client_data = {
            "name": "Test Client",
            "street": "ul. Test 1",
            "city": "Gdańsk",
            "postal_code": "80-001"
        }
        
        created_client = await create_client(test_session, client_data)
        
        # Get the client
        retrieved_client = await get_client_by_id(test_session, created_client.id)
        
        assert retrieved_client is not None
        assert retrieved_client.id == created_client.id
        assert retrieved_client.name == "Test Client"
    
    @pytest.mark.asyncio
    async def test_get_client_by_id_not_found(self, test_session):
        """Test getting client by non-existent ID."""
        client = await get_client_by_id(test_session, 999)
        assert client is None
    
    @pytest.mark.asyncio
    async def test_get_clients_pagination(self, test_session):
        """Test getting clients with pagination."""
        # Create multiple clients
        for i in range(5):
            client_data = {
                "name": f"Client {i+1}",
                "street": f"ul. Test {i+1}",
                "city": "Warszawa",
                "postal_code": "00-001"
            }
            await create_client(test_session, client_data)
        
        # Get first page
        clients, total = await get_clients(test_session, page=1, per_page=3)
        
        assert len(clients) == 3
        assert total == 5
        assert clients[0].name == "Client 1"  # Should be sorted by name
    
    @pytest.mark.asyncio
    async def test_get_clients_search(self, test_session):
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
        
        await create_client(test_session, client_data_1)
        await create_client(test_session, client_data_2)
        
        # Search by name
        clients, total = await get_clients(test_session, search="ABC")
        
        assert len(clients) == 1
        assert total == 1
        assert clients[0].name == "ABC Company"
        
        # Search by city
        clients, total = await get_clients(test_session, search="Kraków")
        
        assert len(clients) == 1
        assert total == 1
        assert clients[0].name == "XYZ Corporation"
    
    @pytest.mark.asyncio
    async def test_update_client(self, test_session):
        """Test updating a client."""
        # Create a client
        client_data = {
            "name": "Original Name",
            "street": "ul. Original 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client = await create_client(test_session, client_data)
        
        # Update the client
        update_data = {
            "name": "Updated Name",
            "email": "updated@test.pl"
        }
        
        updated_client = await update_client(test_session, client.id, update_data)
        
        assert updated_client is not None
        assert updated_client.name == "Updated Name"
        assert updated_client.email == "updated@test.pl"
        assert updated_client.street == "ul. Original 1"  # Should remain unchanged
        assert updated_client.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_update_client_not_found(self, test_session):
        """Test updating non-existent client."""
        update_data = {"name": "New Name"}
        
        result = await update_client(test_session, 999, update_data)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_client(self, test_session):
        """Test deleting a client (soft delete)."""
        # Create a client
        client_data = {
            "name": "To Delete",
            "street": "ul. Delete 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client = await create_client(test_session, client_data)
        
        # Delete the client
        success = await delete_client(test_session, client.id)
        assert success is True
        
        # Verify client is soft deleted
        deleted_client = await get_client_by_id(test_session, client.id)
        assert deleted_client is not None
        assert deleted_client.is_active is False
        assert deleted_client.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_delete_client_not_found(self, test_session):
        """Test deleting non-existent client."""
        success = await delete_client(test_session, 999)
        assert success is False
    
    @pytest.mark.asyncio
    async def test_search_clients_by_nip(self, test_session):
        """Test searching clients by NIP."""
        # Create a client with NIP
        client_data = {
            "name": "NIP Client",
            "nip": "1234563224",
            "street": "ul. NIP 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        await create_client(test_session, client_data)
        
        # Search by NIP
        found_client = await search_clients_by_nip(test_session, "1234563224")
        
        assert found_client is not None
        assert found_client.name == "NIP Client"
        assert found_client.nip == "1234563224"
        
        # Search by non-existent NIP
        not_found = await search_clients_by_nip(test_session, "9999999999")
        assert not_found is None


class TestPaginationUtils:
    """Test pagination utility functions."""
    
    def test_calculate_pagination_info(self):
        """Test pagination calculation."""
        # Test normal case
        info = calculate_pagination_info(total=25, page=2, per_page=10)
        
        assert info["total"] == 25
        assert info["page"] == 2
        assert info["per_page"] == 10
        assert info["total_pages"] == 3
        assert info["has_next"] is True
        assert info["has_prev"] is True
        
        # Test first page
        info = calculate_pagination_info(total=25, page=1, per_page=10)
        assert info["has_prev"] is False
        assert info["has_next"] is True
        
        # Test last page
        info = calculate_pagination_info(total=25, page=3, per_page=10)
        assert info["has_prev"] is True
        assert info["has_next"] is False
        
        # Test empty result
        info = calculate_pagination_info(total=0, page=1, per_page=10)
        assert info["total_pages"] == 1
        assert info["has_prev"] is False
        assert info["has_next"] is False
