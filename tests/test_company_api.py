"""Tests for company API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestCompanyAPI:
    """Test company API endpoints."""
    
    def test_create_company_profile(self, client: TestClient):
        """Test creating a company profile via API."""
        profile_data = {
            "name": "Test Company Sp. z o.o.",
            "nip": "1234563221",
            "street": "ul. Testowa 1",
            "city": "Warszawa",
            "postal_code": "00-001",
            "country": "Poland",
            "email": "test@company.pl",
            "business_activity": "Software development"
        }
        
        response = client.post("/api/v1/company/profile/", json=profile_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Company Sp. z o.o."
        assert data["nip"] == "1234563221"
        assert data["city"] == "Warszawa"
        assert data["id"] is not None
    
    def test_create_company_profile_invalid_nip(self, client: TestClient):
        """Test creating company profile with invalid NIP."""
        profile_data = {
            "name": "Test Company",
            "nip": "1234567890",  # Invalid NIP
            "street": "ul. Testowa 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        response = client.post("/api/v1/company/profile/", json=profile_data)
        
        assert response.status_code == 400
        assert "Invalid NIP number" in response.json()["detail"]
    
    def test_get_company_profile_not_exists(self, client: TestClient):
        """Test getting company profile when none exists."""
        response = client.get("/api/v1/company/profile/")
        
        assert response.status_code == 200
        assert response.json() is None
    
    def test_get_company_profile_exists(self, client: TestClient):
        """Test getting existing company profile."""
        # First create a profile
        profile_data = {
            "name": "Test Company",
            "nip": "1234563221",
            "street": "ul. Testowa 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        create_response = client.post("/api/v1/company/profile/", json=profile_data)
        assert create_response.status_code == 201
        
        # Then get it
        get_response = client.get("/api/v1/company/profile/")
        
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["name"] == "Test Company"
        assert data["nip"] == "1234563221"
    
    def test_update_company_profile(self, client: TestClient):
        """Test updating company profile."""
        # First create a profile
        profile_data = {
            "name": "Test Company",
            "nip": "1234563221",
            "street": "ul. Testowa 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        create_response = client.post("/api/v1/company/profile/", json=profile_data)
        assert create_response.status_code == 201
        
        # Update it
        update_data = {
            "name": "Updated Company Name",
            "email": "updated@company.pl"
        }
        
        update_response = client.put("/api/v1/company/profile/", json=update_data)
        
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"] == "Updated Company Name"
        assert data["email"] == "updated@company.pl"
        assert data["nip"] == "1234563221"  # Should remain unchanged
    
    def test_update_company_profile_not_exists(self, client: TestClient):
        """Test updating company profile when none exists."""
        update_data = {
            "name": "Updated Company Name"
        }
        
        response = client.put("/api/v1/company/profile/", json=update_data)
        
        assert response.status_code == 404
        assert "Company profile not found" in response.json()["detail"]
    
    def test_get_tax_settings_no_company(self, client: TestClient):
        """Test getting tax settings when no company exists."""
        response = client.get("/api/v1/company/settings/tax/")
        
        assert response.status_code == 404
        assert "Company profile not found" in response.json()["detail"]
    
    def test_get_tax_settings_with_company(self, client: TestClient):
        """Test getting tax settings after creating company."""
        # First create a profile
        profile_data = {
            "name": "Test Company",
            "nip": "1234563221",
            "street": "ul. Testowa 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        create_response = client.post("/api/v1/company/profile/", json=profile_data)
        assert create_response.status_code == 201
        
        # Get tax settings
        response = client.get("/api/v1/company/settings/tax/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_vat_payer"] is True
        assert float(data["vat_rate"]) == 23.00
        assert data["tax_type"] == "ryczalt"
        assert float(data["pit_ryczalt_rate"]) == 12.00
    
    def test_update_tax_settings(self, client: TestClient):
        """Test updating tax settings."""
        # First create a profile
        profile_data = {
            "name": "Test Company",
            "nip": "1234563221",
            "street": "ul. Testowa 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        create_response = client.post("/api/v1/company/profile/", json=profile_data)
        assert create_response.status_code == 201
        
        # Update tax settings
        update_data = {
            "vat_rate": 8.00,
            "is_vat_payer": False
        }
        
        response = client.put("/api/v1/company/settings/tax/", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_vat_payer"] is False
        assert float(data["vat_rate"]) == 8.00
        assert data["tax_type"] == "ryczalt"  # Should remain unchanged
    
    def test_get_zus_settings_with_company(self, client: TestClient):
        """Test getting ZUS settings after creating company."""
        # First create a profile
        profile_data = {
            "name": "Test Company",
            "nip": "1234563221",
            "street": "ul. Testowa 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        create_response = client.post("/api/v1/company/profile/", json=profile_data)
        assert create_response.status_code == 201
        
        # Get ZUS settings
        response = client.get("/api/v1/company/settings/zus/")
        
        assert response.status_code == 200
        data = response.json()
        assert float(data["zus_base_amount"]) == 5203.80
        assert float(data["emerytalne_rate"]) == 19.52
        assert float(data["rentowe_rate"]) == 8.00
        assert data["is_chorobowe_active"] is True
        assert data["health_insurance_tier"] == "medium"
