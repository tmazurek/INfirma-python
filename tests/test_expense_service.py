"""Tests for expense service functions."""

import pytest
from decimal import Decimal
from datetime import date, datetime

from app.services.expense_service import (
    round_to_grosz,
    calculate_vat_amounts,
    create_expense,
    get_expense_by_id,
    get_expenses,
    update_expense,
    delete_expense,
    get_expense_summary,
    calculate_pagination_info
)
from app.models.expense_models import ExpenseCategory, PaymentMethod


class TestExpenseCalculationUtils:
    """Test expense calculation utility functions."""
    
    def test_round_to_grosz(self):
        """Test rounding to Polish grosz."""
        # Test normal rounding
        assert round_to_grosz(Decimal("123.456")) == Decimal("123.46")
        assert round_to_grosz(Decimal("123.454")) == Decimal("123.45")
        
        # Test half-up rounding (Polish standard)
        assert round_to_grosz(Decimal("123.455")) == Decimal("123.46")
        assert round_to_grosz(Decimal("123.445")) == Decimal("123.45")
        
        # Test already rounded values
        assert round_to_grosz(Decimal("123.45")) == Decimal("123.45")
        assert round_to_grosz(Decimal("123.00")) == Decimal("123.00")
    
    def test_calculate_vat_amounts_from_net(self):
        """Test VAT calculation from net amount and rate."""
        net, vat, gross = calculate_vat_amounts(
            amount_net=Decimal("100.00"),
            vat_rate=Decimal("23.00")
        )
        
        assert net == Decimal("100.00")
        assert vat == Decimal("23.00")  # 100 * 23% = 23
        assert gross == Decimal("123.00")  # 100 + 23 = 123
    
    def test_calculate_vat_amounts_from_gross(self):
        """Test VAT calculation from gross amount."""
        net, vat, gross = calculate_vat_amounts(
            amount_gross=Decimal("123.00"),
            vat_rate=Decimal("23.00")
        )
        
        assert gross == Decimal("123.00")
        # net = 123 / 1.23 = 100.00
        assert net == Decimal("100.00")
        # vat = 123 - 100 = 23.00
        assert vat == Decimal("23.00")
    
    def test_calculate_vat_amounts_from_gross_default_rate(self):
        """Test VAT calculation from gross with default 23% rate."""
        net, vat, gross = calculate_vat_amounts(
            amount_gross=Decimal("123.00")
        )
        
        assert gross == Decimal("123.00")
        assert net == Decimal("100.00")
        assert vat == Decimal("23.00")
    
    def test_calculate_vat_amounts_invalid_input(self):
        """Test VAT calculation with invalid input."""
        with pytest.raises(ValueError, match="Either provide amount_net"):
            calculate_vat_amounts()
    
    def test_calculate_vat_amounts_with_rounding(self):
        """Test VAT calculation with rounding."""
        net, vat, gross = calculate_vat_amounts(
            amount_net=Decimal("99.99"),
            vat_rate=Decimal("23.00")
        )
        
        assert net == Decimal("99.99")
        assert vat == Decimal("23.00")  # 99.99 * 0.23 = 22.9977 -> 23.00
        assert gross == Decimal("122.99")  # 99.99 + 23.00


class TestExpenseService:
    """Test expense service functions."""
    
    @pytest.mark.asyncio
    async def test_create_expense_with_net_amount(self, test_session):
        """Test creating expense with net amount and VAT rate."""
        expense_data = {
            "expense_date": date(2024, 6, 15),
            "vendor_name": "Test Vendor",
            "description": "Office supplies",
            "category": ExpenseCategory.OFFICE_SUPPLIES,
            "amount_net": Decimal("100.00"),
            "vat_rate": Decimal("23.00"),
            "payment_method": PaymentMethod.CARD,
            "document_reference": "INV-001"
        }
        
        expense = await create_expense(test_session, expense_data)
        
        assert expense.id is not None
        assert expense.vendor_name == "Test Vendor"
        assert expense.amount_net == Decimal("100.00")
        assert expense.vat_rate == Decimal("23.00")
        assert expense.vat_amount == Decimal("23.00")
        assert expense.amount_gross == Decimal("123.00")
        assert expense.is_vat_deductible is True
        assert expense.is_tax_deductible is True
        assert expense.is_active is True
    
    @pytest.mark.asyncio
    async def test_create_expense_with_gross_amount(self, test_session):
        """Test creating expense with gross amount."""
        expense_data = {
            "expense_date": date(2024, 6, 15),
            "vendor_name": "Test Vendor",
            "description": "Software license",
            "category": ExpenseCategory.SOFTWARE,
            "amount_gross": Decimal("123.00"),
            "payment_method": PaymentMethod.BANK_TRANSFER
        }
        
        expense = await create_expense(test_session, expense_data)
        
        assert expense.amount_gross == Decimal("123.00")
        assert expense.amount_net == Decimal("100.00")
        assert expense.vat_amount == Decimal("23.00")
        assert expense.vat_rate == Decimal("23.00")  # Default rate
    
    @pytest.mark.asyncio
    async def test_create_expense_invalid_data(self, test_session):
        """Test creating expense with invalid data."""
        expense_data = {
            "expense_date": date(2024, 6, 15),
            "vendor_name": "Test Vendor",
            "description": "Invalid expense",
            "category": ExpenseCategory.OTHER,
            "payment_method": PaymentMethod.CASH
            # Missing amount data
        }
        
        with pytest.raises(ValueError, match="Either provide amount_net"):
            await create_expense(test_session, expense_data)
    
    @pytest.mark.asyncio
    async def test_get_expense_by_id(self, test_session):
        """Test getting expense by ID."""
        # Create an expense first
        expense_data = {
            "expense_date": date(2024, 6, 15),
            "vendor_name": "Test Vendor",
            "description": "Test expense",
            "category": ExpenseCategory.OFFICE_SUPPLIES,
            "amount_net": Decimal("50.00"),
            "vat_rate": Decimal("23.00"),
            "payment_method": PaymentMethod.CASH
        }
        
        created_expense = await create_expense(test_session, expense_data)
        
        # Get the expense
        retrieved_expense = await get_expense_by_id(test_session, created_expense.id)
        
        assert retrieved_expense is not None
        assert retrieved_expense.id == created_expense.id
        assert retrieved_expense.vendor_name == "Test Vendor"
    
    @pytest.mark.asyncio
    async def test_get_expense_by_id_not_found(self, test_session):
        """Test getting expense by non-existent ID."""
        expense = await get_expense_by_id(test_session, 999)
        assert expense is None
    
    @pytest.mark.asyncio
    async def test_get_expenses_pagination(self, test_session):
        """Test getting expenses with pagination."""
        # Create multiple expenses
        for i in range(5):
            expense_data = {
                "expense_date": date(2024, 6, i + 1),
                "vendor_name": f"Vendor {i + 1}",
                "description": f"Expense {i + 1}",
                "category": ExpenseCategory.OFFICE_SUPPLIES,
                "amount_net": Decimal("10.00"),
                "vat_rate": Decimal("23.00"),
                "payment_method": PaymentMethod.CASH
            }
            await create_expense(test_session, expense_data)
        
        # Get first page
        expenses, total = await get_expenses(test_session, page=1, per_page=3)
        
        assert len(expenses) == 3
        assert total == 5
        # Should be sorted by date desc, then ID desc
        assert expenses[0].expense_date >= expenses[1].expense_date
    
    @pytest.mark.asyncio
    async def test_get_expenses_search(self, test_session):
        """Test searching expenses."""
        # Create test expenses
        expense_data_1 = {
            "expense_date": date(2024, 6, 15),
            "vendor_name": "ABC Company",
            "description": "Office supplies",
            "category": ExpenseCategory.OFFICE_SUPPLIES,
            "amount_net": Decimal("100.00"),
            "vat_rate": Decimal("23.00"),
            "payment_method": PaymentMethod.CASH
        }
        expense_data_2 = {
            "expense_date": date(2024, 6, 16),
            "vendor_name": "XYZ Corporation",
            "description": "Software license",
            "category": ExpenseCategory.SOFTWARE,
            "amount_net": Decimal("200.00"),
            "vat_rate": Decimal("23.00"),
            "payment_method": PaymentMethod.CARD
        }
        
        await create_expense(test_session, expense_data_1)
        await create_expense(test_session, expense_data_2)
        
        # Search by vendor name
        expenses, total = await get_expenses(test_session, search="ABC")
        
        assert len(expenses) == 1
        assert total == 1
        assert expenses[0].vendor_name == "ABC Company"
        
        # Search by description
        expenses, total = await get_expenses(test_session, search="Software")
        
        assert len(expenses) == 1
        assert total == 1
        assert expenses[0].description == "Software license"
    
    @pytest.mark.asyncio
    async def test_get_expenses_filter_by_category(self, test_session):
        """Test filtering expenses by category."""
        # Create expenses with different categories
        expense_data_1 = {
            "expense_date": date(2024, 6, 15),
            "vendor_name": "Vendor 1",
            "description": "Office supplies",
            "category": ExpenseCategory.OFFICE_SUPPLIES,
            "amount_net": Decimal("100.00"),
            "vat_rate": Decimal("23.00"),
            "payment_method": PaymentMethod.CASH
        }
        expense_data_2 = {
            "expense_date": date(2024, 6, 16),
            "vendor_name": "Vendor 2",
            "description": "Software",
            "category": ExpenseCategory.SOFTWARE,
            "amount_net": Decimal("200.00"),
            "vat_rate": Decimal("23.00"),
            "payment_method": PaymentMethod.CARD
        }
        
        await create_expense(test_session, expense_data_1)
        await create_expense(test_session, expense_data_2)
        
        # Filter by category
        expenses, total = await get_expenses(
            test_session, 
            category=ExpenseCategory.SOFTWARE
        )
        
        assert len(expenses) == 1
        assert total == 1
        assert expenses[0].category == ExpenseCategory.SOFTWARE
    
    @pytest.mark.asyncio
    async def test_update_expense(self, test_session):
        """Test updating an expense."""
        # Create an expense
        expense_data = {
            "expense_date": date(2024, 6, 15),
            "vendor_name": "Original Vendor",
            "description": "Original description",
            "category": ExpenseCategory.OFFICE_SUPPLIES,
            "amount_net": Decimal("100.00"),
            "vat_rate": Decimal("23.00"),
            "payment_method": PaymentMethod.CASH
        }
        
        expense = await create_expense(test_session, expense_data)
        
        # Update the expense
        update_data = {
            "vendor_name": "Updated Vendor",
            "amount_net": Decimal("150.00")
        }
        
        updated_expense = await update_expense(test_session, expense.id, update_data)
        
        assert updated_expense is not None
        assert updated_expense.vendor_name == "Updated Vendor"
        assert updated_expense.amount_net == Decimal("150.00")
        assert updated_expense.vat_amount == Decimal("34.50")  # 150 * 23%
        assert updated_expense.amount_gross == Decimal("184.50")
        assert updated_expense.description == "Original description"  # Unchanged
        assert updated_expense.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_update_expense_not_found(self, test_session):
        """Test updating non-existent expense."""
        update_data = {"vendor_name": "New Vendor"}
        
        result = await update_expense(test_session, 999, update_data)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_expense(self, test_session):
        """Test deleting an expense (soft delete)."""
        # Create an expense
        expense_data = {
            "expense_date": date(2024, 6, 15),
            "vendor_name": "To Delete",
            "description": "Will be deleted",
            "category": ExpenseCategory.OTHER,
            "amount_net": Decimal("100.00"),
            "vat_rate": Decimal("23.00"),
            "payment_method": PaymentMethod.CASH
        }
        
        expense = await create_expense(test_session, expense_data)
        
        # Delete the expense
        success = await delete_expense(test_session, expense.id)
        assert success is True
        
        # Verify expense is soft deleted
        deleted_expense = await get_expense_by_id(test_session, expense.id)
        assert deleted_expense is None  # Should not be found in active expenses
    
    @pytest.mark.asyncio
    async def test_delete_expense_not_found(self, test_session):
        """Test deleting non-existent expense."""
        success = await delete_expense(test_session, 999)
        assert success is False


class TestExpenseSummary:
    """Test expense summary functions."""
    
    @pytest.mark.asyncio
    async def test_get_expense_summary(self, test_session):
        """Test getting expense summary."""
        # Create test expenses
        expense_data_1 = {
            "expense_date": date(2024, 6, 15),
            "vendor_name": "Vendor 1",
            "description": "Office supplies",
            "category": ExpenseCategory.OFFICE_SUPPLIES,
            "amount_net": Decimal("100.00"),
            "vat_rate": Decimal("23.00"),
            "payment_method": PaymentMethod.CASH,
            "is_vat_deductible": True,
            "is_tax_deductible": True
        }
        expense_data_2 = {
            "expense_date": date(2024, 6, 16),
            "vendor_name": "Vendor 2",
            "description": "Software",
            "category": ExpenseCategory.SOFTWARE,
            "amount_net": Decimal("200.00"),
            "vat_rate": Decimal("23.00"),
            "payment_method": PaymentMethod.CARD,
            "is_vat_deductible": False,  # Not VAT deductible
            "is_tax_deductible": True
        }
        
        await create_expense(test_session, expense_data_1)
        await create_expense(test_session, expense_data_2)
        
        # Get summary
        summary = await get_expense_summary(test_session)
        
        assert summary.total_expenses == 2
        assert summary.total_amount_net == Decimal("300.00")  # 100 + 200
        assert summary.total_vat_amount == Decimal("69.00")   # 23 + 46
        assert summary.total_amount_gross == Decimal("369.00") # 123 + 246
        assert summary.deductible_vat_amount == Decimal("23.00")  # Only first expense
        assert summary.deductible_expense_amount == Decimal("300.00")  # Both expenses
        
        # Check category breakdown
        assert "office_supplies" in summary.by_category
        assert "software" in summary.by_category
        assert summary.by_category["office_supplies"]["count"] == 1
        assert summary.by_category["software"]["count"] == 1


class TestPaginationUtils:
    """Test pagination utility functions."""
    
    def test_calculate_pagination_info(self):
        """Test pagination calculation."""
        # Test normal case
        info = calculate_pagination_info(total=25, page=2, per_page=10)
        
        assert info["total"] == 25
        assert info["page"] == 2
        assert info["per_page"] == 10
        assert info["total_pages"] == 3
        assert info["has_next"] is True
        assert info["has_prev"] is True
        
        # Test first page
        info = calculate_pagination_info(total=25, page=1, per_page=10)
        assert info["has_prev"] is False
        assert info["has_next"] is True
        
        # Test last page
        info = calculate_pagination_info(total=25, page=3, per_page=10)
        assert info["has_prev"] is True
        assert info["has_next"] is False
        
        # Test empty result
        info = calculate_pagination_info(total=0, page=1, per_page=10)
        assert info["total_pages"] == 1
        assert info["has_prev"] is False
        assert info["has_next"] is False
