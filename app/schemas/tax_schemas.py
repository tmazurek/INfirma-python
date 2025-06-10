"""Pydantic schemas for tax calculation API operations."""

from typing import Optional, List
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict

from app.models.tax_models import TaxPeriod


class TaxCalculationRequest(BaseModel):
    """Schema for tax calculation request."""
    
    year: int = Field(..., ge=2020, le=2030, description="Year for calculation")
    month: int = Field(..., ge=1, le=12, description="Month for calculation")
    monthly_income_gross: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Monthly gross income (PLN) - if not provided, will be calculated from invoices"
    )
    calculation_date: Optional[date] = Field(
        None,
        description="Date for calculation (defaults to today)"
    )


class VATCalculationResponse(BaseModel):
    """Schema for VAT calculation response."""
    
    # Period information
    calculation_date: date
    period_start: date
    period_end: date
    period_type: TaxPeriod
    
    # VAT collected (from invoices/income)
    total_income_net: Decimal
    total_income_vat: Decimal
    total_income_gross: Decimal
    
    # VAT paid (from expenses)
    total_expenses_net: Decimal
    total_expenses_vat: Decimal
    total_expenses_gross: Decimal
    
    # VAT deductible
    deductible_expenses_vat: Decimal
    
    # VAT calculation
    vat_to_pay: Decimal
    vat_rate_used: Decimal
    
    # Metadata
    is_vat_payer: bool
    company_profile_id: int
    
    model_config = ConfigDict(from_attributes=True)


class PITCalculationResponse(BaseModel):
    """Schema for PIT calculation response."""
    
    # Period information
    calculation_date: date
    period_start: date
    period_end: date
    period_type: TaxPeriod
    
    # Income information
    total_income_net: Decimal
    total_income_gross: Decimal
    
    # Deductible expenses
    total_deductible_expenses: Decimal
    
    # Tax calculation
    taxable_income: Decimal
    pit_amount: Decimal
    pit_rate_used: Decimal
    tax_type_used: str
    
    # ZUS deductions (for liniowy/progresywny)
    zus_deductible_amount: Optional[Decimal]
    
    # Metadata
    company_profile_id: int
    
    model_config = ConfigDict(from_attributes=True)


class MonthlyTaxSummaryResponse(BaseModel):
    """Schema for monthly tax summary response."""
    
    # Period information
    year: int
    month: int
    calculation_date: date
    
    # VAT summary
    vat_calculation: VATCalculationResponse
    
    # PIT summary
    pit_calculation: PITCalculationResponse
    
    # ZUS summary
    zus_total_contributions: Decimal
    zus_health_insurance: Decimal
    zus_total_with_health: Decimal
    
    # Overall summary
    total_taxes_to_pay: Decimal
    total_social_contributions: Decimal
    total_monthly_obligations: Decimal
    
    # Net income after all obligations
    net_income_after_taxes: Decimal
    
    # Metadata
    company_profile_id: int
    
    model_config = ConfigDict(from_attributes=True)


class TaxBreakdownItem(BaseModel):
    """Schema for individual tax breakdown item."""
    
    tax_name: str = Field(description="Name of the tax/contribution")
    amount: Decimal = Field(description="Amount to pay")
    rate_percent: Optional[Decimal] = Field(description="Rate as percentage")
    base_amount: Optional[Decimal] = Field(description="Base amount for calculation")
    is_deductible: Optional[bool] = Field(description="Whether this is tax deductible")
    category: str = Field(description="Category: VAT, PIT, ZUS, or Health")


class DetailedTaxCalculationResponse(BaseModel):
    """Schema for detailed tax calculation with breakdown."""
    
    # Basic calculation info
    calculation_date: date
    year: int
    month: int
    monthly_income_gross: Optional[Decimal]
    
    # Detailed breakdown
    tax_breakdown: List[TaxBreakdownItem] = Field(description="Detailed breakdown of all taxes and contributions")
    
    # Summary totals
    total_vat: Decimal
    total_pit: Decimal
    total_zus: Decimal
    total_health_insurance: Decimal
    total_taxes: Decimal
    total_social_contributions: Decimal
    total_obligations: Decimal
    
    # Net income
    gross_income: Decimal
    net_income_after_taxes: Decimal
    effective_tax_rate: Decimal = Field(description="Effective tax rate as percentage")
    
    # Settings used
    vat_rate_used: Decimal
    pit_rate_used: Decimal
    tax_type_used: str
    is_vat_payer: bool
    
    model_config = ConfigDict(from_attributes=True)


class YearlyTaxSummaryResponse(BaseModel):
    """Schema for yearly tax summary response."""
    
    year: int
    calculation_date: date
    
    # Monthly breakdown
    monthly_summaries: List[MonthlyTaxSummaryResponse]
    
    # Yearly totals
    yearly_vat_to_pay: Decimal
    yearly_pit_to_pay: Decimal
    yearly_zus_contributions: Decimal
    yearly_total_obligations: Decimal
    
    # Income summary
    yearly_income_gross: Decimal
    yearly_income_net: Decimal
    yearly_expenses_total: Decimal
    yearly_net_profit: Decimal
    
    # Effective rates
    effective_vat_rate: Decimal
    effective_pit_rate: Decimal
    effective_total_rate: Decimal
    
    # Metadata
    company_profile_id: int
    
    model_config = ConfigDict(from_attributes=True)


class TaxComparisonRequest(BaseModel):
    """Schema for tax comparison between different tax types."""
    
    annual_income: Decimal = Field(..., gt=0, description="Annual income for comparison")
    annual_expenses: Optional[Decimal] = Field(None, ge=0, description="Annual deductible expenses")
    include_zus: bool = Field(default=True, description="Include ZUS contributions in comparison")


class TaxComparisonItem(BaseModel):
    """Schema for tax comparison item."""
    
    tax_type: str
    tax_type_name: str
    annual_pit: Decimal
    annual_zus: Decimal
    annual_health_insurance: Decimal
    total_annual_obligations: Decimal
    net_income_after_taxes: Decimal
    effective_rate: Decimal


class TaxComparisonResponse(BaseModel):
    """Schema for tax comparison response."""
    
    annual_income: Decimal
    annual_expenses: Decimal
    calculation_date: date
    
    # Comparison results
    tax_options: List[TaxComparisonItem]
    
    # Recommendations
    recommended_option: str = Field(description="Recommended tax type based on lowest total obligations")
    potential_savings: Decimal = Field(description="Potential annual savings with recommended option")
    
    model_config = ConfigDict(from_attributes=True)
