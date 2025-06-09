"""Expense tracking service functions."""

import math
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, extract

from app.models.expense_models import Expense, ExpenseCategory, PaymentMethod
from app.schemas.expense_schemas import ExpenseSummaryResponse, ExpenseCategorySummary


def round_to_grosz(amount: Decimal) -> Decimal:
    """Round amount to Polish grosz (0.01 PLN) using ROUND_HALF_UP."""
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_vat_amounts(
    amount_net: Optional[Decimal] = None,
    vat_rate: Optional[Decimal] = None,
    amount_gross: Optional[Decimal] = None
) -> Tuple[Decimal, Decimal, Decimal]:
    """
    Calculate VAT amounts from either net+rate or gross amount.
    
    Args:
        amount_net: Net amount (without VAT)
        vat_rate: VAT rate as percentage (e.g., 23.00 for 23%)
        amount_gross: Gross amount (including VAT)
        
    Returns:
        Tuple of (net_amount, vat_amount, gross_amount)
        
    Raises:
        ValueError: If invalid input combination
    """
    if amount_net is not None and vat_rate is not None:
        # Calculate from net + VAT rate
        net = round_to_grosz(amount_net)
        vat_decimal = vat_rate / Decimal("100")
        vat = round_to_grosz(net * vat_decimal)
        gross = round_to_grosz(net + vat)
        return net, vat, gross
        
    elif amount_gross is not None:
        # Calculate from gross amount (assume 23% VAT if not specified)
        if vat_rate is None:
            vat_rate = Decimal("23.00")
        
        gross = round_to_grosz(amount_gross)
        vat_decimal = vat_rate / Decimal("100")
        
        # Calculate net from gross: net = gross / (1 + vat_rate)
        net = round_to_grosz(gross / (Decimal("1") + vat_decimal))
        vat = round_to_grosz(gross - net)
        return net, vat, gross
        
    else:
        raise ValueError("Either provide amount_net + vat_rate OR amount_gross")


async def create_expense(session: AsyncSession, expense_data: Dict[str, Any]) -> Expense:
    """
    Create a new expense with automatic VAT calculations.
    
    Args:
        session: Database session
        expense_data: Expense data dictionary
        
    Returns:
        Created expense
        
    Raises:
        ValueError: If invalid data provided
    """
    # Calculate VAT amounts
    net, vat, gross = calculate_vat_amounts(
        amount_net=expense_data.get("amount_net"),
        vat_rate=expense_data.get("vat_rate"),
        amount_gross=expense_data.get("amount_gross")
    )
    
    # Create expense with calculated amounts
    expense = Expense(
        expense_date=expense_data["expense_date"],
        vendor_name=expense_data["vendor_name"],
        description=expense_data["description"],
        category=expense_data["category"],
        amount_net=net,
        vat_rate=expense_data.get("vat_rate", Decimal("23.00")),
        vat_amount=vat,
        amount_gross=gross,
        is_vat_deductible=expense_data.get("is_vat_deductible", True),
        is_tax_deductible=expense_data.get("is_tax_deductible", True),
        payment_method=expense_data["payment_method"],
        document_reference=expense_data.get("document_reference"),
        notes=expense_data.get("notes")
    )
    
    session.add(expense)
    await session.commit()
    await session.refresh(expense)
    
    return expense


async def get_expense_by_id(session: AsyncSession, expense_id: int) -> Optional[Expense]:
    """Get expense by ID."""
    statement = select(Expense).where(
        and_(Expense.id == expense_id, Expense.is_active == True)
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_expenses(
    session: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    category: Optional[ExpenseCategory] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    is_vat_deductible: Optional[bool] = None,
    is_tax_deductible: Optional[bool] = None
) -> Tuple[List[Expense], int]:
    """
    Get expenses with filtering, pagination, and search.
    
    Args:
        session: Database session
        page: Page number (1-based)
        per_page: Items per page
        search: Search term for vendor name or description
        category: Filter by expense category
        date_from: Filter expenses from this date
        date_to: Filter expenses to this date
        is_vat_deductible: Filter by VAT deductible status
        is_tax_deductible: Filter by tax deductible status
        
    Returns:
        Tuple of (expenses list, total count)
    """
    # Build base query
    statement = select(Expense).where(Expense.is_active == True)
    count_statement = select(func.count(Expense.id)).where(Expense.is_active == True)
    
    # Apply filters
    filters = []
    
    if search:
        search_filter = or_(
            Expense.vendor_name.ilike(f"%{search}%"),
            Expense.description.ilike(f"%{search}%"),
            Expense.document_reference.ilike(f"%{search}%")
        )
        filters.append(search_filter)
    
    if category:
        filters.append(Expense.category == category)
    
    if date_from:
        filters.append(Expense.expense_date >= date_from)
    
    if date_to:
        filters.append(Expense.expense_date <= date_to)
    
    if is_vat_deductible is not None:
        filters.append(Expense.is_vat_deductible == is_vat_deductible)
    
    if is_tax_deductible is not None:
        filters.append(Expense.is_tax_deductible == is_tax_deductible)
    
    # Apply filters to both statements
    if filters:
        statement = statement.where(and_(*filters))
        count_statement = count_statement.where(and_(*filters))
    
    # Add ordering and pagination
    statement = statement.order_by(Expense.expense_date.desc(), Expense.id.desc())
    statement = statement.offset((page - 1) * per_page).limit(per_page)
    
    # Execute queries
    result = await session.execute(statement)
    expenses = result.scalars().all()
    
    count_result = await session.execute(count_statement)
    total = count_result.scalar()
    
    return list(expenses), total


async def update_expense(
    session: AsyncSession, 
    expense_id: int, 
    update_data: Dict[str, Any]
) -> Optional[Expense]:
    """
    Update an expense.
    
    Args:
        session: Database session
        expense_id: Expense ID to update
        update_data: Data to update
        
    Returns:
        Updated expense or None if not found
    """
    expense = await get_expense_by_id(session, expense_id)
    if not expense:
        return None
    
    # If financial data is being updated, recalculate VAT amounts
    financial_fields = {"amount_net", "vat_rate", "amount_gross"}
    if any(field in update_data for field in financial_fields):
        # Get current or new values
        amount_net = update_data.get("amount_net", expense.amount_net)
        vat_rate = update_data.get("vat_rate", expense.vat_rate)
        amount_gross = update_data.get("amount_gross", expense.amount_gross)
        
        # Recalculate VAT amounts
        net, vat, gross = calculate_vat_amounts(
            amount_net=amount_net if "amount_net" in update_data else None,
            vat_rate=vat_rate,
            amount_gross=amount_gross if "amount_gross" in update_data else None
        )
        
        # Update financial fields
        expense.amount_net = net
        expense.vat_rate = vat_rate
        expense.vat_amount = vat
        expense.amount_gross = gross
    
    # Update other fields
    for field, value in update_data.items():
        if field not in financial_fields and hasattr(expense, field):
            setattr(expense, field, value)
    
    # Update timestamp
    expense.updated_at = datetime.now(timezone.utc)
    
    await session.commit()
    await session.refresh(expense)
    
    return expense


async def delete_expense(session: AsyncSession, expense_id: int) -> bool:
    """
    Soft delete an expense.
    
    Args:
        session: Database session
        expense_id: Expense ID to delete
        
    Returns:
        True if deleted, False if not found
    """
    expense = await get_expense_by_id(session, expense_id)
    if not expense:
        return False
    
    expense.is_active = False
    expense.updated_at = datetime.now(timezone.utc)
    
    await session.commit()
    return True


async def get_expense_summary(
    session: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    category: Optional[ExpenseCategory] = None
) -> ExpenseSummaryResponse:
    """
    Get expense summary with totals and category breakdown.

    Args:
        session: Database session
        date_from: Start date for summary
        date_to: End date for summary
        category: Filter by specific category

    Returns:
        Expense summary with totals and breakdowns
    """
    # Build base query
    filters = [Expense.is_active == True]

    if date_from:
        filters.append(Expense.expense_date >= date_from)

    if date_to:
        filters.append(Expense.expense_date <= date_to)

    if category:
        filters.append(Expense.category == category)

    # Get total counts and amounts
    statement = select(
        func.count(Expense.id).label("total_expenses"),
        func.sum(Expense.amount_net).label("total_net"),
        func.sum(Expense.vat_amount).label("total_vat"),
        func.sum(Expense.amount_gross).label("total_gross"),
        func.sum(
            func.case((Expense.is_vat_deductible == True, Expense.vat_amount), else_=0)
        ).label("deductible_vat"),
        func.sum(
            func.case((Expense.is_tax_deductible == True, Expense.amount_net), else_=0)
        ).label("deductible_expense")
    ).where(and_(*filters))

    result = await session.execute(statement)
    totals = result.first()

    # Get breakdown by category
    category_statement = select(
        Expense.category,
        func.count(Expense.id).label("count"),
        func.sum(Expense.amount_net).label("total_net"),
        func.sum(Expense.vat_amount).label("total_vat"),
        func.sum(Expense.amount_gross).label("total_gross")
    ).where(and_(*filters)).group_by(Expense.category)

    category_result = await session.execute(category_statement)
    category_breakdown = {}

    for row in category_result:
        category_breakdown[row.category.value] = {
            "count": row.count,
            "total_net": float(row.total_net or 0),
            "total_vat": float(row.total_vat or 0),
            "total_gross": float(row.total_gross or 0)
        }

    return ExpenseSummaryResponse(
        total_expenses=totals.total_expenses or 0,
        total_amount_net=totals.total_net or Decimal("0.00"),
        total_vat_amount=totals.total_vat or Decimal("0.00"),
        total_amount_gross=totals.total_gross or Decimal("0.00"),
        deductible_vat_amount=totals.deductible_vat or Decimal("0.00"),
        deductible_expense_amount=totals.deductible_expense or Decimal("0.00"),
        date_from=date_from,
        date_to=date_to,
        by_category=category_breakdown
    )


async def get_monthly_expense_summary(
    session: AsyncSession,
    year: int,
    month: int
) -> Dict[str, Any]:
    """Get expense summary for a specific month."""
    date_from = date(year, month, 1)

    # Calculate last day of month
    if month == 12:
        date_to = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        date_to = date(year, month + 1, 1) - timedelta(days=1)

    return await get_expense_summary(session, date_from, date_to)


def calculate_pagination_info(total: int, page: int, per_page: int) -> Dict[str, Any]:
    """Calculate pagination information."""
    total_pages = max(1, math.ceil(total / per_page))

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }
