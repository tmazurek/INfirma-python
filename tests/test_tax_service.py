"""Tests for tax calculation service functions."""

import pytest
from decimal import Decimal
from datetime import date

from app.services.tax_service import (
    round_to_grosz,
    calculate_monthly_vat,
    calculate_monthly_pit,
    calculate_monthly_tax_summary,
    calculate_pit_for_income_and_type
)
from app.services.company_service import create_company_profile
from app.services.expense_service import create_expense
from app.models.company_models import TaxType
from app.models.expense_models import ExpenseCategory, PaymentMethod


class TestTaxCalculationUtils:
    """Test tax calculation utility functions."""
    
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
    
    def test_calculate_pit_for_income_and_type_ryczalt(self):
        """Test PIT calculation for ryczałt."""
        income = Decimal("100000.00")
        pit_rate = Decimal("12.00")
        
        pit_amount, effective_rate = calculate_pit_for_income_and_type(
            income, TaxType.RYCZALT, pit_rate
        )
        
        assert pit_amount == Decimal("12000.00")  # 100,000 * 12%
        assert effective_rate == pit_rate
    
    def test_calculate_pit_for_income_and_type_liniowy(self):
        """Test PIT calculation for liniowy (19%)."""
        income = Decimal("100000.00")
        zus_deductible = Decimal("20000.00")
        
        pit_amount, effective_rate = calculate_pit_for_income_and_type(
            income, TaxType.LINIOWY, Decimal("19.00"), zus_deductible
        )
        
        # Taxable income: 100,000 - 20,000 = 80,000
        # PIT: 80,000 * 19% = 15,200
        assert pit_amount == Decimal("15200.00")
        assert effective_rate == Decimal("19.00")
    
    def test_calculate_pit_for_income_and_type_progresywny(self):
        """Test PIT calculation for progresywny."""
        # Test income below threshold
        income_low = Decimal("100000.00")
        zus_deductible = Decimal("20000.00")
        
        pit_amount, effective_rate = calculate_pit_for_income_and_type(
            income_low, TaxType.PROGRESYWNY, Decimal("12.00"), zus_deductible
        )
        
        # Taxable income: 100,000 - 20,000 = 80,000 (below 120,000 threshold)
        # PIT: 80,000 * 12% = 9,600
        assert pit_amount == Decimal("9600.00")
        assert effective_rate == Decimal("12.00")
        
        # Test income above threshold
        income_high = Decimal("200000.00")
        
        pit_amount, effective_rate = calculate_pit_for_income_and_type(
            income_high, TaxType.PROGRESYWNY, Decimal("12.00"), zus_deductible
        )
        
        # Taxable income: 200,000 - 20,000 = 180,000
        # PIT: 120,000 * 12% + (180,000 - 120,000) * 32% = 14,400 + 19,200 = 33,600
        assert pit_amount == Decimal("33600.00")


class TestVATCalculation:
    """Test VAT calculation functions."""
    
    @pytest.mark.asyncio
    async def test_calculate_monthly_vat_no_expenses(self, test_session):
        """Test VAT calculation with no expenses."""
        # Create company profile
        profile_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        company_profile = await create_company_profile(test_session, profile_data)
        
        # Calculate VAT for June 2024
        result = await calculate_monthly_vat(
            test_session, company_profile.id, 2024, 6
        )
        
        # Verify result structure
        assert result.calculation_date == date.today()
        assert result.period_start == date(2024, 6, 1)
        assert result.period_end == date(2024, 6, 30)
        assert result.company_profile_id == company_profile.id
        
        # With no income or expenses, VAT should be 0
        assert result.total_income_net == Decimal("0.00")
        assert result.total_expenses_net == Decimal("0.00")
        assert result.vat_to_pay == Decimal("0.00")
        assert result.is_vat_payer is True  # Default setting
    
    @pytest.mark.asyncio
    async def test_calculate_monthly_vat_with_expenses(self, test_session):
        """Test VAT calculation with expenses."""
        # Create company profile
        profile_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        company_profile = await create_company_profile(test_session, profile_data)
        
        # Create test expenses for June 2024
        expense_data_1 = {
            "expense_date": date(2024, 6, 15),
            "vendor_name": "Vendor 1",
            "description": "Office supplies",
            "category": ExpenseCategory.OFFICE_SUPPLIES,
            "amount_net": Decimal("100.00"),
            "vat_rate": Decimal("23.00"),
            "payment_method": PaymentMethod.CASH,
            "is_vat_deductible": True
        }
        
        expense_data_2 = {
            "expense_date": date(2024, 6, 20),
            "vendor_name": "Vendor 2",
            "description": "Software",
            "category": ExpenseCategory.SOFTWARE,
            "amount_net": Decimal("200.00"),
            "vat_rate": Decimal("23.00"),
            "payment_method": PaymentMethod.CARD,
            "is_vat_deductible": False  # Not VAT deductible
        }
        
        await create_expense(test_session, expense_data_1)
        await create_expense(test_session, expense_data_2)
        
        # Calculate VAT
        result = await calculate_monthly_vat(
            test_session, company_profile.id, 2024, 6
        )
        
        # Verify calculations
        assert result.total_expenses_net == Decimal("300.00")  # 100 + 200
        assert result.total_expenses_vat == Decimal("69.00")   # 23 + 46
        assert result.total_expenses_gross == Decimal("369.00") # 123 + 246
        assert result.deductible_expenses_vat == Decimal("23.00")  # Only first expense
        
        # VAT to pay = income VAT - deductible expense VAT = 0 - 23 = -23 (refund)
        assert result.vat_to_pay == Decimal("-23.00")


class TestPITCalculation:
    """Test PIT calculation functions."""
    
    @pytest.mark.asyncio
    async def test_calculate_monthly_pit_ryczalt(self, test_session):
        """Test PIT calculation for ryczałt."""
        # Create company profile
        profile_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        company_profile = await create_company_profile(test_session, profile_data)
        
        # Calculate PIT for June 2024 with 10,000 PLN gross income
        monthly_income_gross = Decimal("12300.00")  # 10,000 net + 23% VAT
        
        result = await calculate_monthly_pit(
            test_session, company_profile.id, 2024, 6, monthly_income_gross
        )
        
        # Verify result structure
        assert result.calculation_date == date.today()
        assert result.period_start == date(2024, 6, 1)
        assert result.period_end == date(2024, 6, 30)
        assert result.company_profile_id == company_profile.id
        
        # Verify calculations
        assert result.total_income_gross == monthly_income_gross
        assert result.total_income_net == Decimal("10000.00")  # 12300 / 1.23
        assert result.tax_type_used == "ryczalt"
        
        # PIT for ryczałt: 10,000 * 12% = 1,200
        assert result.pit_amount == Decimal("1200.00")
        assert result.zus_deductible_amount is None  # No ZUS deduction for ryczałt
    
    @pytest.mark.asyncio
    async def test_calculate_monthly_pit_with_expenses(self, test_session):
        """Test PIT calculation with deductible expenses."""
        # Create company profile
        profile_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        company_profile = await create_company_profile(test_session, profile_data)
        
        # Create tax-deductible expense
        expense_data = {
            "expense_date": date(2024, 6, 15),
            "vendor_name": "Vendor",
            "description": "Business expense",
            "category": ExpenseCategory.OFFICE_SUPPLIES,
            "amount_net": Decimal("2000.00"),
            "vat_rate": Decimal("23.00"),
            "payment_method": PaymentMethod.CASH,
            "is_tax_deductible": True
        }
        
        await create_expense(test_session, expense_data)
        
        # Calculate PIT
        monthly_income_gross = Decimal("12300.00")
        
        result = await calculate_monthly_pit(
            test_session, company_profile.id, 2024, 6, monthly_income_gross
        )
        
        # Verify deductible expenses are included
        assert result.total_deductible_expenses == Decimal("2000.00")
        
        # Taxable income: 10,000 - 2,000 = 8,000
        assert result.taxable_income == Decimal("8000.00")
        
        # PIT for ryczałt: 10,000 * 12% = 1,200 (expenses don't reduce ryczałt base)
        assert result.pit_amount == Decimal("1200.00")


class TestMonthlyTaxSummary:
    """Test monthly tax summary calculation."""
    
    @pytest.mark.asyncio
    async def test_calculate_monthly_tax_summary(self, test_session):
        """Test comprehensive monthly tax summary."""
        # Create company profile
        profile_data = {
            "name": "Test Company",
            "nip": "1234563224",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        company_profile = await create_company_profile(test_session, profile_data)
        
        # Calculate tax summary for June 2024
        monthly_income_gross = Decimal("12300.00")
        
        result = await calculate_monthly_tax_summary(
            test_session, company_profile.id, 2024, 6, monthly_income_gross
        )
        
        # Verify result structure
        assert result.year == 2024
        assert result.month == 6
        assert result.company_profile_id == company_profile.id
        
        # Verify VAT calculation is included
        assert hasattr(result, 'vat_calculation')
        assert result.vat_calculation.total_income_gross == Decimal("0.00")  # No invoices yet
        
        # Verify PIT calculation is included
        assert hasattr(result, 'pit_calculation')
        assert result.pit_calculation.total_income_gross == monthly_income_gross
        assert result.pit_calculation.pit_amount == Decimal("1200.00")  # 10,000 * 12%
        
        # Verify ZUS calculations are included
        assert result.zus_total_contributions > Decimal("0.00")
        assert result.zus_health_insurance > Decimal("0.00")
        assert result.zus_total_with_health > Decimal("0.00")
        
        # Verify totals
        assert result.total_taxes_to_pay >= result.pit_calculation.pit_amount
        assert result.total_social_contributions == result.zus_total_with_health
        assert result.total_monthly_obligations == (
            result.total_taxes_to_pay + result.total_social_contributions
        )
        
        # Net income should be gross income minus all obligations
        expected_net = monthly_income_gross - result.total_monthly_obligations
        assert result.net_income_after_taxes == expected_net


class TestTaxCalculationEdgeCases:
    """Test edge cases for tax calculations."""
    
    @pytest.mark.asyncio
    async def test_calculate_vat_company_not_found(self, test_session):
        """Test VAT calculation when company not found."""
        with pytest.raises(ValueError, match="Tax settings not found"):
            await calculate_monthly_vat(test_session, 999, 2024, 6)
    
    @pytest.mark.asyncio
    async def test_calculate_pit_company_not_found(self, test_session):
        """Test PIT calculation when company not found."""
        with pytest.raises(ValueError, match="Tax settings not found"):
            await calculate_monthly_pit(test_session, 999, 2024, 6)
    
    def test_calculate_pit_zero_income(self):
        """Test PIT calculation with zero income."""
        pit_amount, effective_rate = calculate_pit_for_income_and_type(
            Decimal("0.00"), TaxType.RYCZALT, Decimal("12.00")
        )
        
        assert pit_amount == Decimal("0.00")
        assert effective_rate == Decimal("12.00")
    
    def test_calculate_pit_with_high_zus_deduction(self):
        """Test PIT calculation where ZUS deduction exceeds income."""
        income = Decimal("5000.00")
        zus_deductible = Decimal("10000.00")  # Higher than income
        
        pit_amount, effective_rate = calculate_pit_for_income_and_type(
            income, TaxType.LINIOWY, Decimal("19.00"), zus_deductible
        )
        
        # Taxable income should be 0 (not negative)
        assert pit_amount == Decimal("0.00")
        assert effective_rate == Decimal("19.00")
