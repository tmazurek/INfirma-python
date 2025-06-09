"""Tests for expense API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestExpenseAPI:
    """Test expense API endpoints."""
    
    def test_create_expense_with_net_amount(self, client: TestClient):
        """Test creating expense with net amount and VAT rate."""
        expense_data = {
            "expense_date": "2024-06-15",
            "vendor_name": "Test Vendor",
            "description": "Office supplies",
            "category": "office_supplies",
            "amount_net": 100.00,
            "vat_rate": 23.00,
            "payment_method": "card",
            "document_reference": "INV-001",
            "is_vat_deductible": True,
            "is_tax_deductible": True
        }
        
        response = client.post("/api/v1/expenses/", json=expense_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["vendor_name"] == "Test Vendor"
        assert data["amount_net"] == 100.00
        assert data["vat_rate"] == 23.00
        assert data["vat_amount"] == 23.00
        assert data["amount_gross"] == 123.00
        assert data["is_vat_deductible"] is True
        assert data["is_active"] is True
        assert data["id"] is not None
    
    def test_create_expense_with_gross_amount(self, client: TestClient):
        """Test creating expense with gross amount."""
        expense_data = {
            "expense_date": "2024-06-15",
            "vendor_name": "Test Vendor",
            "description": "Software license",
            "category": "software",
            "amount_gross": 123.00,
            "payment_method": "bank_transfer"
        }
        
        response = client.post("/api/v1/expenses/", json=expense_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["amount_gross"] == 123.00
        assert data["amount_net"] == 100.00
        assert data["vat_amount"] == 23.00
        assert data["vat_rate"] == 23.00  # Default rate
    
    def test_create_expense_invalid_data(self, client: TestClient):
        """Test creating expense with invalid data."""
        expense_data = {
            "expense_date": "2024-06-15",
            "vendor_name": "Test Vendor",
            "description": "Invalid expense",
            "category": "other",
            "payment_method": "cash"
            # Missing amount data
        }
        
        response = client.post("/api/v1/expenses/", json=expense_data)
        
        assert response.status_code == 400
        assert "Either provide amount_net" in response.json()["detail"]
    
    def test_create_expense_future_date(self, client: TestClient):
        """Test creating expense with future date."""
        expense_data = {
            "expense_date": "2030-12-31",  # Future date
            "vendor_name": "Test Vendor",
            "description": "Future expense",
            "category": "other",
            "amount_net": 100.00,
            "vat_rate": 23.00,
            "payment_method": "cash"
        }
        
        response = client.post("/api/v1/expenses/", json=expense_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_get_expenses_empty(self, client: TestClient):
        """Test getting expenses when none exist."""
        response = client.get("/api/v1/expenses/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["expenses"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["per_page"] == 20
        assert data["total_pages"] == 1
    
    def test_get_expenses_with_data(self, client: TestClient):
        """Test getting expenses with data."""
        # Create an expense first
        expense_data = {
            "expense_date": "2024-06-15",
            "vendor_name": "Test Vendor",
            "description": "Test expense",
            "category": "office_supplies",
            "amount_net": 100.00,
            "vat_rate": 23.00,
            "payment_method": "cash"
        }
        
        create_response = client.post("/api/v1/expenses/", json=expense_data)
        assert create_response.status_code == 201
        
        # Get expenses
        response = client.get("/api/v1/expenses/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["expenses"]) == 1
        assert data["total"] == 1
        assert data["expenses"][0]["vendor_name"] == "Test Vendor"
    
    def test_get_expenses_with_pagination(self, client: TestClient):
        """Test getting expenses with pagination."""
        # Create multiple expenses
        for i in range(5):
            expense_data = {
                "expense_date": f"2024-06-{i+10:02d}",
                "vendor_name": f"Vendor {i+1}",
                "description": f"Expense {i+1}",
                "category": "office_supplies",
                "amount_net": 10.00,
                "vat_rate": 23.00,
                "payment_method": "cash"
            }
            response = client.post("/api/v1/expenses/", json=expense_data)
            assert response.status_code == 201
        
        # Get first page
        response = client.get("/api/v1/expenses/?page=1&per_page=3")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["expenses"]) == 3
        assert data["total"] == 5
        assert data["total_pages"] == 2
    
    def test_get_expenses_with_search(self, client: TestClient):
        """Test searching expenses."""
        # Create test expenses
        expense_data_1 = {
            "expense_date": "2024-06-15",
            "vendor_name": "ABC Company",
            "description": "Office supplies",
            "category": "office_supplies",
            "amount_net": 100.00,
            "vat_rate": 23.00,
            "payment_method": "cash"
        }
        expense_data_2 = {
            "expense_date": "2024-06-16",
            "vendor_name": "XYZ Corporation",
            "description": "Software license",
            "category": "software",
            "amount_net": 200.00,
            "vat_rate": 23.00,
            "payment_method": "card"
        }
        
        client.post("/api/v1/expenses/", json=expense_data_1)
        client.post("/api/v1/expenses/", json=expense_data_2)
        
        # Search by vendor name
        response = client.get("/api/v1/expenses/?search=ABC")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["expenses"]) == 1
        assert data["expenses"][0]["vendor_name"] == "ABC Company"
    
    def test_get_expenses_with_filters(self, client: TestClient):
        """Test filtering expenses."""
        # Create test expenses
        expense_data_1 = {
            "expense_date": "2024-06-15",
            "vendor_name": "Vendor 1",
            "description": "Office supplies",
            "category": "office_supplies",
            "amount_net": 100.00,
            "vat_rate": 23.00,
            "payment_method": "cash"
        }
        expense_data_2 = {
            "expense_date": "2024-06-16",
            "vendor_name": "Vendor 2",
            "description": "Software",
            "category": "software",
            "amount_net": 200.00,
            "vat_rate": 23.00,
            "payment_method": "card"
        }
        
        client.post("/api/v1/expenses/", json=expense_data_1)
        client.post("/api/v1/expenses/", json=expense_data_2)
        
        # Filter by category
        response = client.get("/api/v1/expenses/?category=software")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["expenses"]) == 1
        assert data["expenses"][0]["category"] == "software"
        
        # Filter by date range
        response = client.get("/api/v1/expenses/?date_from=2024-06-16&date_to=2024-06-16")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["expenses"]) == 1
        assert data["expenses"][0]["expense_date"] == "2024-06-16"
    
    def test_get_expense_by_id(self, client: TestClient):
        """Test getting a specific expense by ID."""
        # Create an expense first
        expense_data = {
            "expense_date": "2024-06-15",
            "vendor_name": "Test Vendor",
            "description": "Test expense",
            "category": "office_supplies",
            "amount_net": 100.00,
            "vat_rate": 23.00,
            "payment_method": "cash"
        }
        
        create_response = client.post("/api/v1/expenses/", json=expense_data)
        created_expense = create_response.json()
        
        # Get the expense
        response = client.get(f"/api/v1/expenses/{created_expense['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_expense["id"]
        assert data["vendor_name"] == "Test Vendor"
    
    def test_get_expense_by_id_not_found(self, client: TestClient):
        """Test getting non-existent expense."""
        response = client.get("/api/v1/expenses/999")
        
        assert response.status_code == 404
        assert "Expense not found" in response.json()["detail"]
    
    def test_update_expense(self, client: TestClient):
        """Test updating an expense."""
        # Create an expense first
        expense_data = {
            "expense_date": "2024-06-15",
            "vendor_name": "Original Vendor",
            "description": "Original description",
            "category": "office_supplies",
            "amount_net": 100.00,
            "vat_rate": 23.00,
            "payment_method": "cash"
        }
        
        create_response = client.post("/api/v1/expenses/", json=expense_data)
        created_expense = create_response.json()
        
        # Update the expense
        update_data = {
            "vendor_name": "Updated Vendor",
            "amount_net": 150.00
        }
        
        response = client.put(f"/api/v1/expenses/{created_expense['id']}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["vendor_name"] == "Updated Vendor"
        assert data["amount_net"] == 150.00
        assert data["vat_amount"] == 34.50  # 150 * 23%
        assert data["amount_gross"] == 184.50
        assert data["description"] == "Original description"  # Should remain unchanged
    
    def test_update_expense_not_found(self, client: TestClient):
        """Test updating non-existent expense."""
        update_data = {"vendor_name": "New Vendor"}
        
        response = client.put("/api/v1/expenses/999", json=update_data)
        
        assert response.status_code == 404
        assert "Expense not found" in response.json()["detail"]
    
    def test_delete_expense(self, client: TestClient):
        """Test deleting an expense."""
        # Create an expense first
        expense_data = {
            "expense_date": "2024-06-15",
            "vendor_name": "To Delete",
            "description": "Will be deleted",
            "category": "other",
            "amount_net": 100.00,
            "vat_rate": 23.00,
            "payment_method": "cash"
        }
        
        create_response = client.post("/api/v1/expenses/", json=expense_data)
        created_expense = create_response.json()
        
        # Delete the expense
        response = client.delete(f"/api/v1/expenses/{created_expense['id']}")
        
        assert response.status_code == 204
        
        # Verify expense is not found in active expenses
        get_response = client.get(f"/api/v1/expenses/{created_expense['id']}")
        assert get_response.status_code == 404
    
    def test_delete_expense_not_found(self, client: TestClient):
        """Test deleting non-existent expense."""
        response = client.delete("/api/v1/expenses/999")
        
        assert response.status_code == 404
        assert "Expense not found" in response.json()["detail"]
    
    def test_get_expense_summary(self, client: TestClient):
        """Test getting expense summary."""
        # Create test expenses
        expense_data_1 = {
            "expense_date": "2024-06-15",
            "vendor_name": "Vendor 1",
            "description": "Office supplies",
            "category": "office_supplies",
            "amount_net": 100.00,
            "vat_rate": 23.00,
            "payment_method": "cash"
        }
        expense_data_2 = {
            "expense_date": "2024-06-16",
            "vendor_name": "Vendor 2",
            "description": "Software",
            "category": "software",
            "amount_net": 200.00,
            "vat_rate": 23.00,
            "payment_method": "card"
        }
        
        client.post("/api/v1/expenses/", json=expense_data_1)
        client.post("/api/v1/expenses/", json=expense_data_2)
        
        # Get summary
        response = client.get("/api/v1/expenses/summary/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_expenses"] == 2
        assert data["total_amount_net"] == 300.00
        assert data["total_vat_amount"] == 69.00
        assert data["total_amount_gross"] == 369.00
        assert "by_category" in data
        assert "office_supplies" in data["by_category"]
        assert "software" in data["by_category"]
    
    def test_get_expense_categories(self, client: TestClient):
        """Test getting available expense categories."""
        response = client.get("/api/v1/expenses/categories/")
        
        assert response.status_code == 200
        categories = response.json()
        assert isinstance(categories, list)
        assert "office_supplies" in categories
        assert "software" in categories
        assert "travel" in categories
    
    def test_get_payment_methods(self, client: TestClient):
        """Test getting available payment methods."""
        response = client.get("/api/v1/expenses/payment-methods/")
        
        assert response.status_code == 200
        methods = response.json()
        assert isinstance(methods, list)
        assert "cash" in methods
        assert "card" in methods
        assert "bank_transfer" in methods
