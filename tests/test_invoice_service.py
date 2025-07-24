"""Tests for invoice service functions."""

import pytest
from decimal import Decimal
from datetime import date, timedelta

from app.services.invoice_service import (
    round_to_grosz,
    calculate_item_totals,
    calculate_due_date,
    generate_invoice_number,
    create_invoice,
    get_invoice,
    get_invoice_by_number,
    update_invoice,
    delete_invoice,
    list_invoices,
    update_invoice_status,
    get_invoice_summary
)
from app.services.client_service import create_client
from app.schemas.invoice_schemas import InvoiceCreate, InvoiceItemCreate, InvoiceUpdate, InvoiceFilters
from app.models.invoice_models import InvoiceStatus, PaymentTerms


class TestInvoiceCalculations:
    """Test invoice calculation functions."""
    
    def test_round_to_grosz(self):
        """Test rounding to Polish grosz."""
        assert round_to_grosz(Decimal("123.456")) == Decimal("123.46")
        assert round_to_grosz(Decimal("123.454")) == Decimal("123.45")
        assert round_to_grosz(Decimal("123.455")) == Decimal("123.46")  # Half-up rounding
    
    def test_calculate_item_totals(self):
        """Test item total calculations."""
        quantity = Decimal("2.5")
        unit_price_net = Decimal("100.00")
        vat_rate = Decimal("23.00")
        
        total_net, total_vat, total_gross = calculate_item_totals(quantity, unit_price_net, vat_rate)
        
        assert total_net == Decimal("250.00")  # 2.5 * 100
        assert total_vat == Decimal("57.50")   # 250 * 23%
        assert total_gross == Decimal("307.50") # 250 + 57.50
    
    def test_calculate_due_date(self):
        """Test due date calculations."""
        issue_date = date(2024, 6, 15)
        
        # Test standard payment terms
        assert calculate_due_date(issue_date, PaymentTerms.IMMEDIATE) == issue_date
        assert calculate_due_date(issue_date, PaymentTerms.DAYS_7) == date(2024, 6, 22)
        assert calculate_due_date(issue_date, PaymentTerms.DAYS_14) == date(2024, 6, 29)
        assert calculate_due_date(issue_date, PaymentTerms.DAYS_30) == date(2024, 7, 15)
        assert calculate_due_date(issue_date, PaymentTerms.DAYS_60) == date(2024, 8, 14)
        assert calculate_due_date(issue_date, PaymentTerms.DAYS_90) == date(2024, 9, 13)
        
        # Test custom payment terms
        assert calculate_due_date(issue_date, PaymentTerms.CUSTOM, 45) == date(2024, 7, 30)
        
        # Test custom without days should raise error
        with pytest.raises(ValueError):
            calculate_due_date(issue_date, PaymentTerms.CUSTOM)


class TestInvoiceNumberGeneration:
    """Test invoice number generation."""
    
    @pytest.mark.asyncio
    async def test_generate_invoice_number_first(self, test_session):
        """Test generating first invoice number for a year."""
        issue_date = date(2024, 6, 15)
        
        invoice_number = await generate_invoice_number(test_session, issue_date)
        
        assert invoice_number == "FV/2024/001"
    
    @pytest.mark.asyncio
    async def test_generate_invoice_number_sequence(self, test_session):
        """Test generating sequential invoice numbers."""
        # Create a client first
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        client = await create_client(test_session, client_data)
        
        # Create first invoice
        invoice_data_1 = InvoiceCreate(
            client_id=client.id,
            issue_date=date(2024, 6, 15),
            place_of_issue="Warszawa",
            items=[
                InvoiceItemCreate(
                    description="Test service",
                    quantity=Decimal("1"),
                    unit_price_net=Decimal("100.00"),
                    vat_rate=Decimal("23.00")
                )
            ]
        )
        
        invoice1 = await create_invoice(test_session, invoice_data_1)
        assert invoice1.invoice_number == "FV/2024/001"
        
        # Create second invoice
        invoice_data_2 = InvoiceCreate(
            client_id=client.id,
            issue_date=date(2024, 6, 16),
            place_of_issue="Warszawa",
            items=[
                InvoiceItemCreate(
                    description="Another service",
                    quantity=Decimal("1"),
                    unit_price_net=Decimal("200.00"),
                    vat_rate=Decimal("23.00")
                )
            ]
        )
        
        invoice2 = await create_invoice(test_session, invoice_data_2)
        assert invoice2.invoice_number == "FV/2024/002"


class TestInvoiceCreation:
    """Test invoice creation."""
    
    @pytest.mark.asyncio
    async def test_create_invoice_success(self, test_session):
        """Test successful invoice creation."""
        # Create a client first
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        client = await create_client(test_session, client_data)
        
        # Create invoice
        invoice_data = InvoiceCreate(
            client_id=client.id,
            issue_date=date(2024, 6, 15),
            service_date=date(2024, 6, 14),
            payment_terms=PaymentTerms.DAYS_30,
            place_of_issue="Warszawa",
            notes="Test invoice",
            items=[
                InvoiceItemCreate(
                    description="Programming services",
                    quantity=Decimal("10"),
                    unit="godz.",
                    unit_price_net=Decimal("150.00"),
                    vat_rate=Decimal("23.00"),
                    item_code="PROG-001"
                ),
                InvoiceItemCreate(
                    description="Consultation",
                    quantity=Decimal("2"),
                    unit="godz.",
                    unit_price_net=Decimal("200.00"),
                    vat_rate=Decimal("23.00")
                )
            ]
        )
        
        invoice = await create_invoice(test_session, invoice_data)
        
        # Verify invoice details
        assert invoice.invoice_number == "FV/2024/001"
        assert invoice.client_id == client.id
        assert invoice.issue_date == date(2024, 6, 15)
        assert invoice.due_date == date(2024, 7, 15)  # 30 days later
        assert invoice.service_date == date(2024, 6, 14)
        assert invoice.payment_terms == PaymentTerms.DAYS_30
        assert invoice.place_of_issue == "Warszawa"
        assert invoice.notes == "Test invoice"
        assert invoice.status == InvoiceStatus.DRAFT
        assert invoice.currency == "PLN"
        
        # Verify calculations
        # Item 1: 10 * 150 = 1500 net, 345 VAT, 1845 gross
        # Item 2: 2 * 200 = 400 net, 92 VAT, 492 gross
        # Total: 1900 net, 437 VAT, 2337 gross
        assert invoice.total_net == Decimal("1900.00")
        assert invoice.total_vat == Decimal("437.00")
        assert invoice.total_gross == Decimal("2337.00")
        
        # Verify items
        assert len(invoice.items) == 2
        
        item1 = invoice.items[0]
        assert item1.description == "Programming services"
        assert item1.quantity == Decimal("10")
        assert item1.unit == "godz."
        assert item1.unit_price_net == Decimal("150.00")
        assert item1.vat_rate == Decimal("23.00")
        assert item1.item_total_net == Decimal("1500.00")
        assert item1.item_total_vat == Decimal("345.00")
        assert item1.item_total_gross == Decimal("1845.00")
        assert item1.item_code == "PROG-001"
        
        item2 = invoice.items[1]
        assert item2.description == "Consultation"
        assert item2.quantity == Decimal("2")
        assert item2.unit_price_net == Decimal("200.00")
        assert item2.item_total_net == Decimal("400.00")
        assert item2.item_total_vat == Decimal("92.00")
        assert item2.item_total_gross == Decimal("492.00")
    
    @pytest.mark.asyncio
    async def test_create_invoice_client_not_found(self, test_session):
        """Test invoice creation with non-existent client."""
        invoice_data = InvoiceCreate(
            client_id=999,  # Non-existent client
            issue_date=date(2024, 6, 15),
            place_of_issue="Warszawa",
            items=[
                InvoiceItemCreate(
                    description="Test service",
                    quantity=Decimal("1"),
                    unit_price_net=Decimal("100.00"),
                    vat_rate=Decimal("23.00")
                )
            ]
        )
        
        with pytest.raises(ValueError, match="Client with ID 999 not found"):
            await create_invoice(test_session, invoice_data)
    
    @pytest.mark.asyncio
    async def test_create_invoice_custom_payment_terms(self, test_session):
        """Test invoice creation with custom payment terms."""
        # Create a client first
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        client = await create_client(test_session, client_data)
        
        # Create invoice with custom payment terms
        invoice_data = InvoiceCreate(
            client_id=client.id,
            issue_date=date(2024, 6, 15),
            payment_terms=PaymentTerms.CUSTOM,
            payment_terms_days=45,
            place_of_issue="Warszawa",
            items=[
                InvoiceItemCreate(
                    description="Test service",
                    quantity=Decimal("1"),
                    unit_price_net=Decimal("100.00"),
                    vat_rate=Decimal("23.00")
                )
            ]
        )
        
        invoice = await create_invoice(test_session, invoice_data)
        
        assert invoice.payment_terms == PaymentTerms.CUSTOM
        assert invoice.payment_terms_days == 45
        assert invoice.due_date == date(2024, 7, 30)  # 45 days later


class TestInvoiceRetrieval:
    """Test invoice retrieval functions."""
    
    @pytest.mark.asyncio
    async def test_get_invoice_success(self, test_session):
        """Test successful invoice retrieval."""
        # Create client and invoice
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        client = await create_client(test_session, client_data)
        
        invoice_data = InvoiceCreate(
            client_id=client.id,
            issue_date=date(2024, 6, 15),
            place_of_issue="Warszawa",
            items=[
                InvoiceItemCreate(
                    description="Test service",
                    quantity=Decimal("1"),
                    unit_price_net=Decimal("100.00"),
                    vat_rate=Decimal("23.00")
                )
            ]
        )
        
        created_invoice = await create_invoice(test_session, invoice_data)
        
        # Retrieve invoice
        retrieved_invoice = await get_invoice(test_session, created_invoice.id)
        
        assert retrieved_invoice is not None
        assert retrieved_invoice.id == created_invoice.id
        assert retrieved_invoice.invoice_number == created_invoice.invoice_number
        assert len(retrieved_invoice.items) == 1
    
    @pytest.mark.asyncio
    async def test_get_invoice_not_found(self, test_session):
        """Test invoice retrieval when not found."""
        invoice = await get_invoice(test_session, 999)
        assert invoice is None
    
    @pytest.mark.asyncio
    async def test_get_invoice_by_number_success(self, test_session):
        """Test successful invoice retrieval by number."""
        # Create client and invoice
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        client = await create_client(test_session, client_data)
        
        invoice_data = InvoiceCreate(
            client_id=client.id,
            issue_date=date(2024, 6, 15),
            place_of_issue="Warszawa",
            items=[
                InvoiceItemCreate(
                    description="Test service",
                    quantity=Decimal("1"),
                    unit_price_net=Decimal("100.00"),
                    vat_rate=Decimal("23.00")
                )
            ]
        )
        
        created_invoice = await create_invoice(test_session, invoice_data)
        
        # Retrieve invoice by number
        retrieved_invoice = await get_invoice_by_number(test_session, created_invoice.invoice_number)
        
        assert retrieved_invoice is not None
        assert retrieved_invoice.id == created_invoice.id
        assert retrieved_invoice.invoice_number == created_invoice.invoice_number
    
    @pytest.mark.asyncio
    async def test_get_invoice_by_number_not_found(self, test_session):
        """Test invoice retrieval by number when not found."""
        invoice = await get_invoice_by_number(test_session, "FV/2024/999")
        assert invoice is None


class TestInvoiceUpdate:
    """Test invoice update functions."""

    @pytest.mark.asyncio
    async def test_update_invoice_success(self, test_session):
        """Test successful invoice update."""
        # Create client and invoice
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        client = await create_client(test_session, client_data)

        invoice_data = InvoiceCreate(
            client_id=client.id,
            issue_date=date(2024, 6, 15),
            place_of_issue="Warszawa",
            notes="Original notes",
            items=[
                InvoiceItemCreate(
                    description="Test service",
                    quantity=Decimal("1"),
                    unit_price_net=Decimal("100.00"),
                    vat_rate=Decimal("23.00")
                )
            ]
        )

        created_invoice = await create_invoice(test_session, invoice_data)

        # Update invoice
        update_data = InvoiceUpdate(
            notes="Updated notes",
            payment_terms=PaymentTerms.DAYS_14
        )

        updated_invoice = await update_invoice(test_session, created_invoice.id, update_data)

        assert updated_invoice is not None
        assert updated_invoice.notes == "Updated notes"
        assert updated_invoice.payment_terms == PaymentTerms.DAYS_14
        assert updated_invoice.due_date == date(2024, 6, 29)  # 14 days from issue date
        assert updated_invoice.updated_at is not None

    @pytest.mark.asyncio
    async def test_update_invoice_not_found(self, test_session):
        """Test invoice update when not found."""
        update_data = InvoiceUpdate(notes="Updated notes")

        updated_invoice = await update_invoice(test_session, 999, update_data)
        assert updated_invoice is None

    @pytest.mark.asyncio
    async def test_update_invoice_not_draft(self, test_session):
        """Test invoice update when not in DRAFT status."""
        # Create client and invoice
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        client = await create_client(test_session, client_data)

        invoice_data = InvoiceCreate(
            client_id=client.id,
            issue_date=date(2024, 6, 15),
            place_of_issue="Warszawa",
            items=[
                InvoiceItemCreate(
                    description="Test service",
                    quantity=Decimal("1"),
                    unit_price_net=Decimal("100.00"),
                    vat_rate=Decimal("23.00")
                )
            ]
        )

        created_invoice = await create_invoice(test_session, invoice_data)

        # Issue the invoice (change status to ISSUED)
        await update_invoice_status(test_session, created_invoice.id, InvoiceStatus.ISSUED)

        # Try to update - should fail
        update_data = InvoiceUpdate(notes="Updated notes")

        with pytest.raises(ValueError, match="Only DRAFT invoices can be updated"):
            await update_invoice(test_session, created_invoice.id, update_data)


class TestInvoiceStatusManagement:
    """Test invoice status management."""

    @pytest.mark.asyncio
    async def test_update_invoice_status_draft_to_issued(self, test_session):
        """Test status transition from DRAFT to ISSUED."""
        # Create client and invoice
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        client = await create_client(test_session, client_data)

        invoice_data = InvoiceCreate(
            client_id=client.id,
            issue_date=date(2024, 6, 15),
            place_of_issue="Warszawa",
            items=[
                InvoiceItemCreate(
                    description="Test service",
                    quantity=Decimal("1"),
                    unit_price_net=Decimal("100.00"),
                    vat_rate=Decimal("23.00")
                )
            ]
        )

        created_invoice = await create_invoice(test_session, invoice_data)
        assert created_invoice.status == InvoiceStatus.DRAFT

        # Update status to ISSUED
        updated_invoice = await update_invoice_status(
            test_session, created_invoice.id, InvoiceStatus.ISSUED
        )

        assert updated_invoice is not None
        assert updated_invoice.status == InvoiceStatus.ISSUED
        assert updated_invoice.updated_at is not None

    @pytest.mark.asyncio
    async def test_update_invoice_status_issued_to_paid(self, test_session):
        """Test status transition from ISSUED to PAID."""
        # Create client and invoice
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        client = await create_client(test_session, client_data)

        invoice_data = InvoiceCreate(
            client_id=client.id,
            issue_date=date(2024, 6, 15),
            place_of_issue="Warszawa",
            items=[
                InvoiceItemCreate(
                    description="Test service",
                    quantity=Decimal("1"),
                    unit_price_net=Decimal("100.00"),
                    vat_rate=Decimal("23.00")
                )
            ]
        )

        created_invoice = await create_invoice(test_session, invoice_data)

        # Issue the invoice first
        await update_invoice_status(test_session, created_invoice.id, InvoiceStatus.ISSUED)

        # Mark as paid
        payment_date = date(2024, 6, 20)
        updated_invoice = await update_invoice_status(
            test_session, created_invoice.id, InvoiceStatus.PAID, payment_date, "Bank transfer"
        )

        assert updated_invoice is not None
        assert updated_invoice.status == InvoiceStatus.PAID
        assert updated_invoice.payment_date == payment_date
        assert updated_invoice.payment_method == "Bank transfer"

    @pytest.mark.asyncio
    async def test_update_invoice_status_invalid_transition(self, test_session):
        """Test invalid status transition."""
        # Create client and invoice
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        client = await create_client(test_session, client_data)

        invoice_data = InvoiceCreate(
            client_id=client.id,
            issue_date=date(2024, 6, 15),
            place_of_issue="Warszawa",
            items=[
                InvoiceItemCreate(
                    description="Test service",
                    quantity=Decimal("1"),
                    unit_price_net=Decimal("100.00"),
                    vat_rate=Decimal("23.00")
                )
            ]
        )

        created_invoice = await create_invoice(test_session, invoice_data)

        # Try invalid transition: DRAFT to PAID (should go through ISSUED first)
        with pytest.raises(ValueError, match="Cannot transition from draft to paid"):
            await update_invoice_status(test_session, created_invoice.id, InvoiceStatus.PAID)

    @pytest.mark.asyncio
    async def test_update_invoice_status_paid_without_date(self, test_session):
        """Test marking invoice as PAID without payment date."""
        # Create client and invoice
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        client = await create_client(test_session, client_data)

        invoice_data = InvoiceCreate(
            client_id=client.id,
            issue_date=date(2024, 6, 15),
            place_of_issue="Warszawa",
            items=[
                InvoiceItemCreate(
                    description="Test service",
                    quantity=Decimal("1"),
                    unit_price_net=Decimal("100.00"),
                    vat_rate=Decimal("23.00")
                )
            ]
        )

        created_invoice = await create_invoice(test_session, invoice_data)

        # Issue the invoice first
        await update_invoice_status(test_session, created_invoice.id, InvoiceStatus.ISSUED)

        # Try to mark as paid without payment date
        with pytest.raises(ValueError, match="payment_date is required when marking invoice as PAID"):
            await update_invoice_status(test_session, created_invoice.id, InvoiceStatus.PAID)


class TestInvoiceDeletion:
    """Test invoice deletion."""

    @pytest.mark.asyncio
    async def test_delete_invoice_success(self, test_session):
        """Test successful invoice deletion."""
        # Create client and invoice
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        client = await create_client(test_session, client_data)

        invoice_data = InvoiceCreate(
            client_id=client.id,
            issue_date=date(2024, 6, 15),
            place_of_issue="Warszawa",
            items=[
                InvoiceItemCreate(
                    description="Test service",
                    quantity=Decimal("1"),
                    unit_price_net=Decimal("100.00"),
                    vat_rate=Decimal("23.00")
                )
            ]
        )

        created_invoice = await create_invoice(test_session, invoice_data)

        # Delete invoice
        deleted = await delete_invoice(test_session, created_invoice.id)
        assert deleted is True

        # Verify invoice is soft deleted
        retrieved_invoice = await get_invoice(test_session, created_invoice.id)
        assert retrieved_invoice is None  # Should not be found due to soft delete

    @pytest.mark.asyncio
    async def test_delete_invoice_not_found(self, test_session):
        """Test invoice deletion when not found."""
        deleted = await delete_invoice(test_session, 999)
        assert deleted is False

    @pytest.mark.asyncio
    async def test_delete_invoice_not_draft(self, test_session):
        """Test invoice deletion when not in DRAFT status."""
        # Create client and invoice
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        client = await create_client(test_session, client_data)

        invoice_data = InvoiceCreate(
            client_id=client.id,
            issue_date=date(2024, 6, 15),
            place_of_issue="Warszawa",
            items=[
                InvoiceItemCreate(
                    description="Test service",
                    quantity=Decimal("1"),
                    unit_price_net=Decimal("100.00"),
                    vat_rate=Decimal("23.00")
                )
            ]
        )

        created_invoice = await create_invoice(test_session, invoice_data)

        # Issue the invoice
        await update_invoice_status(test_session, created_invoice.id, InvoiceStatus.ISSUED)

        # Try to delete - should fail
        with pytest.raises(ValueError, match="Only DRAFT invoices can be deleted"):
            await delete_invoice(test_session, created_invoice.id)
