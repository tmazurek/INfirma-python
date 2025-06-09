"""Expense tracking API endpoints."""

from typing import Optional, List
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.expense_schemas import (
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseRead,
    ExpenseListResponse,
    ExpenseSummaryResponse
)
from app.models.expense_models import ExpenseCategory, PaymentMethod
from app.services import expense_service

router = APIRouter(prefix="/api/v1/expenses", tags=["expenses"])


@router.post("/", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense_data: ExpenseCreate,
    session: AsyncSession = Depends(get_session)
) -> ExpenseRead:
    """Create a new expense."""
    try:
        expense = await expense_service.create_expense(
            session, 
            expense_data.model_dump()
        )
        return ExpenseRead.model_validate(expense)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=ExpenseListResponse)
async def get_expenses(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in vendor name, description, or document reference"),
    category: Optional[ExpenseCategory] = Query(None, description="Filter by expense category"),
    date_from: Optional[date] = Query(None, description="Filter expenses from this date"),
    date_to: Optional[date] = Query(None, description="Filter expenses to this date"),
    is_vat_deductible: Optional[bool] = Query(None, description="Filter by VAT deductible status"),
    is_tax_deductible: Optional[bool] = Query(None, description="Filter by tax deductible status"),
    session: AsyncSession = Depends(get_session)
) -> ExpenseListResponse:
    """Get expenses with filtering and pagination."""
    expenses, total = await expense_service.get_expenses(
        session=session,
        page=page,
        per_page=per_page,
        search=search,
        category=category,
        date_from=date_from,
        date_to=date_to,
        is_vat_deductible=is_vat_deductible,
        is_tax_deductible=is_tax_deductible
    )
    
    pagination_info = expense_service.calculate_pagination_info(total, page, per_page)
    
    return ExpenseListResponse(
        expenses=[ExpenseRead.model_validate(expense) for expense in expenses],
        **pagination_info
    )


@router.get("/{expense_id}", response_model=ExpenseRead)
async def get_expense(
    expense_id: int,
    session: AsyncSession = Depends(get_session)
) -> ExpenseRead:
    """Get a specific expense by ID."""
    expense = await expense_service.get_expense_by_id(session, expense_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    return ExpenseRead.model_validate(expense)


@router.put("/{expense_id}", response_model=ExpenseRead)
async def update_expense(
    expense_id: int,
    expense_data: ExpenseUpdate,
    session: AsyncSession = Depends(get_session)
) -> ExpenseRead:
    """Update an expense."""
    try:
        updated_expense = await expense_service.update_expense(
            session, 
            expense_id, 
            expense_data.model_dump(exclude_unset=True)
        )
        
        if not updated_expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )
        
        return ExpenseRead.model_validate(updated_expense)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Delete an expense (soft delete)."""
    success = await expense_service.delete_expense(session, expense_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )


@router.get("/summary/", response_model=ExpenseSummaryResponse)
async def get_expense_summary(
    date_from: Optional[date] = Query(None, description="Start date for summary"),
    date_to: Optional[date] = Query(None, description="End date for summary"),
    category: Optional[ExpenseCategory] = Query(None, description="Filter by specific category"),
    session: AsyncSession = Depends(get_session)
) -> ExpenseSummaryResponse:
    """Get expense summary with totals and category breakdown."""
    return await expense_service.get_expense_summary(
        session=session,
        date_from=date_from,
        date_to=date_to,
        category=category
    )


@router.get("/categories/", response_model=List[str])
async def get_expense_categories():
    """Get list of available expense categories."""
    return [category.value for category in ExpenseCategory]


@router.get("/payment-methods/", response_model=List[str])
async def get_payment_methods():
    """Get list of available payment methods."""
    return [method.value for method in PaymentMethod]


@router.get("/summary/monthly/{year}/{month}", response_model=ExpenseSummaryResponse)
async def get_monthly_expense_summary(
    year: int,
    month: int,
    session: AsyncSession = Depends(get_session)
) -> ExpenseSummaryResponse:
    """Get expense summary for a specific month."""
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

    try:
        return await expense_service.get_monthly_expense_summary(session, year, month)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error calculating monthly summary: {str(e)}"
        )
