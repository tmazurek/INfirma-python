"""Tests for ZUS calculation service."""

import pytest
from decimal import Decimal
from datetime import date

from app.services.zus_service import (
    round_to_grosz,
    calculate_contribution_amount,
    calculate_health_insurance,
    calculate_monthly_zus,
    calculate_yearly_zus_summary,
    ZUSCalculationResult
)
from app.services.company_service import create_company_profile
from app.models.company_models import HealthInsuranceTier


class TestZUSCalculationUtils:
    """Test ZUS calculation utility functions."""
    
    def test_round_to_grosz(self):
        """Test rounding to Polish grosz."""
        # Test normal rounding
        assert round_to_grosz(Decimal("123.456")) == Decimal("123.46")
        assert round_to_grosz(Decimal("123.454")) == Decimal("123.45")
        
        # Test half-up rounding (Polish standard)
        assert round_to_grosz(Decimal("123.455")) == Decimal("123.46")
        assert round_to_grosz(Decimal("123.445")) == Decimal("123.45")
        
        # Test already rounded values
        assert round_to_grosz(Decimal("123.45")) == Decimal("123.45")
        assert round_to_grosz(Decimal("123.00")) == Decimal("123.00")
    
    def test_calculate_contribution_amount(self):
        """Test contribution amount calculation."""
        # Test normal calculation
        base = Decimal("5203.80")
        rate = Decimal("19.52")
        expected = round_to_grosz(base * rate / Decimal("100"))
        
        result = calculate_contribution_amount(base, rate)
        assert result == expected
        assert result == Decimal("1015.78")  # 5203.80 * 19.52% = 1015.78
        
        # Test zero rate
        assert calculate_contribution_amount(base, Decimal("0")) == Decimal("0.00")
        
        # Test zero base
        assert calculate_contribution_amount(Decimal("0"), rate) == Decimal("0.00")
        
        # Test negative values
        assert calculate_contribution_amount(Decimal("-100"), rate) == Decimal("0.00")
        assert calculate_contribution_amount(base, Decimal("-5")) == Decimal("0.00")
    
    def test_calculate_health_insurance(self):
        """Test health insurance calculation."""
        monthly_income = Decimal("10000.00")
        
        # Test low tier (9% of 60% of 7000)
        low_result = calculate_health_insurance(monthly_income, HealthInsuranceTier.LOW)
        expected_low = round_to_grosz(Decimal("7000") * Decimal("0.60") * Decimal("0.09"))
        assert low_result == expected_low
        assert low_result == Decimal("378.00")
        
        # Test medium tier (9% of 75% of 7000)
        medium_result = calculate_health_insurance(monthly_income, HealthInsuranceTier.MEDIUM)
        expected_medium = round_to_grosz(Decimal("7000") * Decimal("0.75") * Decimal("0.09"))
        assert medium_result == expected_medium
        assert medium_result == Decimal("472.50")
        
        # Test high tier with high income (9% of income)
        high_result = calculate_health_insurance(monthly_income, HealthInsuranceTier.HIGH)
        expected_high = round_to_grosz(monthly_income * Decimal("0.09"))
        assert high_result == expected_high
        assert high_result == Decimal("900.00")
        
        # Test high tier with low income (minimum base applies)
        low_income = Decimal("3000.00")
        high_low_result = calculate_health_insurance(low_income, HealthInsuranceTier.HIGH)
        min_base = Decimal("7000") * Decimal("0.75")
        expected_high_low = round_to_grosz(min_base * Decimal("0.09"))
        assert high_low_result == expected_high_low
        assert high_low_result == Decimal("472.50")


class TestZUSCalculationService:
    """Test ZUS calculation service functions."""
    
    @pytest.mark.asyncio
    async def test_calculate_monthly_zus(self, test_session):
        """Test monthly ZUS calculation."""
        # Create a company profile first
        profile_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        company_profile = await create_company_profile(test_session, profile_data)
        
        # Calculate ZUS
        monthly_income = Decimal("8000.00")
        result = await calculate_monthly_zus(
            test_session, 
            company_profile.id, 
            monthly_income
        )
        
        # Verify result structure
        assert isinstance(result, ZUSCalculationResult)
        assert result.zus_base_amount == Decimal("5203.80")
        
        # Verify individual contributions (using default rates)
        assert result.emerytalne == Decimal("1015.78")  # 5203.80 * 19.52%
        assert result.rentowe == Decimal("416.30")      # 5203.80 * 8.00%
        assert result.wypadkowe == Decimal("86.90")     # 5203.80 * 1.67%
        assert result.chorobowe == Decimal("127.49")    # 5203.80 * 2.45%
        assert result.labor_fund == Decimal("127.49")   # 5203.80 * 2.45%
        assert result.fep == Decimal("5.20")            # 5203.80 * 0.10%
        
        # Verify health insurance (medium tier by default)
        expected_health = round_to_grosz(Decimal("7000") * Decimal("0.75") * Decimal("0.09"))
        assert result.health_insurance == expected_health
        assert result.health_insurance_tier == HealthInsuranceTier.MEDIUM
        
        # Verify totals
        expected_zus_total = (
            result.emerytalne + result.rentowe + result.wypadkowe + 
            result.chorobowe + result.labor_fund + result.fep
        )
        assert result.total_zus_contributions == expected_zus_total
        assert result.total_with_health == expected_zus_total + result.health_insurance
        
        # Verify metadata
        assert result.calculation_date == date.today()
        assert result.settings_effective_from is not None
    
    @pytest.mark.asyncio
    async def test_calculate_monthly_zus_no_optional_contributions(self, test_session):
        """Test ZUS calculation with optional contributions disabled."""
        # Create company profile
        profile_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        company_profile = await create_company_profile(test_session, profile_data)
        
        # Update ZUS settings to disable optional contributions
        from app.services.company_service import update_zus_settings
        await update_zus_settings(test_session, company_profile.id, {
            "is_chorobowe_active": False,
            "is_fep_active": False
        })
        
        # Calculate ZUS
        result = await calculate_monthly_zus(test_session, company_profile.id)
        
        # Verify optional contributions are zero
        assert result.chorobowe == Decimal("0.00")
        assert result.fep == Decimal("0.00")
        
        # Verify mandatory contributions are still calculated
        assert result.emerytalne > Decimal("0.00")
        assert result.rentowe > Decimal("0.00")
        assert result.wypadkowe > Decimal("0.00")
        assert result.labor_fund > Decimal("0.00")  # Labor fund is always active
    
    @pytest.mark.asyncio
    async def test_calculate_monthly_zus_company_not_found(self, test_session):
        """Test ZUS calculation when company not found."""
        with pytest.raises(ValueError, match="ZUS settings not found"):
            await calculate_monthly_zus(test_session, 999)
    
    @pytest.mark.asyncio
    async def test_calculate_yearly_zus_summary(self, test_session):
        """Test yearly ZUS summary calculation."""
        # Create company profile
        profile_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        company_profile = await create_company_profile(test_session, profile_data)
        
        # Calculate yearly summary
        year = 2024
        monthly_incomes = {
            1: Decimal("5000.00"),
            2: Decimal("6000.00"),
            3: Decimal("7000.00")
        }
        
        result = await calculate_yearly_zus_summary(
            test_session, 
            company_profile.id, 
            year, 
            monthly_incomes
        )
        
        # Verify result structure
        assert result["year"] == year
        assert "monthly_breakdown" in result
        assert "yearly_totals" in result
        assert "calculation_date" in result
        
        # Verify monthly breakdown
        monthly_breakdown = result["monthly_breakdown"]
        assert len(monthly_breakdown) == 12  # All 12 months
        
        # Check first month
        jan_data = monthly_breakdown[0]
        assert jan_data["month"] == 1
        assert "emerytalne" in jan_data
        assert "total_with_health" in jan_data
        
        # Verify yearly totals structure
        yearly_totals = result["yearly_totals"]
        assert "emerytalne" in yearly_totals
        assert "total_with_health" in yearly_totals
        
        # Verify totals are sum of monthly amounts
        total_emerytalne = sum(month["emerytalne"] for month in monthly_breakdown)
        assert abs(yearly_totals["emerytalne"] - total_emerytalne) < 0.01
    
    @pytest.mark.asyncio
    async def test_zus_calculation_result_to_dict(self, test_session):
        """Test ZUSCalculationResult to_dict method."""
        # Create company profile
        profile_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        company_profile = await create_company_profile(test_session, profile_data)
        
        # Calculate ZUS
        result = await calculate_monthly_zus(test_session, company_profile.id)
        
        # Convert to dict
        result_dict = result.to_dict()
        
        # Verify dict structure
        expected_keys = [
            "zus_base_amount", "emerytalne", "rentowe", "wypadkowe",
            "chorobowe", "labor_fund", "fep", "health_insurance",
            "health_insurance_tier", "total_zus_contributions",
            "total_with_health", "calculation_date", "settings_effective_from"
        ]
        
        for key in expected_keys:
            assert key in result_dict
        
        # Verify data types
        assert isinstance(result_dict["zus_base_amount"], float)
        assert isinstance(result_dict["emerytalne"], float)
        assert isinstance(result_dict["health_insurance_tier"], str)
        assert isinstance(result_dict["calculation_date"], str)
        
        # Verify values
        assert result_dict["zus_base_amount"] == float(result.zus_base_amount)
        assert result_dict["health_insurance_tier"] == result.health_insurance_tier.value


class TestZUSCalculationEdgeCases:
    """Test edge cases for ZUS calculations."""

    def test_calculate_contribution_with_very_small_amounts(self):
        """Test calculation with very small amounts."""
        # Test with very small base
        result = calculate_contribution_amount(Decimal("0.01"), Decimal("19.52"))
        assert result == Decimal("0.00")  # Should round to 0

        # Test with very small rate
        result = calculate_contribution_amount(Decimal("5203.80"), Decimal("0.01"))
        assert result == Decimal("0.52")  # 5203.80 * 0.01% = 0.52

    def test_calculate_contribution_with_large_amounts(self):
        """Test calculation with large amounts."""
        # Test with large base
        large_base = Decimal("999999.99")
        rate = Decimal("19.52")
        result = calculate_contribution_amount(large_base, rate)
        expected = round_to_grosz(large_base * rate / Decimal("100"))
        assert result == expected

    def test_health_insurance_edge_cases(self):
        """Test health insurance calculation edge cases."""
        # Test with zero income
        result = calculate_health_insurance(Decimal("0.00"), HealthInsuranceTier.HIGH)
        min_base = Decimal("7000") * Decimal("0.75")
        expected = round_to_grosz(min_base * Decimal("0.09"))
        assert result == expected

        # Test with very high income
        high_income = Decimal("100000.00")
        result = calculate_health_insurance(high_income, HealthInsuranceTier.HIGH)
        expected = round_to_grosz(high_income * Decimal("0.09"))
        assert result == expected
