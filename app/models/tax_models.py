"""Tax calculation models and result structures."""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import date
from decimal import Decimal

from sqlmodel import SQLModel, Field


class TaxPeriod(str, Enum):
    """Tax calculation period types."""
    
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class VATCalculationResult(SQLModel):
    """Result of VAT calculation with detailed breakdown."""
    
    # Period information
    calculation_date: date = Field(description="Date of calculation")
    period_start: date = Field(description="Start date of calculation period")
    period_end: date = Field(description="End date of calculation period")
    period_type: TaxPeriod = Field(description="Type of calculation period")
    
    # VAT collected (from invoices/income)
    total_income_net: Decimal = Field(description="Total income (net amount)")
    total_income_vat: Decimal = Field(description="Total VAT collected from income")
    total_income_gross: Decimal = Field(description="Total income (gross amount)")
    
    # VAT paid (from expenses)
    total_expenses_net: Decimal = Field(description="Total expenses (net amount)")
    total_expenses_vat: Decimal = Field(description="Total VAT paid on expenses")
    total_expenses_gross: Decimal = Field(description="Total expenses (gross amount)")
    
    # VAT deductible (only from VAT-deductible expenses)
    deductible_expenses_vat: Decimal = Field(description="VAT that can be deducted")
    
    # VAT calculation
    vat_to_pay: Decimal = Field(description="Net VAT amount to pay (or refund if negative)")
    vat_rate_used: Decimal = Field(description="VAT rate used for calculations (%)")
    
    # Metadata
    is_vat_payer: bool = Field(description="Whether company is VAT payer")
    company_profile_id: int = Field(description="Company profile ID")


class PITCalculationResult(SQLModel):
    """Result of PIT (Personal Income Tax) calculation."""
    
    # Period information
    calculation_date: date = Field(description="Date of calculation")
    period_start: date = Field(description="Start date of calculation period")
    period_end: date = Field(description="End date of calculation period")
    period_type: TaxPeriod = Field(description="Type of calculation period")
    
    # Income information
    total_income_net: Decimal = Field(description="Total income (net amount)")
    total_income_gross: Decimal = Field(description="Total income (gross amount)")
    
    # Deductible expenses
    total_deductible_expenses: Decimal = Field(description="Total tax-deductible expenses")
    
    # Tax calculation
    taxable_income: Decimal = Field(description="Income subject to tax (after deductions)")
    pit_amount: Decimal = Field(description="PIT amount to pay")
    pit_rate_used: Decimal = Field(description="PIT rate used for calculations (%)")
    tax_type_used: str = Field(description="Tax type used (ryczalt/liniowy/progresywny)")
    
    # ZUS deductions (for liniowy/progresywny)
    zus_deductible_amount: Optional[Decimal] = Field(
        default=None,
        description="ZUS contributions that can be deducted from tax"
    )
    
    # Metadata
    company_profile_id: int = Field(description="Company profile ID")


class MonthlyTaxSummary(SQLModel):
    """Monthly tax summary combining VAT and PIT."""
    
    # Period information
    year: int = Field(description="Year of calculation")
    month: int = Field(description="Month of calculation")
    calculation_date: date = Field(description="Date when calculation was performed")
    
    # VAT summary
    vat_calculation: VATCalculationResult = Field(description="VAT calculation details")
    
    # PIT summary
    pit_calculation: PITCalculationResult = Field(description="PIT calculation details")
    
    # ZUS summary (from existing ZUS service)
    zus_total_contributions: Decimal = Field(description="Total ZUS contributions")
    zus_health_insurance: Decimal = Field(description="Health insurance amount")
    zus_total_with_health: Decimal = Field(description="Total ZUS + health insurance")
    
    # Overall summary
    total_taxes_to_pay: Decimal = Field(description="Total taxes to pay (VAT + PIT)")
    total_social_contributions: Decimal = Field(description="Total social contributions (ZUS)")
    total_monthly_obligations: Decimal = Field(description="Total monthly obligations (taxes + ZUS)")
    
    # Net income after all obligations
    net_income_after_taxes: Decimal = Field(description="Net income after all taxes and contributions")
    
    # Metadata
    company_profile_id: int = Field(description="Company profile ID")


class YearlyTaxSummary(SQLModel):
    """Yearly tax summary with month-by-month breakdown."""
    
    year: int = Field(description="Year of calculation")
    calculation_date: date = Field(description="Date when calculation was performed")
    
    # Monthly breakdown
    monthly_summaries: list = Field(description="List of monthly tax summaries")
    
    # Yearly totals
    yearly_vat_to_pay: Decimal = Field(description="Total VAT to pay for the year")
    yearly_pit_to_pay: Decimal = Field(description="Total PIT to pay for the year")
    yearly_zus_contributions: Decimal = Field(description="Total ZUS contributions for the year")
    yearly_total_obligations: Decimal = Field(description="Total yearly obligations")
    
    # Income summary
    yearly_income_gross: Decimal = Field(description="Total yearly income (gross)")
    yearly_income_net: Decimal = Field(description="Total yearly income (net)")
    yearly_expenses_total: Decimal = Field(description="Total yearly expenses")
    yearly_net_profit: Decimal = Field(description="Net profit after all obligations")
    
    # Metadata
    company_profile_id: int = Field(description="Company profile ID")
