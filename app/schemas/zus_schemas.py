"""Pydantic schemas for ZUS calculation API operations."""

from decimal import Decimal
from typing import Optional, Dict, List
from datetime import date

from pydantic import BaseModel, Field, ConfigDict

from app.models.company_models import HealthInsuranceTier


class ZUSCalculationRequest(BaseModel):
    """Schema for ZUS calculation request."""
    
    monthly_income: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Monthly income for health insurance calculation (PLN)"
    )
    calculation_date: Optional[date] = Field(
        None,
        description="Date for calculation (defaults to today)"
    )


class ZUSCalculationResponse(BaseModel):
    """Schema for ZUS calculation response."""
    
    # Base amount
    zus_base_amount: Decimal = Field(description="ZUS base amount used for calculations")
    
    # Individual contributions
    emerytalne: Decimal = Field(description="Emerytalne (pension) contribution")
    rentowe: Decimal = Field(description="Rentowe (disability) contribution")
    wypadkowe: Decimal = Field(description="Wypadkowe (accident) contribution")
    chorobowe: Decimal = Field(description="Chorobowe (sickness) contribution")
    labor_fund: Decimal = Field(description="Labor Fund contribution")
    fep: Decimal = Field(description="FEP contribution")
    
    # Health insurance
    health_insurance: Decimal = Field(description="Health insurance contribution")
    health_insurance_tier: HealthInsuranceTier = Field(description="Health insurance tier used")
    
    # Totals
    total_zus_contributions: Decimal = Field(description="Total ZUS contributions (without health)")
    total_with_health: Decimal = Field(description="Total including health insurance")
    
    # Metadata
    calculation_date: date = Field(description="Date of calculation")
    settings_effective_from: Optional[date] = Field(description="Date from which ZUS settings are effective")
    
    model_config = ConfigDict(from_attributes=True)


class MonthlyZUSBreakdown(BaseModel):
    """Schema for monthly ZUS breakdown."""
    
    month: int = Field(ge=1, le=12, description="Month number (1-12)")
    zus_base_amount: Decimal
    emerytalne: Decimal
    rentowe: Decimal
    wypadkowe: Decimal
    chorobowe: Decimal
    labor_fund: Decimal
    fep: Decimal
    health_insurance: Decimal
    health_insurance_tier: str
    total_zus_contributions: Decimal
    total_with_health: Decimal
    calculation_date: str
    settings_effective_from: Optional[str]


class YearlyZUSTotals(BaseModel):
    """Schema for yearly ZUS totals."""
    
    emerytalne: Decimal
    rentowe: Decimal
    wypadkowe: Decimal
    chorobowe: Decimal
    labor_fund: Decimal
    fep: Decimal
    health_insurance: Decimal
    total_zus_contributions: Decimal
    total_with_health: Decimal


class YearlyZUSCalculationRequest(BaseModel):
    """Schema for yearly ZUS calculation request."""
    
    year: int = Field(ge=2020, le=2030, description="Year for calculation")
    monthly_incomes: Optional[Dict[int, Decimal]] = Field(
        None,
        description="Optional monthly incomes as {month: income} for health insurance"
    )


class YearlyZUSCalculationResponse(BaseModel):
    """Schema for yearly ZUS calculation response."""
    
    year: int = Field(description="Year of calculation")
    monthly_breakdown: List[MonthlyZUSBreakdown] = Field(description="Month-by-month breakdown")
    yearly_totals: YearlyZUSTotals = Field(description="Yearly totals")
    calculation_date: str = Field(description="Date when calculation was performed")
    
    model_config = ConfigDict(from_attributes=True)


class ZUSContributionBreakdown(BaseModel):
    """Schema for detailed ZUS contribution breakdown with rates."""
    
    contribution_name: str = Field(description="Name of the contribution")
    base_amount: Decimal = Field(description="Base amount for calculation")
    rate_percent: Decimal = Field(description="Rate as percentage")
    calculated_amount: Decimal = Field(description="Calculated contribution amount")
    is_active: bool = Field(description="Whether this contribution is active")


class DetailedZUSCalculationResponse(BaseModel):
    """Schema for detailed ZUS calculation with breakdown of each contribution."""
    
    # Basic calculation info
    calculation_date: date
    zus_base_amount: Decimal
    monthly_income: Optional[Decimal]
    
    # Detailed breakdown
    contributions: List[ZUSContributionBreakdown] = Field(description="Detailed breakdown of each contribution")
    
    # Health insurance details
    health_insurance: Decimal
    health_insurance_tier: HealthInsuranceTier
    health_insurance_base: Decimal = Field(description="Base amount used for health insurance calculation")
    
    # Summary
    total_zus_contributions: Decimal
    total_with_health: Decimal
    
    # Settings info
    settings_effective_from: Optional[date]
    
    model_config = ConfigDict(from_attributes=True)
