"""Invoice models for Polish accounting system."""

from enum import Enum
from typing import Optional, List
from datetime import datetime, timezone, date
from decimal import Decimal

from sqlmodel import SQLModel, Field, Relationship


class InvoiceStatus(str, Enum):
    """Invoice status enumeration."""
    
    DRAFT = "draft"
    ISSUED = "issued"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class PaymentTerms(str, Enum):
    """Payment terms enumeration."""
    
    IMMEDIATE = "immediate"
    DAYS_7 = "7_days"
    DAYS_14 = "14_days"
    DAYS_30 = "30_days"
    DAYS_60 = "60_days"
    DAYS_90 = "90_days"
    CUSTOM = "custom"


class Invoice(SQLModel, table=True):
    """Invoice model for Polish invoicing system."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Invoice identification
    invoice_number: str = Field(
        max_length=50,
        unique=True,
        index=True,
        description="Unique invoice number (e.g., FV/2024/001)"
    )
    
    # Client information
    client_id: int = Field(foreign_key="client.id", description="Client ID")
    
    # Dates
    issue_date: date = Field(description="Invoice issue date")
    due_date: date = Field(description="Payment due date")
    service_date: Optional[date] = Field(
        default=None,
        description="Service/delivery date (for Polish tax purposes)"
    )
    
    # Payment terms
    payment_terms: PaymentTerms = Field(
        default=PaymentTerms.DAYS_30,
        description="Payment terms"
    )
    payment_terms_days: Optional[int] = Field(
        default=None,
        description="Custom payment terms in days (if payment_terms is CUSTOM)"
    )
    
    # Financial totals
    total_net: Decimal = Field(
        max_digits=12,
        decimal_places=2,
        description="Total net amount (without VAT) in PLN"
    )
    total_vat: Decimal = Field(
        max_digits=12,
        decimal_places=2,
        description="Total VAT amount in PLN"
    )
    total_gross: Decimal = Field(
        max_digits=12,
        decimal_places=2,
        description="Total gross amount (including VAT) in PLN"
    )
    
    # Currency and exchange
    currency: str = Field(default="PLN", max_length=3, description="Currency code")
    exchange_rate: Optional[Decimal] = Field(
        default=None,
        max_digits=10,
        decimal_places=4,
        description="Exchange rate to PLN (if currency is not PLN)"
    )
    
    # Status and workflow
    status: InvoiceStatus = Field(default=InvoiceStatus.DRAFT, description="Invoice status")
    
    # Payment information
    payment_date: Optional[date] = Field(default=None, description="Date when invoice was paid")
    payment_method: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Payment method used"
    )
    
    # Additional information
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Additional notes or comments"
    )
    internal_notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Internal notes (not visible on invoice)"
    )
    
    # Polish specific fields
    place_of_issue: str = Field(
        max_length=100,
        description="Place where invoice was issued (required in Poland)"
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
    
    # Status tracking
    is_active: bool = Field(default=True, description="Whether invoice is active (soft delete)")
    
    # Relationships
    items: List["InvoiceItem"] = Relationship(back_populates="invoice")


class InvoiceItem(SQLModel, table=True):
    """Invoice item model for line items on invoices."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Invoice relationship
    invoice_id: int = Field(foreign_key="invoice.id", description="Invoice ID")
    
    # Item details
    description: str = Field(max_length=500, description="Item description")
    quantity: Decimal = Field(
        max_digits=10,
        decimal_places=3,
        description="Quantity"
    )
    unit: str = Field(
        default="szt.",
        max_length=20,
        description="Unit of measurement (e.g., szt., kg, godz.)"
    )
    
    # Pricing
    unit_price_net: Decimal = Field(
        max_digits=12,
        decimal_places=2,
        description="Unit price (net, without VAT) in PLN"
    )
    vat_rate: Decimal = Field(
        max_digits=5,
        decimal_places=2,
        description="VAT rate applied (%)"
    )
    
    # Calculated totals
    item_total_net: Decimal = Field(
        max_digits=12,
        decimal_places=2,
        description="Item total net amount (quantity * unit_price_net)"
    )
    item_total_vat: Decimal = Field(
        max_digits=12,
        decimal_places=2,
        description="Item total VAT amount"
    )
    item_total_gross: Decimal = Field(
        max_digits=12,
        decimal_places=2,
        description="Item total gross amount (net + VAT)"
    )
    
    # Additional item information
    item_code: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Internal item/service code"
    )
    
    # Metadata
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )
    
    # Relationships
    invoice: Invoice = Relationship(back_populates="items")


class InvoiceSummary(SQLModel):
    """Summary model for invoice statistics."""
    
    total_invoices: int = Field(description="Total number of invoices")
    total_amount_net: Decimal = Field(description="Total net amount")
    total_amount_vat: Decimal = Field(description="Total VAT amount")
    total_amount_gross: Decimal = Field(description="Total gross amount")
    
    # By status breakdown
    by_status: dict = Field(default_factory=dict, description="Breakdown by status")
    
    # By month breakdown
    by_month: dict = Field(default_factory=dict, description="Breakdown by month")
    
    # Outstanding amounts
    outstanding_amount: Decimal = Field(description="Total outstanding amount (unpaid invoices)")
    overdue_amount: Decimal = Field(description="Total overdue amount")
    
    # Date range
    date_from: Optional[date] = Field(description="Start date of summary period")
    date_to: Optional[date] = Field(description="End date of summary period")
