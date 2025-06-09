"""Pydantic schemas for client-related API operations."""

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, EmailStr


class ClientCreate(BaseModel):
    """Schema for creating a client."""
    
    name: str = Field(..., max_length=255, description="Client name")
    nip: Optional[str] = Field(None, max_length=10, description="Client NIP number")
    regon: Optional[str] = Field(None, max_length=14, description="REGON number")
    
    # Address
    street: str = Field(..., max_length=255, description="Street address")
    city: str = Field(..., max_length=100, description="City")
    postal_code: str = Field(..., max_length=6, description="Postal code")
    country: str = Field(default="Poland", max_length=100, description="Country")
    
    # Contact information
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    email: Optional[str] = Field(None, max_length=255, description="Email address")
    website: Optional[str] = Field(None, max_length=255, description="Website URL")
    
    # Business details
    business_activity: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Description of client's business activity"
    )
    
    # Additional notes
    notes: Optional[str] = Field(
        None, 
        max_length=1000, 
        description="Additional notes about the client"
    )
    
    # Status
    is_active: bool = Field(default=True, description="Is client active")


class ClientUpdate(BaseModel):
    """Schema for updating a client."""
    
    name: Optional[str] = Field(None, max_length=255, description="Client name")
    nip: Optional[str] = Field(None, max_length=10, description="Client NIP number")
    regon: Optional[str] = Field(None, max_length=14, description="REGON number")
    
    # Address
    street: Optional[str] = Field(None, max_length=255, description="Street address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    postal_code: Optional[str] = Field(None, max_length=6, description="Postal code")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    
    # Contact information
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    email: Optional[str] = Field(None, max_length=255, description="Email address")
    website: Optional[str] = Field(None, max_length=255, description="Website URL")
    
    # Business details
    business_activity: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Description of client's business activity"
    )
    
    # Additional notes
    notes: Optional[str] = Field(
        None, 
        max_length=1000, 
        description="Additional notes about the client"
    )
    
    # Status
    is_active: Optional[bool] = Field(None, description="Is client active")


class ClientRead(BaseModel):
    """Schema for reading a client."""
    
    id: int
    name: str
    nip: Optional[str]
    regon: Optional[str]
    
    # Address
    street: str
    city: str
    postal_code: str
    country: str
    
    # Contact information
    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]
    
    # Business details
    business_activity: Optional[str]
    
    # Additional notes
    notes: Optional[str]
    
    # Metadata
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Status
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class ClientList(BaseModel):
    """Schema for client list with pagination."""
    
    clients: list[ClientRead]
    total: int
    page: int
    per_page: int
    total_pages: int


class ClientSummary(BaseModel):
    """Schema for client summary (minimal info for dropdowns, etc.)."""
    
    id: int
    name: str
    city: str
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)
