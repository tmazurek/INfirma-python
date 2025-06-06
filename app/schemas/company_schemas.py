"""Pydantic schemas for company-related API operations."""

from decimal import Decimal
from typing import Optional
from datetime import date

from pydantic import BaseModel, Field, ConfigDict

from app.models.company_models import HealthInsuranceTier, TaxType


class CompanyProfileCreate(BaseModel):
    """Schema for creating a company profile."""
    
    name: str = Field(..., max_length=255, description="Company name")
    nip: str = Field(..., max_length=10, description="NIP number")
    regon: Optional[str] = Field(None, max_length=14, description="REGON number")
    krs: Optional[str] = Field(None, max_length=10, description="KRS number")
    
    # Address
    street: str = Field(..., max_length=255, description="Street address")
    city: str = Field(..., max_length=100, description="City")
    postal_code: str = Field(..., max_length=6, description="Postal code")
    country: str = Field(default="Poland", max_length=100, description="Country")
    
    # Contact
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    email: Optional[str] = Field(None, max_length=255, description="Email address")
    website: Optional[str] = Field(None, max_length=255, description="Website URL")
    
    # Business details
    business_activity: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Description of business activity"
    )


class CompanyProfileUpdate(BaseModel):
    """Schema for updating a company profile."""
    
    name: Optional[str] = Field(None, max_length=255, description="Company name")
    nip: Optional[str] = Field(None, max_length=10, description="NIP number")
    regon: Optional[str] = Field(None, max_length=14, description="REGON number")
    krs: Optional[str] = Field(None, max_length=10, description="KRS number")
    
    # Address
    street: Optional[str] = Field(None, max_length=255, description="Street address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    postal_code: Optional[str] = Field(None, max_length=6, description="Postal code")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    
    # Contact
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    email: Optional[str] = Field(None, max_length=255, description="Email address")
    website: Optional[str] = Field(None, max_length=255, description="Website URL")
    
    # Business details
    business_activity: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Description of business activity"
    )


class CompanyProfileRead(BaseModel):
    """Schema for reading a company profile."""
    
    id: int
    name: str
    nip: str
    regon: Optional[str]
    krs: Optional[str]
    
    # Address
    street: str
    city: str
    postal_code: str
    country: str
    
    # Contact
    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]
    
    # Business details
    business_activity: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


class TaxSettingsUpdate(BaseModel):
    """Schema for updating tax settings."""
    
    is_vat_payer: Optional[bool] = Field(None, description="Is VAT payer")
    vat_rate: Optional[Decimal] = Field(
        None, 
        ge=0, 
        le=100, 
        description="Default VAT rate (%)"
    )
    tax_type: Optional[TaxType] = Field(None, description="Type of income tax")
    pit_ryczalt_rate: Optional[Decimal] = Field(
        None,
        ge=0,
        le=100,
        description="PIT ryczałt rate for IT services (%)"
    )


class TaxSettingsRead(BaseModel):
    """Schema for reading tax settings."""
    
    id: int
    company_profile_id: int
    is_vat_payer: bool
    vat_rate: Decimal
    tax_type: TaxType
    pit_ryczalt_rate: Decimal
    
    model_config = ConfigDict(from_attributes=True)


class ZUSSettingsUpdate(BaseModel):
    """Schema for updating ZUS settings."""
    
    zus_base_amount: Optional[Decimal] = Field(
        None,
        gt=0,
        description="ZUS base amount for calculations (PLN)"
    )
    emerytalne_rate: Optional[Decimal] = Field(
        None,
        ge=0,
        le=100,
        description="Emerytalne (pension) contribution rate (%)"
    )
    rentowe_rate: Optional[Decimal] = Field(
        None,
        ge=0,
        le=100,
        description="Rentowe (disability) contribution rate (%)"
    )
    wypadkowe_rate: Optional[Decimal] = Field(
        None,
        ge=0,
        le=100,
        description="Wypadkowe (accident) contribution rate (%)"
    )
    is_chorobowe_active: Optional[bool] = Field(
        None, 
        description="Is chorobowe (sickness) contribution active"
    )
    chorobowe_rate: Optional[Decimal] = Field(
        None,
        ge=0,
        le=100,
        description="Chorobowe (sickness) contribution rate (%)"
    )
    labor_fund_rate: Optional[Decimal] = Field(
        None,
        ge=0,
        le=100,
        description="Labor Fund contribution rate (%)"
    )
    is_fep_active: Optional[bool] = Field(
        None,
        description="Is FEP contribution active"
    )
    fep_rate: Optional[Decimal] = Field(
        None,
        ge=0,
        le=100,
        description="FEP contribution rate (%)"
    )
    health_insurance_tier: Optional[HealthInsuranceTier] = Field(
        None,
        description="Health insurance tier"
    )
    effective_from: Optional[date] = Field(
        None,
        description="Date from which these settings are effective"
    )


class ZUSSettingsRead(BaseModel):
    """Schema for reading ZUS settings."""
    
    id: int
    company_profile_id: int
    zus_base_amount: Decimal
    emerytalne_rate: Decimal
    rentowe_rate: Decimal
    wypadkowe_rate: Decimal
    is_chorobowe_active: bool
    chorobowe_rate: Decimal
    labor_fund_rate: Decimal
    is_fep_active: bool
    fep_rate: Decimal
    health_insurance_tier: HealthInsuranceTier
    effective_from: date
    
    model_config = ConfigDict(from_attributes=True)
