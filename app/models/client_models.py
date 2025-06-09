"""Client management models."""

from typing import Optional
from datetime import datetime, timezone

from sqlmodel import SQLModel, Field


class Client(SQLModel, table=True):
    """Client model for managing customer information."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Basic information
    name: str = Field(max_length=255, description="Client name")
    nip: Optional[str] = Field(default=None, max_length=10, description="Client NIP number")
    regon: Optional[str] = Field(default=None, max_length=14, description="REGON number")
    
    # Address
    street: str = Field(max_length=255, description="Street address")
    city: str = Field(max_length=100, description="City")
    postal_code: str = Field(max_length=6, description="Postal code")
    country: str = Field(default="Poland", max_length=100, description="Country")
    
    # Contact information
    phone: Optional[str] = Field(default=None, max_length=20, description="Phone number")
    email: Optional[str] = Field(default=None, max_length=255, description="Email address")
    website: Optional[str] = Field(default=None, max_length=255, description="Website URL")
    
    # Business details
    business_activity: Optional[str] = Field(
        default=None, 
        max_length=500, 
        description="Description of client's business activity"
    )
    
    # Additional notes
    notes: Optional[str] = Field(
        default=None, 
        max_length=1000, 
        description="Additional notes about the client"
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    
    # Status
    is_active: bool = Field(default=True, description="Is client active")
    

