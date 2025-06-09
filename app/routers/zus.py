"""ZUS calculation API endpoints."""

from typing import Optional
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.zus_schemas import (
    ZUSCalculationRequest,
    ZUSCalculationResponse,
    YearlyZUSCalculationRequest,
    YearlyZUSCalculationResponse,
    DetailedZUSCalculationResponse,
    ZUSContributionBreakdown
)
from app.services import zus_service, company_service

router = APIRouter(prefix="/api/v1/zus", tags=["zus-calculations"])


@router.post("/calculate/", response_model=ZUSCalculationResponse)
async def calculate_monthly_zus(
    calculation_request: ZUSCalculationRequest,
    session: AsyncSession = Depends(get_session)
) -> ZUSCalculationResponse:
    """Calculate monthly ZUS contributions for the company."""
    # Get company profile
    company_profile = await company_service.get_company_profile(session)
    if not company_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found. Please create a company profile first."
        )
    
    try:
        result = await zus_service.calculate_monthly_zus(
            session,
            company_profile.id,
            calculation_request.monthly_income,
            calculation_request.calculation_date
        )
        
        return ZUSCalculationResponse(
            zus_base_amount=result.zus_base_amount,
            emerytalne=result.emerytalne,
            rentowe=result.rentowe,
            wypadkowe=result.wypadkowe,
            chorobowe=result.chorobowe,
            labor_fund=result.labor_fund,
            fep=result.fep,
            health_insurance=result.health_insurance,
            health_insurance_tier=result.health_insurance_tier,
            total_zus_contributions=result.total_zus_contributions,
            total_with_health=result.total_with_health,
            calculation_date=result.calculation_date,
            settings_effective_from=result.settings_effective_from
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/calculate/", response_model=ZUSCalculationResponse)
async def calculate_monthly_zus_get(
    monthly_income: Optional[Decimal] = Query(None, ge=0, description="Monthly income for health insurance"),
    calculation_date: Optional[date] = Query(None, description="Date for calculation"),
    session: AsyncSession = Depends(get_session)
) -> ZUSCalculationResponse:
    """Calculate monthly ZUS contributions using GET method with query parameters."""
    # Create request object
    request = ZUSCalculationRequest(
        monthly_income=monthly_income,
        calculation_date=calculation_date
    )
    
    # Reuse the POST endpoint logic
    return await calculate_monthly_zus(request, session)


@router.post("/calculate/detailed/", response_model=DetailedZUSCalculationResponse)
async def calculate_detailed_zus(
    calculation_request: ZUSCalculationRequest,
    session: AsyncSession = Depends(get_session)
) -> DetailedZUSCalculationResponse:
    """Calculate monthly ZUS contributions with detailed breakdown of each contribution."""
    # Get company profile
    company_profile = await company_service.get_company_profile(session)
    if not company_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )
    
    # Get ZUS settings
    zus_settings = await company_service.get_zus_settings(session, company_profile.id)
    if not zus_settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ZUS settings not found"
        )
    
    try:
        result = await zus_service.calculate_monthly_zus(
            session,
            company_profile.id,
            calculation_request.monthly_income,
            calculation_request.calculation_date
        )
        
        # Create detailed breakdown
        contributions = [
            ZUSContributionBreakdown(
                contribution_name="Emerytalne (Pension)",
                base_amount=zus_settings.zus_base_amount,
                rate_percent=zus_settings.emerytalne_rate,
                calculated_amount=result.emerytalne,
                is_active=True
            ),
            ZUSContributionBreakdown(
                contribution_name="Rentowe (Disability)",
                base_amount=zus_settings.zus_base_amount,
                rate_percent=zus_settings.rentowe_rate,
                calculated_amount=result.rentowe,
                is_active=True
            ),
            ZUSContributionBreakdown(
                contribution_name="Wypadkowe (Accident)",
                base_amount=zus_settings.zus_base_amount,
                rate_percent=zus_settings.wypadkowe_rate,
                calculated_amount=result.wypadkowe,
                is_active=True
            ),
            ZUSContributionBreakdown(
                contribution_name="Chorobowe (Sickness)",
                base_amount=zus_settings.zus_base_amount,
                rate_percent=zus_settings.chorobowe_rate,
                calculated_amount=result.chorobowe,
                is_active=zus_settings.is_chorobowe_active
            ),
            ZUSContributionBreakdown(
                contribution_name="Labor Fund",
                base_amount=zus_settings.zus_base_amount,
                rate_percent=zus_settings.labor_fund_rate,
                calculated_amount=result.labor_fund,
                is_active=True
            ),
            ZUSContributionBreakdown(
                contribution_name="FEP",
                base_amount=zus_settings.zus_base_amount,
                rate_percent=zus_settings.fep_rate,
                calculated_amount=result.fep,
                is_active=zus_settings.is_fep_active
            )
        ]
        
        # Calculate health insurance base
        monthly_income = calculation_request.monthly_income or Decimal("0.00")
        if result.health_insurance_tier.value == "low":
            health_base = Decimal("7000.00") * Decimal("0.60")
        elif result.health_insurance_tier.value == "medium":
            health_base = Decimal("7000.00") * Decimal("0.75")
        else:  # high
            health_base = max(monthly_income, Decimal("7000.00") * Decimal("0.75"))
        
        return DetailedZUSCalculationResponse(
            calculation_date=result.calculation_date,
            zus_base_amount=result.zus_base_amount,
            monthly_income=calculation_request.monthly_income,
            contributions=contributions,
            health_insurance=result.health_insurance,
            health_insurance_tier=result.health_insurance_tier,
            health_insurance_base=health_base,
            total_zus_contributions=result.total_zus_contributions,
            total_with_health=result.total_with_health,
            settings_effective_from=result.settings_effective_from
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/calculate/yearly/", response_model=YearlyZUSCalculationResponse)
async def calculate_yearly_zus(
    calculation_request: YearlyZUSCalculationRequest,
    session: AsyncSession = Depends(get_session)
) -> YearlyZUSCalculationResponse:
    """Calculate yearly ZUS summary with month-by-month breakdown."""
    # Get company profile
    company_profile = await company_service.get_company_profile(session)
    if not company_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )
    
    try:
        result = await zus_service.calculate_yearly_zus_summary(
            session,
            company_profile.id,
            calculation_request.year,
            calculation_request.monthly_incomes
        )
        
        return YearlyZUSCalculationResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/calculate/yearly/{year}", response_model=YearlyZUSCalculationResponse)
async def calculate_yearly_zus_get(
    year: int,
    session: AsyncSession = Depends(get_session)
) -> YearlyZUSCalculationResponse:
    """Calculate yearly ZUS summary using GET method."""
    if year < 2020 or year > 2030:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Year must be between 2020 and 2030"
        )
    
    # Create request object
    request = YearlyZUSCalculationRequest(year=year)
    
    # Reuse the POST endpoint logic
    return await calculate_yearly_zus(request, session)
