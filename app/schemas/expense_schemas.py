"""Pydantic schemas for expense-related API operations."""

from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.expense_models import ExpenseCategory, PaymentMethod


class ExpenseCreate(BaseModel):
    """Schema for creating an expense."""
    
    expense_date: date = Field(..., description="Date when expense occurred")
    vendor_name: str = Field(..., max_length=255, description="Name of vendor/supplier")
    description: str = Field(..., max_length=500, description="Description of expense")
    category: ExpenseCategory = Field(..., description="Expense category")
    
    # Financial details - can provide either net+VAT rate or gross amount
    amount_net: Optional[Decimal] = Field(None, ge=0, description="Net amount (without VAT) in PLN")
    vat_rate: Optional[Decimal] = Field(None, ge=0, le=100, description="VAT rate applied (%)")
    amount_gross: Optional[Decimal] = Field(None, ge=0, description="Gross amount (including VAT) in PLN")
    
    # VAT and tax details
    is_vat_deductible: bool = Field(default=True, description="Whether VAT can be deducted")
    is_tax_deductible: bool = Field(default=True, description="Whether expense is tax deductible")
    
    # Payment and documentation
    payment_method: PaymentMethod = Field(..., description="Method of payment")
    document_reference: Optional[str] = Field(None, max_length=100, description="Invoice/receipt number")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    
    @field_validator('expense_date')
    @classmethod
    def validate_expense_date(cls, v):
        """Validate expense date is not in the future."""
        if v > date.today():
            raise ValueError("Expense date cannot be in the future")
        return v
    
    def model_post_init(self, __context):
        """Validate that either net+VAT or gross amount is provided."""
        if self.amount_net is not None and self.vat_rate is not None:
            # Net + VAT rate provided - this is valid
            return
        elif self.amount_gross is not None:
            # Gross amount provided - this is valid
            return
        else:
            raise ValueError("Either provide amount_net + vat_rate OR amount_gross")


class ExpenseUpdate(BaseModel):
    """Schema for updating an expense."""
    
    expense_date: Optional[date] = Field(None, description="Date when expense occurred")
    vendor_name: Optional[str] = Field(None, max_length=255, description="Name of vendor/supplier")
    description: Optional[str] = Field(None, max_length=500, description="Description of expense")
    category: Optional[ExpenseCategory] = Field(None, description="Expense category")
    
    # Financial details
    amount_net: Optional[Decimal] = Field(None, ge=0, description="Net amount (without VAT) in PLN")
    vat_rate: Optional[Decimal] = Field(None, ge=0, le=100, description="VAT rate applied (%)")
    amount_gross: Optional[Decimal] = Field(None, ge=0, description="Gross amount (including VAT) in PLN")
    
    # VAT and tax details
    is_vat_deductible: Optional[bool] = Field(None, description="Whether VAT can be deducted")
    is_tax_deductible: Optional[bool] = Field(None, description="Whether expense is tax deductible")
    
    # Payment and documentation
    payment_method: Optional[PaymentMethod] = Field(None, description="Method of payment")
    document_reference: Optional[str] = Field(None, max_length=100, description="Invoice/receipt number")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")


class ExpenseRead(BaseModel):
    """Schema for reading an expense."""
    
    id: int
    expense_date: date
    vendor_name: str
    description: str
    category: ExpenseCategory
    
    # Financial details
    amount_net: Decimal
    vat_rate: Decimal
    vat_amount: Decimal
    amount_gross: Decimal
    
    # VAT and tax details
    is_vat_deductible: bool
    is_tax_deductible: bool
    
    # Payment and documentation
    payment_method: PaymentMethod
    document_reference: Optional[str]
    notes: Optional[str]
    
    # Metadata
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class ExpenseListResponse(BaseModel):
    """Schema for expense list response with pagination."""
    
    expenses: List[ExpenseRead]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class ExpenseSummaryResponse(BaseModel):
    """Schema for expense summary response."""
    
    total_expenses: int
    total_amount_net: Decimal
    total_vat_amount: Decimal
    total_amount_gross: Decimal
    deductible_vat_amount: Decimal
    deductible_expense_amount: Decimal
    
    # Date range
    date_from: Optional[date]
    date_to: Optional[date]
    
    # By category breakdown
    by_category: dict
    
    model_config = ConfigDict(from_attributes=True)


class ExpenseCategorySummary(BaseModel):
    """Schema for expense summary by category."""
    
    category: ExpenseCategory
    count: int
    total_net: Decimal
    total_vat: Decimal
    total_gross: Decimal


class MonthlyExpenseSummary(BaseModel):
    """Schema for monthly expense summary."""
    
    year: int
    month: int
    total_expenses: int
    total_amount_net: Decimal
    total_vat_amount: Decimal
    total_amount_gross: Decimal
    deductible_vat_amount: Decimal
    categories: List[ExpenseCategorySummary]


class YearlyExpenseSummary(BaseModel):
    """Schema for yearly expense summary."""
    
    year: int
    monthly_breakdown: List[MonthlyExpenseSummary]
    yearly_totals: ExpenseSummaryResponse
    
    model_config = ConfigDict(from_attributes=True)
