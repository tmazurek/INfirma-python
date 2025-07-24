"""Invoice management API endpoints."""

from typing import Optional, List
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.invoice_schemas import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceRead,
    InvoiceListItem,
    InvoiceStatusUpdate,
    InvoiceSummaryResponse,
    InvoiceFilters
)
from app.models.invoice_models import InvoiceStatus
from app.services import invoice_service

router = APIRouter(prefix="/api/v1/invoices", tags=["invoices"])


@router.post("/", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: InvoiceCreate,
    session: AsyncSession = Depends(get_session)
) -> InvoiceRead:
    """Create a new invoice with items and calculations."""
    try:
        invoice = await invoice_service.create_invoice(session, invoice_data)
        return InvoiceRead.model_validate(invoice)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[InvoiceListItem])
async def list_invoices(
    status_filter: Optional[InvoiceStatus] = Query(None, alias="status", description="Filter by status"),
    client_id: Optional[int] = Query(None, description="Filter by client ID"),
    date_from: Optional[date] = Query(None, description="Filter by issue date from"),
    date_to: Optional[date] = Query(None, description="Filter by issue date to"),
    due_date_from: Optional[date] = Query(None, description="Filter by due date from"),
    due_date_to: Optional[date] = Query(None, description="Filter by due date to"),
    currency: Optional[str] = Query(None, description="Filter by currency"),
    min_amount: Optional[float] = Query(None, ge=0, description="Minimum total amount"),
    max_amount: Optional[float] = Query(None, ge=0, description="Maximum total amount"),
    search: Optional[str] = Query(None, max_length=100, description="Search in invoice number or notes"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    session: AsyncSession = Depends(get_session)
) -> List[InvoiceListItem]:
    """List invoices with filtering and pagination."""
    # Build filters
    filters = InvoiceFilters(
        status=status_filter,
        client_id=client_id,
        date_from=date_from,
        date_to=date_to,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        currency=currency,
        min_amount=min_amount,
        max_amount=max_amount,
        search=search
    )
    
    invoices, total_count = await invoice_service.list_invoices(session, filters, skip, limit)
    
    # Convert to list items (without full details)
    return [InvoiceListItem.model_validate(invoice) for invoice in invoices]


@router.get("/summary/", response_model=InvoiceSummaryResponse)
async def get_invoice_summary(
    date_from: Optional[date] = Query(None, description="Start date for summary"),
    date_to: Optional[date] = Query(None, description="End date for summary"),
    client_id: Optional[int] = Query(None, description="Filter by client ID"),
    session: AsyncSession = Depends(get_session)
) -> InvoiceSummaryResponse:
    """Get invoice summary statistics."""
    summary = await invoice_service.get_invoice_summary(session, date_from, date_to, client_id)
    return InvoiceSummaryResponse.model_validate(summary)


@router.get("/{invoice_id}/", response_model=InvoiceRead)
async def get_invoice(
    invoice_id: int,
    session: AsyncSession = Depends(get_session)
) -> InvoiceRead:
    """Get a specific invoice by ID with all details and items."""
    invoice = await invoice_service.get_invoice(session, invoice_id)
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    return InvoiceRead.model_validate(invoice)


@router.get("/number/{invoice_number}/", response_model=InvoiceRead)
async def get_invoice_by_number(
    invoice_number: str,
    session: AsyncSession = Depends(get_session)
) -> InvoiceRead:
    """Get a specific invoice by invoice number."""
    invoice = await invoice_service.get_invoice_by_number(session, invoice_number)
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    return InvoiceRead.model_validate(invoice)


@router.put("/{invoice_id}/", response_model=InvoiceRead)
async def update_invoice(
    invoice_id: int,
    invoice_data: InvoiceUpdate,
    session: AsyncSession = Depends(get_session)
) -> InvoiceRead:
    """Update an existing invoice (only DRAFT invoices can be updated)."""
    try:
        invoice = await invoice_service.update_invoice(session, invoice_id, invoice_data)
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        return InvoiceRead.model_validate(invoice)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{invoice_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: int,
    session: AsyncSession = Depends(get_session)
) -> None:
    """Delete an invoice (only DRAFT invoices can be deleted)."""
    try:
        deleted = await invoice_service.delete_invoice(session, invoice_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{invoice_id}/issue/", response_model=InvoiceRead)
async def issue_invoice(
    invoice_id: int,
    session: AsyncSession = Depends(get_session)
) -> InvoiceRead:
    """Issue an invoice (transition from DRAFT to ISSUED status)."""
    try:
        invoice = await invoice_service.update_invoice_status(
            session, invoice_id, InvoiceStatus.ISSUED
        )
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        return InvoiceRead.model_validate(invoice)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{invoice_id}/mark-paid/", response_model=InvoiceRead)
async def mark_invoice_paid(
    invoice_id: int,
    status_data: InvoiceStatusUpdate,
    session: AsyncSession = Depends(get_session)
) -> InvoiceRead:
    """Mark an invoice as paid."""
    try:
        # Validate that status is PAID
        if status_data.status != InvoiceStatus.PAID:
            raise ValueError("This endpoint only accepts PAID status")
        
        invoice = await invoice_service.update_invoice_status(
            session,
            invoice_id,
            status_data.status,
            status_data.payment_date,
            status_data.payment_method
        )
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        return InvoiceRead.model_validate(invoice)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{invoice_id}/cancel/", response_model=InvoiceRead)
async def cancel_invoice(
    invoice_id: int,
    session: AsyncSession = Depends(get_session)
) -> InvoiceRead:
    """Cancel an invoice."""
    try:
        invoice = await invoice_service.update_invoice_status(
            session, invoice_id, InvoiceStatus.CANCELLED
        )
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        return InvoiceRead.model_validate(invoice)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{invoice_id}/archive/", response_model=InvoiceRead)
async def archive_invoice(
    invoice_id: int,
    session: AsyncSession = Depends(get_session)
) -> InvoiceRead:
    """Archive an invoice (only PAID invoices can be archived)."""
    try:
        invoice = await invoice_service.update_invoice_status(
            session, invoice_id, InvoiceStatus.ARCHIVED
        )
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        return InvoiceRead.model_validate(invoice)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{invoice_id}/status/", response_model=InvoiceRead)
async def update_invoice_status(
    invoice_id: int,
    status_data: InvoiceStatusUpdate,
    session: AsyncSession = Depends(get_session)
) -> InvoiceRead:
    """Update invoice status with validation."""
    try:
        invoice = await invoice_service.update_invoice_status(
            session,
            invoice_id,
            status_data.status,
            status_data.payment_date,
            status_data.payment_method
        )
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        return InvoiceRead.model_validate(invoice)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
