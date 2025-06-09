"""Expense tracking models."""

from enum import Enum
from typing import Optional
from datetime import datetime, timezone, date
from decimal import Decimal

from sqlmodel import SQLModel, Field


class ExpenseCategory(str, Enum):
    """Expense categories for Polish business accounting."""
    
    OFFICE_SUPPLIES = "office_supplies"
    EQUIPMENT = "equipment"
    SOFTWARE = "software"
    TRAVEL = "travel"
    MEALS = "meals"
    FUEL = "fuel"
    UTILITIES = "utilities"
    RENT = "rent"
    INSURANCE = "insurance"
    PROFESSIONAL_SERVICES = "professional_services"
    MARKETING = "marketing"
    TRAINING = "training"
    TELECOMMUNICATIONS = "telecommunications"
    BANK_FEES = "bank_fees"
    OTHER = "other"


class PaymentMethod(str, Enum):
    """Payment methods for expenses."""
    
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CARD = "card"
    ONLINE = "online"
    CHECK = "check"
    OTHER = "other"


class Expense(SQLModel, table=True):
    """Expense model for tracking business expenses."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Basic expense information
    expense_date: date = Field(description="Date when expense occurred")
    vendor_name: str = Field(max_length=255, description="Name of vendor/supplier")
    description: str = Field(max_length=500, description="Description of expense")
    category: ExpenseCategory = Field(description="Expense category")
    
    # Financial details
    amount_net: Decimal = Field(
        max_digits=10,
        decimal_places=2,
        description="Net amount (without VAT) in PLN"
    )
    vat_rate: Decimal = Field(
        max_digits=5,
        decimal_places=2,
        description="VAT rate applied (%)"
    )
    vat_amount: Decimal = Field(
        max_digits=10,
        decimal_places=2,
        description="VAT amount in PLN"
    )
    amount_gross: Decimal = Field(
        max_digits=10,
        decimal_places=2,
        description="Gross amount (including VAT) in PLN"
    )
    
    # VAT and tax details
    is_vat_deductible: bool = Field(
        default=True,
        description="Whether VAT can be deducted"
    )
    is_tax_deductible: bool = Field(
        default=True,
        description="Whether expense is tax deductible"
    )
    
    # Payment and documentation
    payment_method: PaymentMethod = Field(description="Method of payment")
    document_reference: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Invoice/receipt number or reference"
    )
    
    # Additional details
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Additional notes about the expense"
    )
    
    # Metadata
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp"
    )
    
    # Status
    is_active: bool = Field(default=True, description="Whether expense is active (soft delete)")


class ExpenseSummary(SQLModel):
    """Summary model for expense statistics."""
    
    total_expenses: int = Field(description="Total number of expenses")
    total_amount_net: Decimal = Field(description="Total net amount")
    total_vat_amount: Decimal = Field(description="Total VAT amount")
    total_amount_gross: Decimal = Field(description="Total gross amount")
    deductible_vat_amount: Decimal = Field(description="Total deductible VAT amount")
    deductible_expense_amount: Decimal = Field(description="Total tax-deductible expense amount")
    
    # By category breakdown
    by_category: dict = Field(default_factory=dict, description="Breakdown by category")
    
    # Date range
    date_from: Optional[date] = Field(description="Start date of summary period")
    date_to: Optional[date] = Field(description="End date of summary period")
