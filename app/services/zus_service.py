"""ZUS (Social Insurance) calculation service."""

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, Any
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_models import ZUSSettings, HealthInsuranceTier
from app.services.company_service import get_zus_settings


class ZUSCalculationResult:
    """Result of ZUS calculation with detailed breakdown."""
    
    def __init__(self):
        # Base amount
        self.zus_base_amount: Decimal = Decimal("0.00")
        
        # Individual contributions
        self.emerytalne: Decimal = Decimal("0.00")
        self.rentowe: Decimal = Decimal("0.00") 
        self.wypadkowe: Decimal = Decimal("0.00")
        self.chorobowe: Decimal = Decimal("0.00")
        self.labor_fund: Decimal = Decimal("0.00")
        self.fep: Decimal = Decimal("0.00")
        
        # Health insurance
        self.health_insurance: Decimal = Decimal("0.00")
        self.health_insurance_tier: HealthInsuranceTier = HealthInsuranceTier.MEDIUM
        
        # Totals
        self.total_zus_contributions: Decimal = Decimal("0.00")
        self.total_with_health: Decimal = Decimal("0.00")
        
        # Metadata
        self.calculation_date: date = date.today()
        self.settings_effective_from: Optional[date] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "zus_base_amount": float(self.zus_base_amount),
            "emerytalne": float(self.emerytalne),
            "rentowe": float(self.rentowe),
            "wypadkowe": float(self.wypadkowe),
            "chorobowe": float(self.chorobowe),
            "labor_fund": float(self.labor_fund),
            "fep": float(self.fep),
            "health_insurance": float(self.health_insurance),
            "health_insurance_tier": self.health_insurance_tier.value,
            "total_zus_contributions": float(self.total_zus_contributions),
            "total_with_health": float(self.total_with_health),
            "calculation_date": self.calculation_date.isoformat(),
            "settings_effective_from": self.settings_effective_from.isoformat() if self.settings_effective_from else None
        }


def round_to_grosz(amount: Decimal) -> Decimal:
    """
    Round amount to Polish grosz (0.01 PLN) using ROUND_HALF_UP.
    
    Args:
        amount: Amount to round
        
    Returns:
        Rounded amount to 2 decimal places
    """
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_contribution_amount(base_amount: Decimal, rate_percent: Decimal) -> Decimal:
    """
    Calculate contribution amount from base and percentage rate.
    
    Args:
        base_amount: Base amount for calculation
        rate_percent: Rate as percentage (e.g., 19.52 for 19.52%)
        
    Returns:
        Calculated contribution amount rounded to grosz
    """
    if base_amount <= 0 or rate_percent < 0:
        return Decimal("0.00")
    
    # Convert percentage to decimal (19.52% -> 0.1952)
    rate_decimal = rate_percent / Decimal("100")
    
    # Calculate amount
    amount = base_amount * rate_decimal
    
    # Round to grosz
    return round_to_grosz(amount)


def calculate_health_insurance(
    monthly_income: Decimal, 
    tier: HealthInsuranceTier
) -> Decimal:
    """
    Calculate health insurance contribution based on income and tier.
    
    Polish health insurance rates for 2024:
    - Low tier: 9% of 60% of average salary (≈ 270 PLN)
    - Medium tier: 9% of 75% of average salary (≈ 335 PLN) 
    - High tier: 9% of income (for high earners)
    
    Args:
        monthly_income: Monthly income amount
        tier: Health insurance tier
        
    Returns:
        Health insurance contribution amount
    """
    # 2024 average salary base amounts for health insurance
    AVERAGE_SALARY_BASE = Decimal("7000.00")  # Approximate average salary
    
    if tier == HealthInsuranceTier.LOW:
        # 9% of 60% of average salary
        base = AVERAGE_SALARY_BASE * Decimal("0.60")
        contribution = base * Decimal("0.09")
    elif tier == HealthInsuranceTier.MEDIUM:
        # 9% of 75% of average salary  
        base = AVERAGE_SALARY_BASE * Decimal("0.75")
        contribution = base * Decimal("0.09")
    else:  # HIGH
        # 9% of actual income (with minimum)
        min_base = AVERAGE_SALARY_BASE * Decimal("0.75")
        base = max(monthly_income, min_base)
        contribution = base * Decimal("0.09")
    
    return round_to_grosz(contribution)


async def calculate_monthly_zus(
    session: AsyncSession,
    company_profile_id: int,
    monthly_income: Optional[Decimal] = None,
    calculation_date: Optional[date] = None
) -> ZUSCalculationResult:
    """
    Calculate monthly ZUS contributions for a company.
    
    Args:
        session: Database session
        company_profile_id: Company profile ID
        monthly_income: Monthly income for health insurance calculation
        calculation_date: Date for calculation (defaults to today)
        
    Returns:
        ZUSCalculationResult with detailed breakdown
        
    Raises:
        ValueError: If ZUS settings not found
    """
    if calculation_date is None:
        calculation_date = date.today()
    
    if monthly_income is None:
        monthly_income = Decimal("0.00")
    
    # Get ZUS settings
    zus_settings = await get_zus_settings(session, company_profile_id)
    if not zus_settings:
        raise ValueError("ZUS settings not found for company")
    
    # Initialize result
    result = ZUSCalculationResult()
    result.calculation_date = calculation_date
    result.settings_effective_from = zus_settings.effective_from
    result.zus_base_amount = zus_settings.zus_base_amount
    result.health_insurance_tier = zus_settings.health_insurance_tier
    
    # Calculate mandatory contributions
    result.emerytalne = calculate_contribution_amount(
        zus_settings.zus_base_amount, 
        zus_settings.emerytalne_rate
    )
    
    result.rentowe = calculate_contribution_amount(
        zus_settings.zus_base_amount,
        zus_settings.rentowe_rate
    )
    
    result.wypadkowe = calculate_contribution_amount(
        zus_settings.zus_base_amount,
        zus_settings.wypadkowe_rate
    )
    
    # Calculate optional contributions
    if zus_settings.is_chorobowe_active:
        result.chorobowe = calculate_contribution_amount(
            zus_settings.zus_base_amount,
            zus_settings.chorobowe_rate
        )
    
    result.labor_fund = calculate_contribution_amount(
        zus_settings.zus_base_amount,
        zus_settings.labor_fund_rate
    )
    
    if zus_settings.is_fep_active:
        result.fep = calculate_contribution_amount(
            zus_settings.zus_base_amount,
            zus_settings.fep_rate
        )
    
    # Calculate health insurance
    result.health_insurance = calculate_health_insurance(
        monthly_income,
        zus_settings.health_insurance_tier
    )
    
    # Calculate totals
    result.total_zus_contributions = (
        result.emerytalne + 
        result.rentowe + 
        result.wypadkowe + 
        result.chorobowe + 
        result.labor_fund + 
        result.fep
    )
    
    result.total_with_health = result.total_zus_contributions + result.health_insurance
    
    return result


async def calculate_yearly_zus_summary(
    session: AsyncSession,
    company_profile_id: int,
    year: int,
    monthly_incomes: Optional[Dict[int, Decimal]] = None
) -> Dict[str, Any]:
    """
    Calculate yearly ZUS summary with month-by-month breakdown.
    
    Args:
        session: Database session
        company_profile_id: Company profile ID
        year: Year for calculation
        monthly_incomes: Optional dict of {month: income} for health insurance
        
    Returns:
        Dictionary with yearly summary and monthly breakdown
    """
    if monthly_incomes is None:
        monthly_incomes = {}
    
    monthly_results = []
    yearly_totals = {
        "emerytalne": Decimal("0.00"),
        "rentowe": Decimal("0.00"),
        "wypadkowe": Decimal("0.00"),
        "chorobowe": Decimal("0.00"),
        "labor_fund": Decimal("0.00"),
        "fep": Decimal("0.00"),
        "health_insurance": Decimal("0.00"),
        "total_zus_contributions": Decimal("0.00"),
        "total_with_health": Decimal("0.00")
    }
    
    for month in range(1, 13):
        calculation_date = date(year, month, 1)
        monthly_income = monthly_incomes.get(month, Decimal("0.00"))
        
        try:
            result = await calculate_monthly_zus(
                session, 
                company_profile_id, 
                monthly_income, 
                calculation_date
            )
            
            monthly_data = result.to_dict()
            monthly_data["month"] = month
            monthly_results.append(monthly_data)
            
            # Add to yearly totals
            yearly_totals["emerytalne"] += result.emerytalne
            yearly_totals["rentowe"] += result.rentowe
            yearly_totals["wypadkowe"] += result.wypadkowe
            yearly_totals["chorobowe"] += result.chorobowe
            yearly_totals["labor_fund"] += result.labor_fund
            yearly_totals["fep"] += result.fep
            yearly_totals["health_insurance"] += result.health_insurance
            yearly_totals["total_zus_contributions"] += result.total_zus_contributions
            yearly_totals["total_with_health"] += result.total_with_health
            
        except ValueError:
            # If settings not found for this month, skip
            continue
    
    # Convert yearly totals to float for JSON serialization
    yearly_totals_float = {k: float(v) for k, v in yearly_totals.items()}
    
    return {
        "year": year,
        "monthly_breakdown": monthly_results,
        "yearly_totals": yearly_totals_float,
        "calculation_date": date.today().isoformat()
    }
