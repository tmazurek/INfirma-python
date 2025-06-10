"""Tests for tax calculation API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestTaxCalculationAPI:
    """Test tax calculation API endpoints."""
    
    def test_calculate_vat_no_company(self, client: TestClient):
        """Test VAT calculation when no company profile exists."""
        calculation_data = {
            "year": 2024,
            "month": 6
        }
        
        response = client.post("/api/v1/taxes/vat/calculate/", json=calculation_data)
        
        assert response.status_code == 404
        assert "Company profile not found" in response.json()["detail"]
    
    def test_calculate_vat_with_company(self, client: TestClient):
        """Test VAT calculation with company profile."""
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
        
        # Now calculate VAT
        calculation_data = {
            "year": 2024,
            "month": 6
        }
        
        response = client.post("/api/v1/taxes/vat/calculate/", json=calculation_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        expected_fields = [
            "calculation_date", "period_start", "period_end", "period_type",
            "total_income_net", "total_income_vat", "total_income_gross",
            "total_expenses_net", "total_expenses_vat", "total_expenses_gross",
            "deductible_expenses_vat", "vat_to_pay", "vat_rate_used",
            "is_vat_payer", "company_profile_id"
        ]
        
        for field in expected_fields:
            assert field in data
        
        # Verify period information
        assert data["period_start"] == "2024-06-01"
        assert data["period_end"] == "2024-06-30"
        assert data["period_type"] == "monthly"
        assert data["vat_rate_used"] == 23.0  # Default VAT rate
        assert data["is_vat_payer"] is True
    
    def test_calculate_vat_get_method(self, client: TestClient):
        """Test VAT calculation using GET method."""
        # Create company profile first
        company_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client.post("/api/v1/company/profile/", json=company_data)
        
        # Calculate VAT using GET
        response = client.get("/api/v1/taxes/vat/calculate/?year=2024&month=6")
        
        assert response.status_code == 200
        data = response.json()
        assert data["period_start"] == "2024-06-01"
        assert data["vat_rate_used"] == 23.0
    
    def test_calculate_pit_with_company(self, client: TestClient):
        """Test PIT calculation with company profile."""
        # Create company profile first
        company_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client.post("/api/v1/company/profile/", json=company_data)
        
        # Calculate PIT
        calculation_data = {
            "year": 2024,
            "month": 6,
            "monthly_income_gross": 12300.00
        }
        
        response = client.post("/api/v1/taxes/pit/calculate/", json=calculation_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        expected_fields = [
            "calculation_date", "period_start", "period_end", "period_type",
            "total_income_net", "total_income_gross", "total_deductible_expenses",
            "taxable_income", "pit_amount", "pit_rate_used", "tax_type_used",
            "zus_deductible_amount", "company_profile_id"
        ]
        
        for field in expected_fields:
            assert field in data
        
        # Verify calculations
        assert data["total_income_gross"] == 12300.00
        assert data["total_income_net"] == 10000.00  # 12300 / 1.23
        assert data["tax_type_used"] == "ryczalt"  # Default tax type
        assert data["pit_rate_used"] == 12.0  # Default ryczałt rate
        assert data["pit_amount"] == 1200.00  # 10000 * 12%
    
    def test_calculate_pit_get_method(self, client: TestClient):
        """Test PIT calculation using GET method."""
        # Create company profile first
        company_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client.post("/api/v1/company/profile/", json=company_data)
        
        # Calculate PIT using GET
        response = client.get("/api/v1/taxes/pit/calculate/?year=2024&month=6&monthly_income_gross=12300.00")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_income_gross"] == 12300.00
        assert data["pit_amount"] == 1200.00
    
    def test_calculate_monthly_tax_summary(self, client: TestClient):
        """Test comprehensive monthly tax summary."""
        # Create company profile first
        company_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client.post("/api/v1/company/profile/", json=company_data)
        
        # Calculate monthly tax summary
        calculation_data = {
            "year": 2024,
            "month": 6,
            "monthly_income_gross": 12300.00
        }
        
        response = client.post("/api/v1/taxes/summary/monthly/", json=calculation_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        expected_fields = [
            "year", "month", "calculation_date", "vat_calculation", "pit_calculation",
            "zus_total_contributions", "zus_health_insurance", "zus_total_with_health",
            "total_taxes_to_pay", "total_social_contributions", "total_monthly_obligations",
            "net_income_after_taxes", "company_profile_id"
        ]
        
        for field in expected_fields:
            assert field in data
        
        # Verify calculations
        assert data["year"] == 2024
        assert data["month"] == 6
        assert data["pit_calculation"]["pit_amount"] == 1200.00
        assert data["zus_total_contributions"] > 0
        assert data["total_monthly_obligations"] > 0
        assert data["net_income_after_taxes"] < 12300.00  # Should be less than gross income
    
    def test_calculate_monthly_tax_summary_get(self, client: TestClient):
        """Test monthly tax summary using GET method."""
        # Create company profile first
        company_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client.post("/api/v1/company/profile/", json=company_data)
        
        # Calculate using GET
        response = client.get("/api/v1/taxes/summary/monthly/2024/6?monthly_income_gross=12300.00")
        
        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2024
        assert data["month"] == 6
    
    def test_calculate_detailed_tax_summary(self, client: TestClient):
        """Test detailed tax summary with breakdown."""
        # Create company profile first
        company_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client.post("/api/v1/company/profile/", json=company_data)
        
        # Calculate detailed tax summary
        calculation_data = {
            "year": 2024,
            "month": 6,
            "monthly_income_gross": 12300.00
        }
        
        response = client.post("/api/v1/taxes/summary/detailed/", json=calculation_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        expected_fields = [
            "calculation_date", "year", "month", "monthly_income_gross",
            "tax_breakdown", "total_vat", "total_pit", "total_zus",
            "total_health_insurance", "total_taxes", "total_social_contributions",
            "total_obligations", "gross_income", "net_income_after_taxes",
            "effective_tax_rate", "vat_rate_used", "pit_rate_used",
            "tax_type_used", "is_vat_payer"
        ]
        
        for field in expected_fields:
            assert field in data
        
        # Verify tax breakdown
        assert "tax_breakdown" in data
        tax_breakdown = data["tax_breakdown"]
        assert len(tax_breakdown) >= 3  # Should have VAT, PIT, ZUS, Health
        
        # Check breakdown items
        breakdown_names = [item["tax_name"] for item in tax_breakdown]
        assert any("PIT" in name for name in breakdown_names)
        assert any("ZUS" in name for name in breakdown_names)
        assert any("Health" in name for name in breakdown_names)
        
        # Verify totals
        assert data["total_pit"] == 1200.00
        assert data["effective_tax_rate"] > 0
        assert data["gross_income"] == 12300.00
    
    def test_compare_tax_options(self, client: TestClient):
        """Test tax options comparison."""
        # Create company profile first
        company_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client.post("/api/v1/company/profile/", json=company_data)
        
        # Compare tax options
        comparison_data = {
            "annual_income": 120000.00,
            "annual_expenses": 20000.00,
            "include_zus": True
        }
        
        response = client.post("/api/v1/taxes/compare/", json=comparison_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        expected_fields = [
            "annual_income", "annual_expenses", "calculation_date",
            "tax_options", "recommended_option", "potential_savings"
        ]
        
        for field in expected_fields:
            assert field in data
        
        # Verify tax options
        assert "tax_options" in data
        tax_options = data["tax_options"]
        assert len(tax_options) == 3  # Ryczałt, Liniowy, Progresywny
        
        # Check each option has required fields
        for option in tax_options:
            assert "tax_type" in option
            assert "tax_type_name" in option
            assert "annual_pit" in option
            assert "annual_zus" in option
            assert "total_annual_obligations" in option
            assert "net_income_after_taxes" in option
            assert "effective_rate" in option
        
        # Verify tax types are present
        tax_types = [option["tax_type"] for option in tax_options]
        assert "ryczalt" in tax_types
        assert "liniowy" in tax_types
        assert "progresywny" in tax_types
        
        # Verify recommendation
        assert data["recommended_option"] in ["Ryczałt", "Liniowy (19%)", "Progresywny (12%/32%)"]
        assert data["potential_savings"] >= 0
    
    def test_invalid_year_month(self, client: TestClient):
        """Test tax calculation with invalid year/month."""
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
        response = client.get("/api/v1/taxes/summary/monthly/2050/6")
        assert response.status_code == 400
        assert "Year must be between 2020 and 2030" in response.json()["detail"]
        
        # Try with invalid month
        response = client.get("/api/v1/taxes/summary/monthly/2024/13")
        assert response.status_code == 400
        assert "Month must be between 1 and 12" in response.json()["detail"]
    
    def test_negative_income(self, client: TestClient):
        """Test tax calculation with negative income."""
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
            "year": 2024,
            "month": 6,
            "monthly_income_gross": -1000.00
        }
        
        response = client.post("/api/v1/taxes/pit/calculate/", json=calculation_data)
        
        # Should return validation error
        assert response.status_code == 422  # Validation error
