"""Tax calculation API endpoints."""

from typing import Optional
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.tax_schemas import (
    TaxCalculationRequest,
    VATCalculationResponse,
    PITCalculationResponse,
    MonthlyTaxSummaryResponse,
    DetailedTaxCalculationResponse,
    TaxComparisonRequest,
    TaxComparisonResponse,
    TaxBreakdownItem
)
from app.services import tax_service, company_service, zus_service

router = APIRouter(prefix="/api/v1/taxes", tags=["tax-calculations"])


@router.post("/vat/calculate/", response_model=VATCalculationResponse)
async def calculate_vat(
    calculation_request: TaxCalculationRequest,
    session: AsyncSession = Depends(get_session)
) -> VATCalculationResponse:
    """Calculate monthly VAT obligations."""
    # Get company profile
    company_profile = await company_service.get_company_profile(session)
    if not company_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found. Please create a company profile first."
        )
    
    try:
        result = await tax_service.calculate_monthly_vat(
            session,
            company_profile.id,
            calculation_request.year,
            calculation_request.month,
            calculation_request.calculation_date
        )
        
        return VATCalculationResponse.model_validate(result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/vat/calculate/", response_model=VATCalculationResponse)
async def calculate_vat_get(
    year: int = Query(..., ge=2020, le=2030, description="Year for calculation"),
    month: int = Query(..., ge=1, le=12, description="Month for calculation"),
    calculation_date: Optional[date] = Query(None, description="Date for calculation"),
    session: AsyncSession = Depends(get_session)
) -> VATCalculationResponse:
    """Calculate monthly VAT obligations using GET method."""
    request = TaxCalculationRequest(
        year=year,
        month=month,
        calculation_date=calculation_date
    )
    
    return await calculate_vat(request, session)


@router.post("/pit/calculate/", response_model=PITCalculationResponse)
async def calculate_pit(
    calculation_request: TaxCalculationRequest,
    session: AsyncSession = Depends(get_session)
) -> PITCalculationResponse:
    """Calculate monthly PIT (Personal Income Tax) obligations."""
    # Get company profile
    company_profile = await company_service.get_company_profile(session)
    if not company_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )
    
    try:
        result = await tax_service.calculate_monthly_pit(
            session,
            company_profile.id,
            calculation_request.year,
            calculation_request.month,
            calculation_request.monthly_income_gross,
            calculation_request.calculation_date
        )
        
        return PITCalculationResponse.model_validate(result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/pit/calculate/", response_model=PITCalculationResponse)
async def calculate_pit_get(
    year: int = Query(..., ge=2020, le=2030, description="Year for calculation"),
    month: int = Query(..., ge=1, le=12, description="Month for calculation"),
    monthly_income_gross: Optional[Decimal] = Query(None, ge=0, description="Monthly gross income"),
    calculation_date: Optional[date] = Query(None, description="Date for calculation"),
    session: AsyncSession = Depends(get_session)
) -> PITCalculationResponse:
    """Calculate monthly PIT obligations using GET method."""
    request = TaxCalculationRequest(
        year=year,
        month=month,
        monthly_income_gross=monthly_income_gross,
        calculation_date=calculation_date
    )
    
    return await calculate_pit(request, session)


@router.post("/summary/monthly/", response_model=MonthlyTaxSummaryResponse)
async def calculate_monthly_tax_summary(
    calculation_request: TaxCalculationRequest,
    session: AsyncSession = Depends(get_session)
) -> MonthlyTaxSummaryResponse:
    """Calculate comprehensive monthly tax summary including VAT, PIT, and ZUS."""
    # Get company profile
    company_profile = await company_service.get_company_profile(session)
    if not company_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )
    
    try:
        result = await tax_service.calculate_monthly_tax_summary(
            session,
            company_profile.id,
            calculation_request.year,
            calculation_request.month,
            calculation_request.monthly_income_gross,
            calculation_request.calculation_date
        )
        
        return MonthlyTaxSummaryResponse.model_validate(result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/summary/monthly/{year}/{month}", response_model=MonthlyTaxSummaryResponse)
async def calculate_monthly_tax_summary_get(
    year: int,
    month: int,
    monthly_income_gross: Optional[Decimal] = Query(None, ge=0, description="Monthly gross income"),
    session: AsyncSession = Depends(get_session)
) -> MonthlyTaxSummaryResponse:
    """Calculate monthly tax summary using GET method."""
    # Validate parameters
    if year < 2020 or year > 2030:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Year must be between 2020 and 2030"
        )
    
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Month must be between 1 and 12"
        )
    
    request = TaxCalculationRequest(
        year=year,
        month=month,
        monthly_income_gross=monthly_income_gross
    )
    
    return await calculate_monthly_tax_summary(request, session)


@router.post("/summary/detailed/", response_model=DetailedTaxCalculationResponse)
async def calculate_detailed_tax_summary(
    calculation_request: TaxCalculationRequest,
    session: AsyncSession = Depends(get_session)
) -> DetailedTaxCalculationResponse:
    """Calculate detailed tax summary with breakdown of all taxes and contributions."""
    # Get company profile
    company_profile = await company_service.get_company_profile(session)
    if not company_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )
    
    try:
        # Get comprehensive tax summary
        summary = await tax_service.calculate_monthly_tax_summary(
            session,
            company_profile.id,
            calculation_request.year,
            calculation_request.month,
            calculation_request.monthly_income_gross,
            calculation_request.calculation_date
        )
        
        # Get company settings for rates
        tax_settings = await company_service.get_tax_settings(session, company_profile.id)
        
        # Create detailed breakdown
        tax_breakdown = []
        
        # VAT breakdown
        if summary.vat_calculation.is_vat_payer:
            tax_breakdown.append(TaxBreakdownItem(
                tax_name="VAT to Pay",
                amount=summary.vat_calculation.vat_to_pay,
                rate_percent=summary.vat_calculation.vat_rate_used,
                base_amount=summary.vat_calculation.total_income_net,
                category="VAT"
            ))
        
        # PIT breakdown
        tax_breakdown.append(TaxBreakdownItem(
            tax_name=f"PIT ({summary.pit_calculation.tax_type_used.title()})",
            amount=summary.pit_calculation.pit_amount,
            rate_percent=summary.pit_calculation.pit_rate_used,
            base_amount=summary.pit_calculation.taxable_income,
            category="PIT"
        ))
        
        # ZUS breakdown
        tax_breakdown.append(TaxBreakdownItem(
            tax_name="ZUS Contributions",
            amount=summary.zus_total_contributions,
            category="ZUS"
        ))
        
        tax_breakdown.append(TaxBreakdownItem(
            tax_name="Health Insurance",
            amount=summary.zus_health_insurance,
            rate_percent=Decimal("9.00"),
            category="Health"
        ))
        
        # Calculate effective tax rate
        gross_income = summary.pit_calculation.total_income_gross
        effective_tax_rate = (summary.total_monthly_obligations / gross_income * Decimal("100")) if gross_income > 0 else Decimal("0.00")
        
        return DetailedTaxCalculationResponse(
            calculation_date=summary.calculation_date,
            year=summary.year,
            month=summary.month,
            monthly_income_gross=calculation_request.monthly_income_gross,
            tax_breakdown=tax_breakdown,
            total_vat=summary.vat_calculation.vat_to_pay,
            total_pit=summary.pit_calculation.pit_amount,
            total_zus=summary.zus_total_contributions,
            total_health_insurance=summary.zus_health_insurance,
            total_taxes=summary.total_taxes_to_pay,
            total_social_contributions=summary.total_social_contributions,
            total_obligations=summary.total_monthly_obligations,
            gross_income=gross_income,
            net_income_after_taxes=summary.net_income_after_taxes,
            effective_tax_rate=effective_tax_rate,
            vat_rate_used=summary.vat_calculation.vat_rate_used,
            pit_rate_used=summary.pit_calculation.pit_rate_used,
            tax_type_used=summary.pit_calculation.tax_type_used,
            is_vat_payer=summary.vat_calculation.is_vat_payer
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/compare/", response_model=TaxComparisonResponse)
async def compare_tax_options(
    comparison_request: TaxComparisonRequest,
    session: AsyncSession = Depends(get_session)
) -> TaxComparisonResponse:
    """Compare different tax options (ryczałt vs liniowy vs progresywny)."""
    # Get company profile
    company_profile = await company_service.get_company_profile(session)
    if not company_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company profile not found"
        )

    try:
        # Get current tax settings for rates
        tax_settings = await company_service.get_tax_settings(session, company_profile.id)
        if not tax_settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tax settings not found"
            )

        annual_income = comparison_request.annual_income
        annual_expenses = comparison_request.annual_expenses or Decimal("0.00")

        # Calculate ZUS if requested
        annual_zus = Decimal("0.00")
        annual_health = Decimal("0.00")

        if comparison_request.include_zus:
            try:
                # Calculate monthly ZUS and multiply by 12
                monthly_income = annual_income / Decimal("12")
                zus_result = await zus_service.calculate_monthly_zus(
                    session, company_profile.id, monthly_income
                )
                annual_zus = zus_result.total_zus_contributions * Decimal("12")
                annual_health = zus_result.health_insurance * Decimal("12")
            except ValueError:
                # If ZUS calculation fails, continue without ZUS
                pass

        tax_options = []

        # Option 1: Ryczałt
        from app.models.company_models import TaxType
        pit_ryczalt, _ = tax_service.calculate_pit_for_income_and_type(
            annual_income, TaxType.RYCZALT, tax_settings.pit_ryczalt_rate
        )

        total_ryczalt = pit_ryczalt + annual_zus + annual_health
        net_ryczalt = annual_income - total_ryczalt
        effective_rate_ryczalt = (total_ryczalt / annual_income * Decimal("100")) if annual_income > 0 else Decimal("0.00")

        from app.schemas.tax_schemas import TaxComparisonItem
        tax_options.append(TaxComparisonItem(
            tax_type="ryczalt",
            tax_type_name="Ryczałt",
            annual_pit=pit_ryczalt,
            annual_zus=annual_zus,
            annual_health_insurance=annual_health,
            total_annual_obligations=total_ryczalt,
            net_income_after_taxes=net_ryczalt,
            effective_rate=effective_rate_ryczalt
        ))

        # Option 2: Liniowy (19%)
        taxable_income_liniowy = max(Decimal("0.00"), annual_income - annual_expenses)
        pit_liniowy, _ = tax_service.calculate_pit_for_income_and_type(
            taxable_income_liniowy, TaxType.LINIOWY, Decimal("19.00"), annual_zus
        )

        total_liniowy = pit_liniowy + annual_zus + annual_health
        net_liniowy = annual_income - total_liniowy
        effective_rate_liniowy = (total_liniowy / annual_income * Decimal("100")) if annual_income > 0 else Decimal("0.00")

        tax_options.append(TaxComparisonItem(
            tax_type="liniowy",
            tax_type_name="Liniowy (19%)",
            annual_pit=pit_liniowy,
            annual_zus=annual_zus,
            annual_health_insurance=annual_health,
            total_annual_obligations=total_liniowy,
            net_income_after_taxes=net_liniowy,
            effective_rate=effective_rate_liniowy
        ))

        # Option 3: Progresywny (12%/32%)
        taxable_income_progresywny = max(Decimal("0.00"), annual_income - annual_expenses)
        pit_progresywny, _ = tax_service.calculate_pit_for_income_and_type(
            taxable_income_progresywny, TaxType.PROGRESYWNY, Decimal("12.00"), annual_zus
        )

        total_progresywny = pit_progresywny + annual_zus + annual_health
        net_progresywny = annual_income - total_progresywny
        effective_rate_progresywny = (total_progresywny / annual_income * Decimal("100")) if annual_income > 0 else Decimal("0.00")

        tax_options.append(TaxComparisonItem(
            tax_type="progresywny",
            tax_type_name="Progresywny (12%/32%)",
            annual_pit=pit_progresywny,
            annual_zus=annual_zus,
            annual_health_insurance=annual_health,
            total_annual_obligations=total_progresywny,
            net_income_after_taxes=net_progresywny,
            effective_rate=effective_rate_progresywny
        ))

        # Find the best option (lowest total obligations)
        best_option = min(tax_options, key=lambda x: x.total_annual_obligations)
        worst_option = max(tax_options, key=lambda x: x.total_annual_obligations)

        potential_savings = worst_option.total_annual_obligations - best_option.total_annual_obligations

        return TaxComparisonResponse(
            annual_income=annual_income,
            annual_expenses=annual_expenses,
            calculation_date=date.today(),
            tax_options=tax_options,
            recommended_option=best_option.tax_type_name,
            potential_savings=potential_savings
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error calculating tax comparison: {str(e)}"
        )
