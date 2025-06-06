"""Company profile and settings business logic."""

import re
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.company_models import CompanyProfile, TaxSettings, ZUSSettings
from app.config import settings


def validate_nip(nip: str) -> bool:
    """
    Validate Polish NIP (Tax Identification Number).

    Args:
        nip: NIP number as string

    Returns:
        True if valid, False otherwise
    """
    # Remove any non-digit characters
    nip_digits = re.sub(r'\D', '', nip)

    # Check if exactly 10 digits
    if len(nip_digits) != 10:
        return False

    # Calculate checksum using correct weights
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    checksum = sum(int(digit) * weight for digit, weight in zip(nip_digits[:9], weights))
    control_digit = checksum % 11

    # Handle special case where control digit is 10
    if control_digit == 10:
        return False

    return control_digit == int(nip_digits[9])


async def get_company_profile(session: AsyncSession) -> Optional[CompanyProfile]:
    """
    Get the company profile (assuming single company per instance).

    Args:
        session: Database session

    Returns:
        CompanyProfile if exists, None otherwise
    """
    statement = select(CompanyProfile)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def create_company_profile(
    session: AsyncSession, 
    profile_data: dict
) -> CompanyProfile:
    """
    Create a new company profile with default settings.
    
    Args:
        session: Database session
        profile_data: Company profile data
        
    Returns:
        Created CompanyProfile
        
    Raises:
        ValueError: If NIP is invalid or company already exists
    """
    # Validate NIP
    if not validate_nip(profile_data["nip"]):
        raise ValueError("Invalid NIP number")
    
    # Check if company already exists
    existing = await get_company_profile(session)
    if existing:
        raise ValueError("Company profile already exists")
    
    # Create company profile
    company_profile = CompanyProfile(**profile_data)
    session.add(company_profile)
    await session.commit()
    await session.refresh(company_profile)
    
    # Create default tax settings
    tax_settings = TaxSettings(
        company_profile_id=company_profile.id,
        vat_rate=settings.default_vat_rate,
        pit_ryczalt_rate=settings.default_pit_ryczalt_rate
    )
    session.add(tax_settings)
    
    # Create default ZUS settings
    zus_settings = ZUSSettings(
        company_profile_id=company_profile.id,
        zus_base_amount=settings.default_zus_base_amount,
        emerytalne_rate=settings.default_emerytalne_rate,
        rentowe_rate=settings.default_rentowe_rate,
        wypadkowe_rate=settings.default_wypadkowe_rate,
        chorobowe_rate=settings.default_chorobowe_rate,
        labor_fund_rate=settings.default_labor_fund_rate,
        fep_rate=settings.default_fep_rate
    )
    session.add(zus_settings)
    
    await session.commit()
    await session.refresh(company_profile)
    
    return company_profile


async def update_company_profile(
    session: AsyncSession,
    profile_id: int,
    update_data: dict
) -> Optional[CompanyProfile]:
    """
    Update company profile.
    
    Args:
        session: Database session
        profile_id: Company profile ID
        update_data: Data to update
        
    Returns:
        Updated CompanyProfile if found, None otherwise
        
    Raises:
        ValueError: If NIP is invalid
    """
    # Get existing profile
    statement = select(CompanyProfile).where(CompanyProfile.id == profile_id)
    result = await session.execute(statement)
    company_profile = result.scalar_one_or_none()
    
    if not company_profile:
        return None
    
    # Validate NIP if being updated
    if "nip" in update_data and not validate_nip(update_data["nip"]):
        raise ValueError("Invalid NIP number")
    
    # Update fields
    for field, value in update_data.items():
        if hasattr(company_profile, field):
            setattr(company_profile, field, value)
    
    await session.commit()
    await session.refresh(company_profile)
    
    return company_profile


async def get_tax_settings(session: AsyncSession, company_id: int) -> Optional[TaxSettings]:
    """Get tax settings for a company."""
    statement = select(TaxSettings).where(TaxSettings.company_profile_id == company_id)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def update_tax_settings(
    session: AsyncSession,
    company_id: int,
    update_data: dict
) -> Optional[TaxSettings]:
    """Update tax settings for a company."""
    tax_settings = await get_tax_settings(session, company_id)
    
    if not tax_settings:
        return None
    
    # Update fields
    for field, value in update_data.items():
        if hasattr(tax_settings, field):
            setattr(tax_settings, field, value)
    
    await session.commit()
    await session.refresh(tax_settings)
    
    return tax_settings


async def get_zus_settings(session: AsyncSession, company_id: int) -> Optional[ZUSSettings]:
    """Get ZUS settings for a company."""
    statement = select(ZUSSettings).where(ZUSSettings.company_profile_id == company_id)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def update_zus_settings(
    session: AsyncSession,
    company_id: int,
    update_data: dict
) -> Optional[ZUSSettings]:
    """Update ZUS settings for a company."""
    zus_settings = await get_zus_settings(session, company_id)
    
    if not zus_settings:
        return None
    
    # Update fields
    for field, value in update_data.items():
        if hasattr(zus_settings, field):
            setattr(zus_settings, field, value)
    
    await session.commit()
    await session.refresh(zus_settings)
    
    return zus_settings
