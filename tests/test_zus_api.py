"""Tests for ZUS calculation API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestZUSCalculationAPI:
    """Test ZUS calculation API endpoints."""
    
    def test_calculate_monthly_zus_no_company(self, client: TestClient):
        """Test ZUS calculation when no company profile exists."""
        calculation_data = {
            "monthly_income": 8000.00
        }
        
        response = client.post("/api/v1/zus/calculate/", json=calculation_data)
        
        assert response.status_code == 404
        assert "Company profile not found" in response.json()["detail"]
    
    def test_calculate_monthly_zus_with_company(self, client: TestClient):
        """Test ZUS calculation with company profile."""
        # First create a company profile
        company_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        company_response = client.post("/api/v1/company/profile/", json=company_data)
        assert company_response.status_code == 201
        
        # Now calculate ZUS
        calculation_data = {
            "monthly_income": 8000.00
        }
        
        response = client.post("/api/v1/zus/calculate/", json=calculation_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        expected_fields = [
            "zus_base_amount", "emerytalne", "rentowe", "wypadkowe",
            "chorobowe", "labor_fund", "fep", "health_insurance",
            "health_insurance_tier", "total_zus_contributions",
            "total_with_health", "calculation_date", "settings_effective_from"
        ]
        
        for field in expected_fields:
            assert field in data
        
        # Verify calculations (using default rates)
        assert data["zus_base_amount"] == 5203.80
        assert data["emerytalne"] == 1015.78  # 5203.80 * 19.52%
        assert data["rentowe"] == 416.30      # 5203.80 * 8.00%
        assert data["wypadkowe"] == 86.90     # 5203.80 * 1.67%
        assert data["chorobowe"] == 127.49    # 5203.80 * 2.45%
        assert data["labor_fund"] == 127.49   # 5203.80 * 2.45%
        assert data["fep"] == 5.20            # 5203.80 * 0.10%
        
        # Verify health insurance (medium tier)
        assert data["health_insurance"] == 472.50  # 7000 * 0.75 * 0.09
        assert data["health_insurance_tier"] == "medium"
        
        # Verify totals
        expected_zus_total = 1015.78 + 416.30 + 86.90 + 127.49 + 127.49 + 5.20
        assert abs(data["total_zus_contributions"] - expected_zus_total) < 0.01
        assert abs(data["total_with_health"] - (expected_zus_total + 472.50)) < 0.01
    
    def test_calculate_monthly_zus_get_method(self, client: TestClient):
        """Test ZUS calculation using GET method."""
        # Create company profile first
        company_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client.post("/api/v1/company/profile/", json=company_data)
        
        # Calculate ZUS using GET
        response = client.get("/api/v1/zus/calculate/?monthly_income=5000.00")
        
        assert response.status_code == 200
        data = response.json()
        assert data["zus_base_amount"] == 5203.80
        assert "emerytalne" in data
    
    def test_calculate_monthly_zus_without_income(self, client: TestClient):
        """Test ZUS calculation without monthly income."""
        # Create company profile first
        company_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client.post("/api/v1/company/profile/", json=company_data)
        
        # Calculate ZUS without income
        response = client.post("/api/v1/zus/calculate/", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        # Should still calculate ZUS contributions
        assert data["emerytalne"] > 0
        assert data["health_insurance"] > 0  # Uses default tier calculation
    
    def test_calculate_detailed_zus(self, client: TestClient):
        """Test detailed ZUS calculation."""
        # Create company profile first
        company_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client.post("/api/v1/company/profile/", json=company_data)
        
        # Calculate detailed ZUS
        calculation_data = {
            "monthly_income": 10000.00
        }
        
        response = client.post("/api/v1/zus/calculate/detailed/", json=calculation_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify detailed response structure
        assert "contributions" in data
        assert "health_insurance_base" in data
        assert "monthly_income" in data
        
        # Verify contributions breakdown
        contributions = data["contributions"]
        assert len(contributions) == 6  # All ZUS contributions
        
        contribution_names = [c["contribution_name"] for c in contributions]
        expected_names = [
            "Emerytalne (Pension)", "Rentowe (Disability)", "Wypadkowe (Accident)",
            "Chorobowe (Sickness)", "Labor Fund", "FEP"
        ]
        
        for name in expected_names:
            assert name in contribution_names
        
        # Verify each contribution has required fields
        for contribution in contributions:
            assert "base_amount" in contribution
            assert "rate_percent" in contribution
            assert "calculated_amount" in contribution
            assert "is_active" in contribution
    
    def test_calculate_yearly_zus(self, client: TestClient):
        """Test yearly ZUS calculation."""
        # Create company profile first
        company_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client.post("/api/v1/company/profile/", json=company_data)
        
        # Calculate yearly ZUS
        calculation_data = {
            "year": 2024,
            "monthly_incomes": {
                "1": 5000.00,
                "2": 6000.00,
                "3": 7000.00
            }
        }
        
        response = client.post("/api/v1/zus/calculate/yearly/", json=calculation_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify yearly response structure
        assert data["year"] == 2024
        assert "monthly_breakdown" in data
        assert "yearly_totals" in data
        assert "calculation_date" in data
        
        # Verify monthly breakdown
        monthly_breakdown = data["monthly_breakdown"]
        assert len(monthly_breakdown) == 12  # All 12 months
        
        # Check first month
        jan_data = monthly_breakdown[0]
        assert jan_data["month"] == 1
        assert "emerytalne" in jan_data
        assert "total_with_health" in jan_data
        
        # Verify yearly totals
        yearly_totals = data["yearly_totals"]
        assert "emerytalne" in yearly_totals
        assert "total_with_health" in yearly_totals
    
    def test_calculate_yearly_zus_get_method(self, client: TestClient):
        """Test yearly ZUS calculation using GET method."""
        # Create company profile first
        company_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client.post("/api/v1/company/profile/", json=company_data)
        
        # Calculate yearly ZUS using GET
        response = client.get("/api/v1/zus/calculate/yearly/2024")
        
        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2024
        assert "monthly_breakdown" in data
    
    def test_calculate_yearly_zus_invalid_year(self, client: TestClient):
        """Test yearly ZUS calculation with invalid year."""
        # Create company profile first
        company_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client.post("/api/v1/company/profile/", json=company_data)
        
        # Try with invalid year
        response = client.get("/api/v1/zus/calculate/yearly/2050")
        
        assert response.status_code == 400
        assert "Year must be between 2020 and 2030" in response.json()["detail"]
    
    def test_calculate_zus_with_negative_income(self, client: TestClient):
        """Test ZUS calculation with negative income."""
        # Create company profile first
        company_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client.post("/api/v1/company/profile/", json=company_data)
        
        # Try with negative income
        calculation_data = {
            "monthly_income": -1000.00
        }
        
        response = client.post("/api/v1/zus/calculate/", json=calculation_data)
        
        # Should return validation error
        assert response.status_code == 422  # Validation error
    
    def test_calculate_zus_with_custom_date(self, client: TestClient):
        """Test ZUS calculation with custom calculation date."""
        # Create company profile first
        company_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client.post("/api/v1/company/profile/", json=company_data)
        
        # Calculate ZUS with custom date
        calculation_data = {
            "monthly_income": 8000.00,
            "calculation_date": "2024-06-15"
        }
        
        response = client.post("/api/v1/zus/calculate/", json=calculation_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["calculation_date"] == "2024-06-15"
