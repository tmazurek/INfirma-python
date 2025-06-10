"""Tax calculation service for VAT and PIT calculations."""

from typing import Optional, Dict, Any, Tuple
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from calendar import monthrange

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.tax_models import (
    VATCalculationResult,
    PITCalculationResult,
    MonthlyTaxSummary,
    TaxPeriod
)
from app.models.company_models import TaxType
from app.models.expense_models import Expense
from app.services import company_service, zus_service


def round_to_grosz(amount: Decimal) -> Decimal:
    """Round amount to Polish grosz (0.01 PLN) using ROUND_HALF_UP."""
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


async def calculate_monthly_vat(
    session: AsyncSession,
    company_profile_id: int,
    year: int,
    month: int,
    calculation_date: Optional[date] = None
) -> VATCalculationResult:
    """
    Calculate monthly VAT obligations.
    
    Args:
        session: Database session
        company_profile_id: Company profile ID
        year: Year for calculation
        month: Month for calculation
        calculation_date: Date of calculation (defaults to today)
        
    Returns:
        VATCalculationResult with detailed breakdown
        
    Raises:
        ValueError: If company settings not found
    """
    if calculation_date is None:
        calculation_date = date.today()
    
    # Get company tax settings
    tax_settings = await company_service.get_tax_settings(session, company_profile_id)
    if not tax_settings:
        raise ValueError("Tax settings not found for company")
    
    # Calculate period dates
    period_start = date(year, month, 1)
    last_day = monthrange(year, month)[1]
    period_end = date(year, month, last_day)
    
    # Initialize totals
    total_income_net = Decimal("0.00")
    total_income_vat = Decimal("0.00")
    total_income_gross = Decimal("0.00")
    
    # TODO: When invoice module is implemented, calculate income from invoices
    # For now, we'll use placeholder values or calculate from other sources
    
    # Calculate expenses VAT (from expense tracking)
    expense_statement = select(
        func.sum(Expense.amount_net).label("total_net"),
        func.sum(Expense.vat_amount).label("total_vat"),
        func.sum(Expense.amount_gross).label("total_gross"),
        func.sum(
            func.case((Expense.is_vat_deductible == True, Expense.vat_amount), else_=0)
        ).label("deductible_vat")
    ).where(
        and_(
            Expense.expense_date >= period_start,
            Expense.expense_date <= period_end,
            Expense.is_active == True
        )
    )
    
    expense_result = await session.execute(expense_statement)
    expense_data = expense_result.first()
    
    total_expenses_net = expense_data.total_net or Decimal("0.00")
    total_expenses_vat = expense_data.total_vat or Decimal("0.00")
    total_expenses_gross = expense_data.total_gross or Decimal("0.00")
    deductible_expenses_vat = expense_data.deductible_vat or Decimal("0.00")
    
    # Calculate VAT to pay
    if tax_settings.is_vat_payer:
        vat_to_pay = round_to_grosz(total_income_vat - deductible_expenses_vat)
    else:
        vat_to_pay = Decimal("0.00")
    
    return VATCalculationResult(
        calculation_date=calculation_date,
        period_start=period_start,
        period_end=period_end,
        period_type=TaxPeriod.MONTHLY,
        total_income_net=total_income_net,
        total_income_vat=total_income_vat,
        total_income_gross=total_income_gross,
        total_expenses_net=total_expenses_net,
        total_expenses_vat=total_expenses_vat,
        total_expenses_gross=total_expenses_gross,
        deductible_expenses_vat=deductible_expenses_vat,
        vat_to_pay=vat_to_pay,
        vat_rate_used=tax_settings.vat_rate,
        is_vat_payer=tax_settings.is_vat_payer,
        company_profile_id=company_profile_id
    )


async def calculate_monthly_pit(
    session: AsyncSession,
    company_profile_id: int,
    year: int,
    month: int,
    monthly_income_gross: Optional[Decimal] = None,
    calculation_date: Optional[date] = None
) -> PITCalculationResult:
    """
    Calculate monthly PIT (Personal Income Tax) obligations.
    
    Args:
        session: Database session
        company_profile_id: Company profile ID
        year: Year for calculation
        month: Month for calculation
        monthly_income_gross: Monthly income (if not provided, will be calculated)
        calculation_date: Date of calculation (defaults to today)
        
    Returns:
        PITCalculationResult with detailed breakdown
        
    Raises:
        ValueError: If company settings not found
    """
    if calculation_date is None:
        calculation_date = date.today()
    
    # Get company tax settings
    tax_settings = await company_service.get_tax_settings(session, company_profile_id)
    if not tax_settings:
        raise ValueError("Tax settings not found for company")
    
    # Calculate period dates
    period_start = date(year, month, 1)
    last_day = monthrange(year, month)[1]
    period_end = date(year, month, last_day)
    
    # Use provided income or default to 0 (will be calculated from invoices when implemented)
    if monthly_income_gross is None:
        monthly_income_gross = Decimal("0.00")
    
    # Calculate net income (assuming VAT rate for gross-to-net conversion)
    if monthly_income_gross > 0:
        vat_multiplier = Decimal("1") + (tax_settings.vat_rate / Decimal("100"))
        monthly_income_net = round_to_grosz(monthly_income_gross / vat_multiplier)
    else:
        monthly_income_net = Decimal("0.00")
    
    # Get tax-deductible expenses for the period
    expense_statement = select(
        func.sum(
            func.case((Expense.is_tax_deductible == True, Expense.amount_net), else_=0)
        ).label("deductible_expenses")
    ).where(
        and_(
            Expense.expense_date >= period_start,
            Expense.expense_date <= period_end,
            Expense.is_active == True
        )
    )
    
    expense_result = await session.execute(expense_statement)
    total_deductible_expenses = expense_result.scalar() or Decimal("0.00")
    
    # Calculate taxable income
    taxable_income = max(Decimal("0.00"), monthly_income_net - total_deductible_expenses)
    
    # Calculate PIT based on tax type
    pit_amount = Decimal("0.00")
    zus_deductible_amount = None
    
    if tax_settings.tax_type == TaxType.RYCZALT:
        # Ryczałt: flat rate on income (no expense deductions, no ZUS deductions)
        pit_amount = round_to_grosz(monthly_income_net * tax_settings.pit_ryczalt_rate / Decimal("100"))
        
    elif tax_settings.tax_type == TaxType.LINIOWY:
        # Linear tax: 19% on taxable income (after expenses and ZUS deductions)
        # Get ZUS contributions for deduction
        try:
            zus_result = await zus_service.calculate_monthly_zus(
                session, company_profile_id, monthly_income_net, period_start
            )
            zus_deductible_amount = zus_result.total_zus_contributions
            
            # Deduct ZUS from taxable income
            taxable_income_after_zus = max(Decimal("0.00"), taxable_income - zus_deductible_amount)
            pit_amount = round_to_grosz(taxable_income_after_zus * Decimal("19.00") / Decimal("100"))
            
        except ValueError:
            # If ZUS calculation fails, calculate without ZUS deduction
            pit_amount = round_to_grosz(taxable_income * Decimal("19.00") / Decimal("100"))
            
    elif tax_settings.tax_type == TaxType.PROGRESYWNY:
        # Progressive tax: 12% up to 120,000 PLN, 32% above (2024 rates)
        # This is simplified - real progressive tax has more complex rules
        try:
            zus_result = await zus_service.calculate_monthly_zus(
                session, company_profile_id, monthly_income_net, period_start
            )
            zus_deductible_amount = zus_result.total_zus_contributions
            
            # Deduct ZUS from taxable income
            taxable_income_after_zus = max(Decimal("0.00"), taxable_income - zus_deductible_amount)
            
            # Apply progressive rates (simplified monthly calculation)
            monthly_threshold = Decimal("10000.00")  # 120,000 / 12 months
            
            if taxable_income_after_zus <= monthly_threshold:
                pit_amount = round_to_grosz(taxable_income_after_zus * Decimal("12.00") / Decimal("100"))
            else:
                pit_lower = round_to_grosz(monthly_threshold * Decimal("12.00") / Decimal("100"))
                pit_higher = round_to_grosz((taxable_income_after_zus - monthly_threshold) * Decimal("32.00") / Decimal("100"))
                pit_amount = pit_lower + pit_higher
                
        except ValueError:
            # If ZUS calculation fails, calculate without ZUS deduction
            pit_amount = round_to_grosz(taxable_income * Decimal("12.00") / Decimal("100"))
    
    return PITCalculationResult(
        calculation_date=calculation_date,
        period_start=period_start,
        period_end=period_end,
        period_type=TaxPeriod.MONTHLY,
        total_income_net=monthly_income_net,
        total_income_gross=monthly_income_gross,
        total_deductible_expenses=total_deductible_expenses,
        taxable_income=taxable_income,
        pit_amount=pit_amount,
        pit_rate_used=tax_settings.pit_ryczalt_rate if tax_settings.tax_type == TaxType.RYCZALT else Decimal("19.00"),
        tax_type_used=tax_settings.tax_type.value,
        zus_deductible_amount=zus_deductible_amount,
        company_profile_id=company_profile_id
    )


async def calculate_monthly_tax_summary(
    session: AsyncSession,
    company_profile_id: int,
    year: int,
    month: int,
    monthly_income_gross: Optional[Decimal] = None,
    calculation_date: Optional[date] = None
) -> MonthlyTaxSummary:
    """
    Calculate comprehensive monthly tax summary including VAT, PIT, and ZUS.

    Args:
        session: Database session
        company_profile_id: Company profile ID
        year: Year for calculation
        month: Month for calculation
        monthly_income_gross: Monthly income (if not provided, will be calculated)
        calculation_date: Date of calculation (defaults to today)

    Returns:
        MonthlyTaxSummary with complete breakdown

    Raises:
        ValueError: If company settings not found
    """
    if calculation_date is None:
        calculation_date = date.today()

    # Calculate VAT
    vat_calculation = await calculate_monthly_vat(
        session, company_profile_id, year, month, calculation_date
    )

    # Calculate PIT
    pit_calculation = await calculate_monthly_pit(
        session, company_profile_id, year, month, monthly_income_gross, calculation_date
    )

    # Calculate ZUS
    monthly_income_net = pit_calculation.total_income_net
    try:
        zus_result = await zus_service.calculate_monthly_zus(
            session, company_profile_id, monthly_income_net, calculation_date
        )
        zus_total_contributions = zus_result.total_zus_contributions
        zus_health_insurance = zus_result.health_insurance
        zus_total_with_health = zus_result.total_with_health
    except ValueError:
        # If ZUS calculation fails, use zero values
        zus_total_contributions = Decimal("0.00")
        zus_health_insurance = Decimal("0.00")
        zus_total_with_health = Decimal("0.00")

    # Calculate totals
    total_taxes_to_pay = round_to_grosz(vat_calculation.vat_to_pay + pit_calculation.pit_amount)
    total_social_contributions = zus_total_with_health
    total_monthly_obligations = round_to_grosz(total_taxes_to_pay + total_social_contributions)

    # Calculate net income after all obligations
    gross_income = pit_calculation.total_income_gross
    net_income_after_taxes = round_to_grosz(gross_income - total_monthly_obligations)

    return MonthlyTaxSummary(
        year=year,
        month=month,
        calculation_date=calculation_date,
        vat_calculation=vat_calculation,
        pit_calculation=pit_calculation,
        zus_total_contributions=zus_total_contributions,
        zus_health_insurance=zus_health_insurance,
        zus_total_with_health=zus_total_with_health,
        total_taxes_to_pay=total_taxes_to_pay,
        total_social_contributions=total_social_contributions,
        total_monthly_obligations=total_monthly_obligations,
        net_income_after_taxes=net_income_after_taxes,
        company_profile_id=company_profile_id
    )


def calculate_pit_for_income_and_type(
    income: Decimal,
    tax_type: TaxType,
    pit_ryczalt_rate: Decimal,
    zus_deductible: Optional[Decimal] = None
) -> Tuple[Decimal, Decimal]:
    """
    Calculate PIT amount for given income and tax type.

    Args:
        income: Taxable income
        tax_type: Type of tax calculation
        pit_ryczalt_rate: Ryczałt rate for ryczałt tax type
        zus_deductible: ZUS amount that can be deducted (for liniowy/progresywny)

    Returns:
        Tuple of (pit_amount, effective_rate)
    """
    if zus_deductible is None:
        zus_deductible = Decimal("0.00")

    if tax_type == TaxType.RYCZALT:
        # Ryczałt: flat rate on income
        pit_amount = round_to_grosz(income * pit_ryczalt_rate / Decimal("100"))
        effective_rate = pit_ryczalt_rate

    elif tax_type == TaxType.LINIOWY:
        # Linear tax: 19% on income after ZUS deduction
        taxable_income = max(Decimal("0.00"), income - zus_deductible)
        pit_amount = round_to_grosz(taxable_income * Decimal("19.00") / Decimal("100"))
        effective_rate = Decimal("19.00") if income > 0 else Decimal("0.00")

    elif tax_type == TaxType.PROGRESYWNY:
        # Progressive tax: 12% up to 120,000 PLN annually, 32% above
        taxable_income = max(Decimal("0.00"), income - zus_deductible)
        annual_threshold = Decimal("120000.00")

        if taxable_income <= annual_threshold:
            pit_amount = round_to_grosz(taxable_income * Decimal("12.00") / Decimal("100"))
            effective_rate = Decimal("12.00")
        else:
            pit_lower = round_to_grosz(annual_threshold * Decimal("12.00") / Decimal("100"))
            pit_higher = round_to_grosz((taxable_income - annual_threshold) * Decimal("32.00") / Decimal("100"))
            pit_amount = pit_lower + pit_higher
            effective_rate = (pit_amount / taxable_income * Decimal("100")) if taxable_income > 0 else Decimal("0.00")

    else:
        pit_amount = Decimal("0.00")
        effective_rate = Decimal("0.00")

    return pit_amount, effective_rate
