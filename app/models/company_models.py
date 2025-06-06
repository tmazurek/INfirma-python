"""Company profile and settings models."""

from decimal import Decimal
from enum import Enum
from typing import Optional
from datetime import date

from sqlmodel import SQLModel, Field, Relationship


class HealthInsuranceTier(str, Enum):
    """Health insurance tier enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaxType(str, Enum):
    """Tax type enumeration."""
    RYCZALT = "ryczalt"
    LINIOWY = "liniowy"
    PROGRESYWNY = "progresywny"


class CompanyProfile(SQLModel, table=True):
    """Company profile model."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, description="Company name")
    nip: str = Field(max_length=10, unique=True, description="NIP number")
    regon: Optional[str] = Field(default=None, max_length=14, description="REGON number")
    krs: Optional[str] = Field(default=None, max_length=10, description="KRS number")
    
    # Address
    street: str = Field(max_length=255, description="Street address")
    city: str = Field(max_length=100, description="City")
    postal_code: str = Field(max_length=6, description="Postal code")
    country: str = Field(default="Poland", max_length=100, description="Country")
    
    # Contact
    phone: Optional[str] = Field(default=None, max_length=20, description="Phone number")
    email: Optional[str] = Field(default=None, max_length=255, description="Email address")
    website: Optional[str] = Field(default=None, max_length=255, description="Website URL")
    
    # Business details
    business_activity: Optional[str] = Field(
        default=None, 
        max_length=500, 
        description="Description of business activity"
    )
    
    # Relationships
    tax_settings: Optional["TaxSettings"] = Relationship(back_populates="company_profile")
    zus_settings: Optional["ZUSSettings"] = Relationship(back_populates="company_profile")


class TaxSettings(SQLModel, table=True):
    """Tax settings model."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    company_profile_id: int = Field(foreign_key="companyprofile.id")
    
    # VAT settings
    is_vat_payer: bool = Field(default=True, description="Is VAT payer")
    vat_rate: Decimal = Field(
        default=Decimal("23.00"), 
        max_digits=5, 
        decimal_places=2,
        description="Default VAT rate (%)"
    )
    
    # Income tax settings
    tax_type: TaxType = Field(default=TaxType.RYCZALT, description="Type of income tax")
    pit_ryczalt_rate: Decimal = Field(
        default=Decimal("12.00"),
        max_digits=5,
        decimal_places=2,
        description="PIT ryczałt rate for IT services (%)"
    )
    
    # Relationship
    company_profile: CompanyProfile = Relationship(back_populates="tax_settings")


class ZUSSettings(SQLModel, table=True):
    """ZUS (Social Insurance) settings model."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    company_profile_id: int = Field(foreign_key="companyprofile.id")
    
    # Base amount for calculations
    zus_base_amount: Decimal = Field(
        default=Decimal("5203.80"),
        max_digits=10,
        decimal_places=2,
        description="ZUS base amount for calculations (PLN)"
    )
    
    # Contribution rates (%)
    emerytalne_rate: Decimal = Field(
        default=Decimal("19.52"),
        max_digits=5,
        decimal_places=2,
        description="Emerytalne (pension) contribution rate (%)"
    )
    rentowe_rate: Decimal = Field(
        default=Decimal("8.00"),
        max_digits=5,
        decimal_places=2,
        description="Rentowe (disability) contribution rate (%)"
    )
    wypadkowe_rate: Decimal = Field(
        default=Decimal("1.67"),
        max_digits=5,
        decimal_places=2,
        description="Wypadkowe (accident) contribution rate (%)"
    )
    
    # Optional contributions
    is_chorobowe_active: bool = Field(
        default=True, 
        description="Is chorobowe (sickness) contribution active"
    )
    chorobowe_rate: Decimal = Field(
        default=Decimal("2.45"),
        max_digits=5,
        decimal_places=2,
        description="Chorobowe (sickness) contribution rate (%)"
    )
    
    labor_fund_rate: Decimal = Field(
        default=Decimal("2.45"),
        max_digits=5,
        decimal_places=2,
        description="Labor Fund contribution rate (%)"
    )
    
    is_fep_active: bool = Field(
        default=True,
        description="Is FEP (Guaranteed Employee Benefits Fund) contribution active"
    )
    fep_rate: Decimal = Field(
        default=Decimal("0.10"),
        max_digits=5,
        decimal_places=2,
        description="FEP contribution rate (%)"
    )
    
    # Health insurance
    health_insurance_tier: HealthInsuranceTier = Field(
        default=HealthInsuranceTier.MEDIUM,
        description="Health insurance tier"
    )
    
    # Effective date
    effective_from: date = Field(
        default_factory=lambda: date.today(),
        description="Date from which these settings are effective"
    )
    
    # Relationship
    company_profile: CompanyProfile = Relationship(back_populates="zus_settings")
