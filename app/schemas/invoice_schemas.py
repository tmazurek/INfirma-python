"""Pydantic schemas for invoice API operations."""

from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.models.invoice_models import InvoiceStatus, PaymentTerms


class InvoiceItemCreate(BaseModel):
    """Schema for creating an invoice item."""
    
    description: str = Field(..., max_length=500, description="Item description")
    quantity: Decimal = Field(..., gt=0, description="Quantity")
    unit: str = Field(default="szt.", max_length=20, description="Unit of measurement")
    unit_price_net: Decimal = Field(..., gt=0, description="Unit price (net, without VAT)")
    vat_rate: Decimal = Field(..., ge=0, le=100, description="VAT rate (%)")
    item_code: Optional[str] = Field(None, max_length=50, description="Internal item/service code")


class InvoiceItemUpdate(BaseModel):
    """Schema for updating an invoice item."""
    
    description: Optional[str] = Field(None, max_length=500, description="Item description")
    quantity: Optional[Decimal] = Field(None, gt=0, description="Quantity")
    unit: Optional[str] = Field(None, max_length=20, description="Unit of measurement")
    unit_price_net: Optional[Decimal] = Field(None, gt=0, description="Unit price (net, without VAT)")
    vat_rate: Optional[Decimal] = Field(None, ge=0, le=100, description="VAT rate (%)")
    item_code: Optional[str] = Field(None, max_length=50, description="Internal item/service code")


class InvoiceItemRead(BaseModel):
    """Schema for reading an invoice item."""
    
    id: int
    description: str
    quantity: Decimal
    unit: str
    unit_price_net: Decimal
    vat_rate: Decimal
    item_total_net: Decimal
    item_total_vat: Decimal
    item_total_gross: Decimal
    item_code: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class InvoiceCreate(BaseModel):
    """Schema for creating an invoice."""
    
    client_id: int = Field(..., description="Client ID")
    issue_date: date = Field(..., description="Invoice issue date")
    service_date: Optional[date] = Field(None, description="Service/delivery date")
    payment_terms: PaymentTerms = Field(default=PaymentTerms.DAYS_30, description="Payment terms")
    payment_terms_days: Optional[int] = Field(
        None,
        ge=1,
        le=365,
        description="Custom payment terms in days (required if payment_terms is CUSTOM)"
    )
    place_of_issue: str = Field(..., max_length=100, description="Place where invoice was issued")
    currency: str = Field(default="PLN", max_length=3, description="Currency code")
    exchange_rate: Optional[Decimal] = Field(
        None,
        gt=0,
        description="Exchange rate to PLN (required if currency is not PLN)"
    )
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    internal_notes: Optional[str] = Field(None, max_length=1000, description="Internal notes")
    
    # Invoice items
    items: List[InvoiceItemCreate] = Field(..., min_length=1, description="Invoice items")
    
    @field_validator('issue_date')
    @classmethod
    def validate_issue_date(cls, v):
        """Validate issue date is not in the future."""
        if v > date.today():
            raise ValueError("Issue date cannot be in the future")
        return v
    
    @field_validator('service_date')
    @classmethod
    def validate_service_date(cls, v):
        """Validate service date if provided."""
        if v and v > date.today():
            raise ValueError("Service date cannot be in the future")
        return v
    
    @field_validator('payment_terms_days')
    @classmethod
    def validate_payment_terms_days(cls, v, info):
        """Validate payment_terms_days is provided when payment_terms is CUSTOM."""
        if info.data.get('payment_terms') == PaymentTerms.CUSTOM and v is None:
            raise ValueError("payment_terms_days is required when payment_terms is CUSTOM")
        if info.data.get('payment_terms') != PaymentTerms.CUSTOM and v is not None:
            raise ValueError("payment_terms_days should only be provided when payment_terms is CUSTOM")
        return v
    
    @field_validator('exchange_rate')
    @classmethod
    def validate_exchange_rate(cls, v, info):
        """Validate exchange rate is provided for non-PLN currencies."""
        currency = info.data.get('currency', 'PLN')
        if currency != 'PLN' and v is None:
            raise ValueError("exchange_rate is required for non-PLN currencies")
        if currency == 'PLN' and v is not None:
            raise ValueError("exchange_rate should not be provided for PLN currency")
        return v


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice."""
    
    client_id: Optional[int] = Field(None, description="Client ID")
    issue_date: Optional[date] = Field(None, description="Invoice issue date")
    service_date: Optional[date] = Field(None, description="Service/delivery date")
    payment_terms: Optional[PaymentTerms] = Field(None, description="Payment terms")
    payment_terms_days: Optional[int] = Field(
        None,
        ge=1,
        le=365,
        description="Custom payment terms in days"
    )
    place_of_issue: Optional[str] = Field(None, max_length=100, description="Place where invoice was issued")
    currency: Optional[str] = Field(None, max_length=3, description="Currency code")
    exchange_rate: Optional[Decimal] = Field(None, gt=0, description="Exchange rate to PLN")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    internal_notes: Optional[str] = Field(None, max_length=1000, description="Internal notes")
    
    @field_validator('issue_date')
    @classmethod
    def validate_issue_date(cls, v):
        """Validate issue date is not in the future."""
        if v and v > date.today():
            raise ValueError("Issue date cannot be in the future")
        return v
    
    @field_validator('service_date')
    @classmethod
    def validate_service_date(cls, v):
        """Validate service date if provided."""
        if v and v > date.today():
            raise ValueError("Service date cannot be in the future")
        return v


class InvoiceRead(BaseModel):
    """Schema for reading an invoice."""
    
    id: int
    invoice_number: str
    client_id: int
    issue_date: date
    due_date: date
    service_date: Optional[date]
    payment_terms: PaymentTerms
    payment_terms_days: Optional[int]
    total_net: Decimal
    total_vat: Decimal
    total_gross: Decimal
    currency: str
    exchange_rate: Optional[Decimal]
    status: InvoiceStatus
    payment_date: Optional[date]
    payment_method: Optional[str]
    notes: Optional[str]
    internal_notes: Optional[str]
    place_of_issue: str
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool
    
    # Include items
    items: List[InvoiceItemRead] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)


class InvoiceListItem(BaseModel):
    """Schema for invoice list items (without full details)."""
    
    id: int
    invoice_number: str
    client_id: int
    issue_date: date
    due_date: date
    total_gross: Decimal
    currency: str
    status: InvoiceStatus
    payment_date: Optional[date]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class InvoiceStatusUpdate(BaseModel):
    """Schema for updating invoice status."""
    
    status: InvoiceStatus = Field(..., description="New invoice status")
    payment_date: Optional[date] = Field(None, description="Payment date (required for PAID status)")
    payment_method: Optional[str] = Field(None, max_length=100, description="Payment method")
    
    @field_validator('payment_date')
    @classmethod
    def validate_payment_date(cls, v, info):
        """Validate payment date is provided when status is PAID."""
        status = info.data.get('status')
        if status == InvoiceStatus.PAID and v is None:
            raise ValueError("payment_date is required when status is PAID")
        if v and v > date.today():
            raise ValueError("Payment date cannot be in the future")
        return v


class InvoiceSummaryResponse(BaseModel):
    """Schema for invoice summary response."""
    
    total_invoices: int
    total_amount_net: Decimal
    total_amount_vat: Decimal
    total_amount_gross: Decimal
    by_status: dict
    by_month: dict
    outstanding_amount: Decimal
    overdue_amount: Decimal
    date_from: Optional[date]
    date_to: Optional[date]
    
    model_config = ConfigDict(from_attributes=True)


class InvoiceFilters(BaseModel):
    """Schema for invoice filtering parameters."""
    
    status: Optional[InvoiceStatus] = Field(None, description="Filter by status")
    client_id: Optional[int] = Field(None, description="Filter by client")
    date_from: Optional[date] = Field(None, description="Filter by issue date from")
    date_to: Optional[date] = Field(None, description="Filter by issue date to")
    due_date_from: Optional[date] = Field(None, description="Filter by due date from")
    due_date_to: Optional[date] = Field(None, description="Filter by due date to")
    currency: Optional[str] = Field(None, max_length=3, description="Filter by currency")
    min_amount: Optional[Decimal] = Field(None, ge=0, description="Minimum total amount")
    max_amount: Optional[Decimal] = Field(None, ge=0, description="Maximum total amount")
    search: Optional[str] = Field(None, max_length=100, description="Search in invoice number or notes")
