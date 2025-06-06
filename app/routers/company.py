"""Company profile and settings API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.company_models import CompanyProfile, TaxSettings, ZUSSettings
from app.schemas.company_schemas import (
    CompanyProfileCreate,
    CompanyProfileUpdate,
    CompanyProfileRead,
    TaxSettingsUpdate,
    TaxSettingsRead,
    ZUSSettingsUpdate,
    ZUSSettingsRead,
)
from app.services import company_service

router = APIRouter(prefix="/api/v1/company", tags=["company"])


@router.post("/profile/", response_model=CompanyProfileRead, status_code=status.HTTP_201_CREATED)
async def create_company_profile(
    profile_data: CompanyProfileCreate,
    session: AsyncSession = Depends(get_session)
) -> CompanyProfile:
    """Create a new company profile with default settings."""
    try:
        company_profile = await company_service.create_company_profile(
            session, profile_data.model_dump()
        )
        return company_profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/profile/", response_model=Optional[CompanyProfileRead])
async def get_company_profile(
    session: AsyncSession = Depends(get_session)
) -> Optional[CompanyProfile]:
    """Get the company profile."""
    return await company_service.get_company_profile(session)


@router.put("/profile/", response_model=CompanyProfileRead)
async def update_company_profile(
    profile_data: CompanyProfileUpdate,
    session: AsyncSession = Depends(get_session)
) -> CompanyProfile:
    """Update the company profile."""
    # Get existing profile
    existing_profile = await company_service.get_company_profile(session)
    if not existing_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )
    
    try:
        # Update with only provided fields
        update_data = profile_data.model_dump(exclude_unset=True)
        updated_profile = await company_service.update_company_profile(
            session, existing_profile.id, update_data
        )
        
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company profile not found"
            )
        
        return updated_profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/settings/tax/", response_model=Optional[TaxSettingsRead])
async def get_tax_settings(
    session: AsyncSession = Depends(get_session)
) -> Optional[TaxSettings]:
    """Get tax settings for the company."""
    company_profile = await company_service.get_company_profile(session)
    if not company_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )
    
    return await company_service.get_tax_settings(session, company_profile.id)


@router.put("/settings/tax/", response_model=TaxSettingsRead)
async def update_tax_settings(
    settings_data: TaxSettingsUpdate,
    session: AsyncSession = Depends(get_session)
) -> TaxSettings:
    """Update tax settings for the company."""
    company_profile = await company_service.get_company_profile(session)
    if not company_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )
    
    update_data = settings_data.model_dump(exclude_unset=True)
    updated_settings = await company_service.update_tax_settings(
        session, company_profile.id, update_data
    )
    
    if not updated_settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tax settings not found"
        )
    
    return updated_settings


@router.get("/settings/zus/", response_model=Optional[ZUSSettingsRead])
async def get_zus_settings(
    session: AsyncSession = Depends(get_session)
) -> Optional[ZUSSettings]:
    """Get ZUS settings for the company."""
    company_profile = await company_service.get_company_profile(session)
    if not company_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )
    
    return await company_service.get_zus_settings(session, company_profile.id)


@router.put("/settings/zus/", response_model=ZUSSettingsRead)
async def update_zus_settings(
    settings_data: ZUSSettingsUpdate,
    session: AsyncSession = Depends(get_session)
) -> ZUSSettings:
    """Update ZUS settings for the company."""
    company_profile = await company_service.get_company_profile(session)
    if not company_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )
    
    update_data = settings_data.model_dump(exclude_unset=True)
    updated_settings = await company_service.update_zus_settings(
        session, company_profile.id, update_data
    )
    
    if not updated_settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ZUS settings not found"
        )
    
    return updated_settings
