"""Invoice service for managing invoices and calculations."""

from typing import Optional, List, Tuple
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload

from app.models.invoice_models import Invoice, InvoiceItem, InvoiceStatus, PaymentTerms
from app.models.client_models import Client
from app.schemas.invoice_schemas import InvoiceCreate, InvoiceUpdate, InvoiceFilters


def round_to_grosz(amount: Decimal) -> Decimal:
    """Round amount to Polish grosz (0.01 PLN) using ROUND_HALF_UP."""
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_item_totals(quantity: Decimal, unit_price_net: Decimal, vat_rate: Decimal) -> Tuple[Decimal, Decimal, Decimal]:
    """
    Calculate item totals: net, VAT, and gross amounts.
    
    Args:
        quantity: Item quantity
        unit_price_net: Unit price without VAT
        vat_rate: VAT rate as percentage
        
    Returns:
        Tuple of (total_net, total_vat, total_gross)
    """
    total_net = round_to_grosz(quantity * unit_price_net)
    total_vat = round_to_grosz(total_net * vat_rate / Decimal("100"))
    total_gross = round_to_grosz(total_net + total_vat)
    
    return total_net, total_vat, total_gross


def calculate_due_date(issue_date: date, payment_terms: PaymentTerms, payment_terms_days: Optional[int] = None) -> date:
    """
    Calculate due date based on issue date and payment terms.
    
    Args:
        issue_date: Invoice issue date
        payment_terms: Payment terms enum
        payment_terms_days: Custom payment terms in days (for CUSTOM payment terms)
        
    Returns:
        Due date
    """
    if payment_terms == PaymentTerms.IMMEDIATE:
        return issue_date
    elif payment_terms == PaymentTerms.DAYS_7:
        return issue_date + timedelta(days=7)
    elif payment_terms == PaymentTerms.DAYS_14:
        return issue_date + timedelta(days=14)
    elif payment_terms == PaymentTerms.DAYS_30:
        return issue_date + timedelta(days=30)
    elif payment_terms == PaymentTerms.DAYS_60:
        return issue_date + timedelta(days=60)
    elif payment_terms == PaymentTerms.DAYS_90:
        return issue_date + timedelta(days=90)
    elif payment_terms == PaymentTerms.CUSTOM:
        if payment_terms_days is None:
            raise ValueError("payment_terms_days is required for CUSTOM payment terms")
        return issue_date + timedelta(days=payment_terms_days)
    else:
        return issue_date + timedelta(days=30)  # Default fallback


async def generate_invoice_number(session: AsyncSession, issue_date: date) -> str:
    """
    Generate unique invoice number in Polish format: FV/YYYY/NNN.
    
    Args:
        session: Database session
        issue_date: Invoice issue date
        
    Returns:
        Unique invoice number
    """
    year = issue_date.year
    
    # Get the highest invoice number for this year
    statement = select(func.max(Invoice.invoice_number)).where(
        Invoice.invoice_number.like(f"FV/{year}/%")
    )
    
    result = await session.execute(statement)
    max_number = result.scalar()
    
    if max_number:
        # Extract the sequence number from the last invoice
        try:
            sequence = int(max_number.split('/')[-1])
            next_sequence = sequence + 1
        except (ValueError, IndexError):
            next_sequence = 1
    else:
        next_sequence = 1
    
    # Format as FV/YYYY/NNN with zero padding
    return f"FV/{year}/{next_sequence:03d}"


async def create_invoice(session: AsyncSession, invoice_data: InvoiceCreate) -> Invoice:
    """
    Create a new invoice with items and calculations.
    
    Args:
        session: Database session
        invoice_data: Invoice creation data
        
    Returns:
        Created invoice
        
    Raises:
        ValueError: If client not found or validation fails
    """
    # Verify client exists
    client_statement = select(Client).where(Client.id == invoice_data.client_id)
    client_result = await session.execute(client_statement)
    client = client_result.scalar_one_or_none()
    
    if not client:
        raise ValueError(f"Client with ID {invoice_data.client_id} not found")
    
    # Generate invoice number
    invoice_number = await generate_invoice_number(session, invoice_data.issue_date)
    
    # Calculate due date
    due_date = calculate_due_date(
        invoice_data.issue_date,
        invoice_data.payment_terms,
        invoice_data.payment_terms_days
    )
    
    # Calculate totals from items
    total_net = Decimal("0.00")
    total_vat = Decimal("0.00")
    total_gross = Decimal("0.00")
    
    invoice_items = []
    
    for item_data in invoice_data.items:
        item_net, item_vat, item_gross = calculate_item_totals(
            item_data.quantity,
            item_data.unit_price_net,
            item_data.vat_rate
        )
        
        total_net += item_net
        total_vat += item_vat
        total_gross += item_gross
        
        invoice_items.append(InvoiceItem(
            description=item_data.description,
            quantity=item_data.quantity,
            unit=item_data.unit,
            unit_price_net=item_data.unit_price_net,
            vat_rate=item_data.vat_rate,
            item_total_net=item_net,
            item_total_vat=item_vat,
            item_total_gross=item_gross,
            item_code=item_data.item_code
        ))
    
    # Create invoice
    invoice = Invoice(
        invoice_number=invoice_number,
        client_id=invoice_data.client_id,
        issue_date=invoice_data.issue_date,
        due_date=due_date,
        service_date=invoice_data.service_date,
        payment_terms=invoice_data.payment_terms,
        payment_terms_days=invoice_data.payment_terms_days,
        total_net=total_net,
        total_vat=total_vat,
        total_gross=total_gross,
        currency=invoice_data.currency,
        exchange_rate=invoice_data.exchange_rate,
        notes=invoice_data.notes,
        internal_notes=invoice_data.internal_notes,
        place_of_issue=invoice_data.place_of_issue,
        status=InvoiceStatus.DRAFT
    )
    
    # Add invoice to session
    session.add(invoice)
    await session.flush()  # Get the invoice ID
    
    # Add items to invoice
    for item in invoice_items:
        item.invoice_id = invoice.id
        session.add(item)
    
    await session.commit()
    await session.refresh(invoice)
    
    # Load items relationship
    statement = select(Invoice).options(selectinload(Invoice.items)).where(Invoice.id == invoice.id)
    result = await session.execute(statement)
    return result.scalar_one()


async def get_invoice(session: AsyncSession, invoice_id: int) -> Optional[Invoice]:
    """
    Get invoice by ID with items.
    
    Args:
        session: Database session
        invoice_id: Invoice ID
        
    Returns:
        Invoice or None if not found
    """
    statement = select(Invoice).options(selectinload(Invoice.items)).where(
        and_(Invoice.id == invoice_id, Invoice.is_active == True)
    )
    
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_invoice_by_number(session: AsyncSession, invoice_number: str) -> Optional[Invoice]:
    """
    Get invoice by invoice number with items.
    
    Args:
        session: Database session
        invoice_number: Invoice number
        
    Returns:
        Invoice or None if not found
    """
    statement = select(Invoice).options(selectinload(Invoice.items)).where(
        and_(Invoice.invoice_number == invoice_number, Invoice.is_active == True)
    )
    
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def update_invoice(session: AsyncSession, invoice_id: int, invoice_data: InvoiceUpdate) -> Optional[Invoice]:
    """
    Update an existing invoice.
    
    Args:
        session: Database session
        invoice_id: Invoice ID
        invoice_data: Update data
        
    Returns:
        Updated invoice or None if not found
        
    Raises:
        ValueError: If invoice cannot be updated (e.g., not in DRAFT status)
    """
    invoice = await get_invoice(session, invoice_id)
    if not invoice:
        return None
    
    # Only allow updates for DRAFT invoices
    if invoice.status != InvoiceStatus.DRAFT:
        raise ValueError("Only DRAFT invoices can be updated")
    
    # Update fields
    update_data = invoice_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(invoice, field):
            setattr(invoice, field, value)
    
    # Recalculate due date if payment terms changed
    if 'payment_terms' in update_data or 'payment_terms_days' in update_data:
        invoice.due_date = calculate_due_date(
            invoice.issue_date,
            invoice.payment_terms,
            invoice.payment_terms_days
        )
    
    # Update timestamp
    invoice.updated_at = datetime.now(timezone.utc)
    
    await session.commit()
    await session.refresh(invoice)
    
    return invoice


async def delete_invoice(session: AsyncSession, invoice_id: int) -> bool:
    """
    Soft delete an invoice (only DRAFT invoices can be deleted).
    
    Args:
        session: Database session
        invoice_id: Invoice ID
        
    Returns:
        True if deleted, False if not found
        
    Raises:
        ValueError: If invoice cannot be deleted
    """
    invoice = await get_invoice(session, invoice_id)
    if not invoice:
        return False
    
    # Only allow deletion of DRAFT invoices
    if invoice.status != InvoiceStatus.DRAFT:
        raise ValueError("Only DRAFT invoices can be deleted")
    
    invoice.is_active = False
    invoice.updated_at = datetime.now(timezone.utc)
    
    await session.commit()
    return True


async def list_invoices(
    session: AsyncSession,
    filters: Optional[InvoiceFilters] = None,
    skip: int = 0,
    limit: int = 100
) -> Tuple[List[Invoice], int]:
    """
    List invoices with filtering and pagination.

    Args:
        session: Database session
        filters: Optional filters
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        Tuple of (invoices, total_count)
    """
    # Build base query
    statement = select(Invoice).where(Invoice.is_active == True)
    count_statement = select(func.count(Invoice.id)).where(Invoice.is_active == True)

    # Apply filters
    if filters:
        conditions = []

        if filters.status:
            conditions.append(Invoice.status == filters.status)

        if filters.client_id:
            conditions.append(Invoice.client_id == filters.client_id)

        if filters.date_from:
            conditions.append(Invoice.issue_date >= filters.date_from)

        if filters.date_to:
            conditions.append(Invoice.issue_date <= filters.date_to)

        if filters.due_date_from:
            conditions.append(Invoice.due_date >= filters.due_date_from)

        if filters.due_date_to:
            conditions.append(Invoice.due_date <= filters.due_date_to)

        if filters.currency:
            conditions.append(Invoice.currency == filters.currency)

        if filters.min_amount:
            conditions.append(Invoice.total_gross >= filters.min_amount)

        if filters.max_amount:
            conditions.append(Invoice.total_gross <= filters.max_amount)

        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(
                    Invoice.invoice_number.ilike(search_term),
                    Invoice.notes.ilike(search_term)
                )
            )

        if conditions:
            statement = statement.where(and_(*conditions))
            count_statement = count_statement.where(and_(*conditions))

    # Apply ordering and pagination
    statement = statement.order_by(desc(Invoice.created_at)).offset(skip).limit(limit)

    # Execute queries
    result = await session.execute(statement)
    invoices = result.scalars().all()

    count_result = await session.execute(count_statement)
    total_count = count_result.scalar()

    return list(invoices), total_count


async def update_invoice_status(
    session: AsyncSession,
    invoice_id: int,
    new_status: InvoiceStatus,
    payment_date: Optional[date] = None,
    payment_method: Optional[str] = None
) -> Optional[Invoice]:
    """
    Update invoice status with validation.

    Args:
        session: Database session
        invoice_id: Invoice ID
        new_status: New status
        payment_date: Payment date (required for PAID status)
        payment_method: Payment method

    Returns:
        Updated invoice or None if not found

    Raises:
        ValueError: If status transition is invalid
    """
    invoice = await get_invoice(session, invoice_id)
    if not invoice:
        return None

    # Validate status transitions
    current_status = invoice.status

    # Define valid transitions
    valid_transitions = {
        InvoiceStatus.DRAFT: [InvoiceStatus.ISSUED, InvoiceStatus.CANCELLED],
        InvoiceStatus.ISSUED: [InvoiceStatus.PAID, InvoiceStatus.OVERDUE, InvoiceStatus.CANCELLED],
        InvoiceStatus.PAID: [InvoiceStatus.ARCHIVED],
        InvoiceStatus.OVERDUE: [InvoiceStatus.PAID, InvoiceStatus.CANCELLED],
        InvoiceStatus.CANCELLED: [],  # Cannot transition from cancelled
        InvoiceStatus.ARCHIVED: []   # Cannot transition from archived
    }

    if new_status not in valid_transitions.get(current_status, []):
        raise ValueError(f"Cannot transition from {current_status} to {new_status}")

    # Special validation for PAID status
    if new_status == InvoiceStatus.PAID and payment_date is None:
        raise ValueError("payment_date is required when marking invoice as PAID")

    # Update invoice
    invoice.status = new_status
    invoice.updated_at = datetime.now(timezone.utc)

    if new_status == InvoiceStatus.PAID:
        invoice.payment_date = payment_date
        invoice.payment_method = payment_method

    await session.commit()
    await session.refresh(invoice)

    return invoice


async def get_invoice_summary(
    session: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    client_id: Optional[int] = None
) -> dict:
    """
    Get invoice summary statistics.

    Args:
        session: Database session
        date_from: Start date filter
        date_to: End date filter
        client_id: Client ID filter

    Returns:
        Summary statistics dictionary
    """
    # Build base query
    conditions = [Invoice.is_active == True]

    if date_from:
        conditions.append(Invoice.issue_date >= date_from)

    if date_to:
        conditions.append(Invoice.issue_date <= date_to)

    if client_id:
        conditions.append(Invoice.client_id == client_id)

    # Get basic statistics
    statement = select(
        func.count(Invoice.id).label("total_invoices"),
        func.sum(Invoice.total_net).label("total_net"),
        func.sum(Invoice.total_vat).label("total_vat"),
        func.sum(Invoice.total_gross).label("total_gross")
    ).where(and_(*conditions))

    result = await session.execute(statement)
    stats = result.first()

    # Get status breakdown
    status_statement = select(
        Invoice.status,
        func.count(Invoice.id).label("count"),
        func.sum(Invoice.total_gross).label("amount")
    ).where(and_(*conditions)).group_by(Invoice.status)

    status_result = await session.execute(status_statement)
    status_breakdown = {}

    for row in status_result:
        status_breakdown[row.status] = {
            "count": row.count,
            "amount": float(row.amount or 0)
        }

    # Calculate outstanding and overdue amounts
    outstanding_statement = select(
        func.sum(Invoice.total_gross)
    ).where(
        and_(
            Invoice.is_active == True,
            Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.OVERDUE])
        )
    )

    outstanding_result = await session.execute(outstanding_statement)
    outstanding_amount = outstanding_result.scalar() or Decimal("0.00")

    overdue_statement = select(
        func.sum(Invoice.total_gross)
    ).where(
        and_(
            Invoice.is_active == True,
            Invoice.status == InvoiceStatus.OVERDUE
        )
    )

    overdue_result = await session.execute(overdue_statement)
    overdue_amount = overdue_result.scalar() or Decimal("0.00")

    return {
        "total_invoices": stats.total_invoices or 0,
        "total_amount_net": float(stats.total_net or 0),
        "total_amount_vat": float(stats.total_vat or 0),
        "total_amount_gross": float(stats.total_gross or 0),
        "by_status": status_breakdown,
        "by_month": {},  # TODO: Implement monthly breakdown in future
        "outstanding_amount": float(outstanding_amount),
        "overdue_amount": float(overdue_amount),
        "date_from": date_from,
        "date_to": date_to
    }
