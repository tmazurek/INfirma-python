"""Tests for invoice API endpoints."""

import pytest
from fastapi.testclient import TestClient
from datetime import date


class TestInvoiceAPI:
    """Test invoice API endpoints."""
    
    def test_create_invoice_success(self, client: TestClient):
        """Test successful invoice creation."""
        # First create a client
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client_response = client.post("/api/v1/clients/", json=client_data)
        assert client_response.status_code == 201
        created_client = client_response.json()
        
        # Create invoice
        invoice_data = {
            "client_id": created_client["id"],
            "issue_date": "2024-06-15",
            "service_date": "2024-06-14",
            "payment_terms": "30_days",
            "place_of_issue": "Warszawa",
            "notes": "Test invoice",
            "items": [
                {
                    "description": "Programming services",
                    "quantity": 10.0,
                    "unit": "godz.",
                    "unit_price_net": 150.00,
                    "vat_rate": 23.00,
                    "item_code": "PROG-001"
                },
                {
                    "description": "Consultation",
                    "quantity": 2.0,
                    "unit": "godz.",
                    "unit_price_net": 200.00,
                    "vat_rate": 23.00
                }
            ]
        }
        
        response = client.post("/api/v1/invoices/", json=invoice_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        expected_fields = [
            "id", "invoice_number", "client_id", "issue_date", "due_date",
            "service_date", "payment_terms", "total_net", "total_vat", "total_gross",
            "currency", "status", "place_of_issue", "notes", "items"
        ]
        
        for field in expected_fields:
            assert field in data
        
        # Verify calculations
        assert data["invoice_number"] == "FV/2024/001"
        assert data["client_id"] == created_client["id"]
        assert data["issue_date"] == "2024-06-15"
        assert data["due_date"] == "2024-07-15"  # 30 days later
        assert data["service_date"] == "2024-06-14"
        assert data["payment_terms"] == "30_days"
        assert data["total_net"] == 1900.00  # 10*150 + 2*200
        assert data["total_vat"] == 437.00   # 1900 * 23%
        assert data["total_gross"] == 2337.00
        assert data["currency"] == "PLN"
        assert data["status"] == "draft"
        assert data["place_of_issue"] == "Warszawa"
        assert data["notes"] == "Test invoice"
        
        # Verify items
        assert len(data["items"]) == 2
        
        item1 = data["items"][0]
        assert item1["description"] == "Programming services"
        assert item1["quantity"] == 10.0
        assert item1["unit"] == "godz."
        assert item1["unit_price_net"] == 150.00
        assert item1["vat_rate"] == 23.00
        assert item1["item_total_net"] == 1500.00
        assert item1["item_total_vat"] == 345.00
        assert item1["item_total_gross"] == 1845.00
        assert item1["item_code"] == "PROG-001"
    
    def test_create_invoice_client_not_found(self, client: TestClient):
        """Test invoice creation with non-existent client."""
        invoice_data = {
            "client_id": 999,  # Non-existent client
            "issue_date": "2024-06-15",
            "place_of_issue": "Warszawa",
            "items": [
                {
                    "description": "Test service",
                    "quantity": 1.0,
                    "unit_price_net": 100.00,
                    "vat_rate": 23.00
                }
            ]
        }
        
        response = client.post("/api/v1/invoices/", json=invoice_data)
        
        assert response.status_code == 400
        assert "Client with ID 999 not found" in response.json()["detail"]
    
    def test_create_invoice_validation_errors(self, client: TestClient):
        """Test invoice creation with validation errors."""
        # Missing required fields
        invoice_data = {
            "client_id": 1,
            "issue_date": "2024-06-15",
            # Missing place_of_issue and items
        }
        
        response = client.post("/api/v1/invoices/", json=invoice_data)
        assert response.status_code == 422  # Validation error
        
        # Future issue date
        invoice_data = {
            "client_id": 1,
            "issue_date": "2025-12-31",  # Future date
            "place_of_issue": "Warszawa",
            "items": [
                {
                    "description": "Test service",
                    "quantity": 1.0,
                    "unit_price_net": 100.00,
                    "vat_rate": 23.00
                }
            ]
        }
        
        response = client.post("/api/v1/invoices/", json=invoice_data)
        assert response.status_code == 422
    
    def test_get_invoice_success(self, client: TestClient):
        """Test successful invoice retrieval."""
        # Create client and invoice first
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client_response = client.post("/api/v1/clients/", json=client_data)
        created_client = client_response.json()
        
        invoice_data = {
            "client_id": created_client["id"],
            "issue_date": "2024-06-15",
            "place_of_issue": "Warszawa",
            "items": [
                {
                    "description": "Test service",
                    "quantity": 1.0,
                    "unit_price_net": 100.00,
                    "vat_rate": 23.00
                }
            ]
        }
        
        create_response = client.post("/api/v1/invoices/", json=invoice_data)
        created_invoice = create_response.json()
        
        # Get invoice
        response = client.get(f"/api/v1/invoices/{created_invoice['id']}/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_invoice["id"]
        assert data["invoice_number"] == created_invoice["invoice_number"]
        assert len(data["items"]) == 1
    
    def test_get_invoice_not_found(self, client: TestClient):
        """Test invoice retrieval when not found."""
        response = client.get("/api/v1/invoices/999/")
        
        assert response.status_code == 404
        assert "Invoice not found" in response.json()["detail"]
    
    def test_get_invoice_by_number_success(self, client: TestClient):
        """Test successful invoice retrieval by number."""
        # Create client and invoice first
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client_response = client.post("/api/v1/clients/", json=client_data)
        created_client = client_response.json()
        
        invoice_data = {
            "client_id": created_client["id"],
            "issue_date": "2024-06-15",
            "place_of_issue": "Warszawa",
            "items": [
                {
                    "description": "Test service",
                    "quantity": 1.0,
                    "unit_price_net": 100.00,
                    "vat_rate": 23.00
                }
            ]
        }
        
        create_response = client.post("/api/v1/invoices/", json=invoice_data)
        created_invoice = create_response.json()
        
        # Get invoice by number
        response = client.get(f"/api/v1/invoices/number/{created_invoice['invoice_number']}/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_invoice["id"]
        assert data["invoice_number"] == created_invoice["invoice_number"]
    
    def test_list_invoices_empty(self, client: TestClient):
        """Test listing invoices when none exist."""
        response = client.get("/api/v1/invoices/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_list_invoices_with_data(self, client: TestClient):
        """Test listing invoices with data."""
        # Create client and multiple invoices
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client_response = client.post("/api/v1/clients/", json=client_data)
        created_client = client_response.json()
        
        # Create first invoice
        invoice_data_1 = {
            "client_id": created_client["id"],
            "issue_date": "2024-06-15",
            "place_of_issue": "Warszawa",
            "items": [
                {
                    "description": "Service 1",
                    "quantity": 1.0,
                    "unit_price_net": 100.00,
                    "vat_rate": 23.00
                }
            ]
        }
        
        client.post("/api/v1/invoices/", json=invoice_data_1)
        
        # Create second invoice
        invoice_data_2 = {
            "client_id": created_client["id"],
            "issue_date": "2024-06-16",
            "place_of_issue": "Warszawa",
            "items": [
                {
                    "description": "Service 2",
                    "quantity": 1.0,
                    "unit_price_net": 200.00,
                    "vat_rate": 23.00
                }
            ]
        }
        
        client.post("/api/v1/invoices/", json=invoice_data_2)
        
        # List invoices
        response = client.get("/api/v1/invoices/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Verify list item structure (should not include full details)
        for item in data:
            expected_fields = [
                "id", "invoice_number", "client_id", "issue_date", "due_date",
                "total_gross", "currency", "status", "created_at"
            ]
            for field in expected_fields:
                assert field in item
            
            # Should not include items in list view
            assert "items" not in item
    
    def test_list_invoices_with_filters(self, client: TestClient):
        """Test listing invoices with filters."""
        # Create client and invoices with different statuses
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client_response = client.post("/api/v1/clients/", json=client_data)
        created_client = client_response.json()
        
        # Create draft invoice
        invoice_data = {
            "client_id": created_client["id"],
            "issue_date": "2024-06-15",
            "place_of_issue": "Warszawa",
            "items": [
                {
                    "description": "Test service",
                    "quantity": 1.0,
                    "unit_price_net": 100.00,
                    "vat_rate": 23.00
                }
            ]
        }
        
        create_response = client.post("/api/v1/invoices/", json=invoice_data)
        created_invoice = create_response.json()
        
        # Issue the invoice
        client.post(f"/api/v1/invoices/{created_invoice['id']}/issue/")
        
        # Filter by status
        response = client.get("/api/v1/invoices/?status=issued")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "issued"
        
        # Filter by client
        response = client.get(f"/api/v1/invoices/?client_id={created_client['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["client_id"] == created_client["id"]
    
    def test_update_invoice_success(self, client: TestClient):
        """Test successful invoice update."""
        # Create client and invoice first
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client_response = client.post("/api/v1/clients/", json=client_data)
        created_client = client_response.json()
        
        invoice_data = {
            "client_id": created_client["id"],
            "issue_date": "2024-06-15",
            "place_of_issue": "Warszawa",
            "notes": "Original notes",
            "items": [
                {
                    "description": "Test service",
                    "quantity": 1.0,
                    "unit_price_net": 100.00,
                    "vat_rate": 23.00
                }
            ]
        }
        
        create_response = client.post("/api/v1/invoices/", json=invoice_data)
        created_invoice = create_response.json()
        
        # Update invoice
        update_data = {
            "notes": "Updated notes",
            "payment_terms": "14_days"
        }
        
        response = client.put(f"/api/v1/invoices/{created_invoice['id']}/", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Updated notes"
        assert data["payment_terms"] == "14_days"
        assert data["due_date"] == "2024-06-29"  # 14 days from issue date
    
    def test_update_invoice_not_draft(self, client: TestClient):
        """Test invoice update when not in DRAFT status."""
        # Create client and invoice first
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }
        
        client_response = client.post("/api/v1/clients/", json=client_data)
        created_client = client_response.json()
        
        invoice_data = {
            "client_id": created_client["id"],
            "issue_date": "2024-06-15",
            "place_of_issue": "Warszawa",
            "items": [
                {
                    "description": "Test service",
                    "quantity": 1.0,
                    "unit_price_net": 100.00,
                    "vat_rate": 23.00
                }
            ]
        }
        
        create_response = client.post("/api/v1/invoices/", json=invoice_data)
        created_invoice = create_response.json()
        
        # Issue the invoice
        client.post(f"/api/v1/invoices/{created_invoice['id']}/issue/")
        
        # Try to update - should fail
        update_data = {"notes": "Updated notes"}
        
        response = client.put(f"/api/v1/invoices/{created_invoice['id']}/", json=update_data)
        
        assert response.status_code == 400
        assert "Only DRAFT invoices can be updated" in response.json()["detail"]

    def test_issue_invoice_success(self, client: TestClient):
        """Test successful invoice issuing."""
        # Create client and invoice first
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }

        client_response = client.post("/api/v1/clients/", json=client_data)
        created_client = client_response.json()

        invoice_data = {
            "client_id": created_client["id"],
            "issue_date": "2024-06-15",
            "place_of_issue": "Warszawa",
            "items": [
                {
                    "description": "Test service",
                    "quantity": 1.0,
                    "unit_price_net": 100.00,
                    "vat_rate": 23.00
                }
            ]
        }

        create_response = client.post("/api/v1/invoices/", json=invoice_data)
        created_invoice = create_response.json()

        # Issue invoice
        response = client.post(f"/api/v1/invoices/{created_invoice['id']}/issue/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "issued"

    def test_mark_invoice_paid_success(self, client: TestClient):
        """Test successful invoice payment marking."""
        # Create client and invoice first
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }

        client_response = client.post("/api/v1/clients/", json=client_data)
        created_client = client_response.json()

        invoice_data = {
            "client_id": created_client["id"],
            "issue_date": "2024-06-15",
            "place_of_issue": "Warszawa",
            "items": [
                {
                    "description": "Test service",
                    "quantity": 1.0,
                    "unit_price_net": 100.00,
                    "vat_rate": 23.00
                }
            ]
        }

        create_response = client.post("/api/v1/invoices/", json=invoice_data)
        created_invoice = create_response.json()

        # Issue invoice first
        client.post(f"/api/v1/invoices/{created_invoice['id']}/issue/")

        # Mark as paid
        payment_data = {
            "status": "paid",
            "payment_date": "2024-06-20",
            "payment_method": "Bank transfer"
        }

        response = client.post(f"/api/v1/invoices/{created_invoice['id']}/mark-paid/", json=payment_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paid"
        assert data["payment_date"] == "2024-06-20"
        assert data["payment_method"] == "Bank transfer"

    def test_cancel_invoice_success(self, client: TestClient):
        """Test successful invoice cancellation."""
        # Create client and invoice first
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }

        client_response = client.post("/api/v1/clients/", json=client_data)
        created_client = client_response.json()

        invoice_data = {
            "client_id": created_client["id"],
            "issue_date": "2024-06-15",
            "place_of_issue": "Warszawa",
            "items": [
                {
                    "description": "Test service",
                    "quantity": 1.0,
                    "unit_price_net": 100.00,
                    "vat_rate": 23.00
                }
            ]
        }

        create_response = client.post("/api/v1/invoices/", json=invoice_data)
        created_invoice = create_response.json()

        # Cancel invoice
        response = client.post(f"/api/v1/invoices/{created_invoice['id']}/cancel/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"

    def test_delete_invoice_success(self, client: TestClient):
        """Test successful invoice deletion."""
        # Create client and invoice first
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }

        client_response = client.post("/api/v1/clients/", json=client_data)
        created_client = client_response.json()

        invoice_data = {
            "client_id": created_client["id"],
            "issue_date": "2024-06-15",
            "place_of_issue": "Warszawa",
            "items": [
                {
                    "description": "Test service",
                    "quantity": 1.0,
                    "unit_price_net": 100.00,
                    "vat_rate": 23.00
                }
            ]
        }

        create_response = client.post("/api/v1/invoices/", json=invoice_data)
        created_invoice = create_response.json()

        # Delete invoice
        response = client.delete(f"/api/v1/invoices/{created_invoice['id']}/")

        assert response.status_code == 204

        # Verify invoice is deleted
        get_response = client.get(f"/api/v1/invoices/{created_invoice['id']}/")
        assert get_response.status_code == 404

    def test_delete_invoice_not_draft(self, client: TestClient):
        """Test invoice deletion when not in DRAFT status."""
        # Create client and invoice first
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }

        client_response = client.post("/api/v1/clients/", json=client_data)
        created_client = client_response.json()

        invoice_data = {
            "client_id": created_client["id"],
            "issue_date": "2024-06-15",
            "place_of_issue": "Warszawa",
            "items": [
                {
                    "description": "Test service",
                    "quantity": 1.0,
                    "unit_price_net": 100.00,
                    "vat_rate": 23.00
                }
            ]
        }

        create_response = client.post("/api/v1/invoices/", json=invoice_data)
        created_invoice = create_response.json()

        # Issue the invoice
        client.post(f"/api/v1/invoices/{created_invoice['id']}/issue/")

        # Try to delete - should fail
        response = client.delete(f"/api/v1/invoices/{created_invoice['id']}/")

        assert response.status_code == 400
        assert "Only DRAFT invoices can be deleted" in response.json()["detail"]

    def test_get_invoice_summary_empty(self, client: TestClient):
        """Test invoice summary when no invoices exist."""
        response = client.get("/api/v1/invoices/summary/")

        assert response.status_code == 200
        data = response.json()

        expected_fields = [
            "total_invoices", "total_amount_net", "total_amount_vat", "total_amount_gross",
            "by_status", "outstanding_amount", "overdue_amount"
        ]

        for field in expected_fields:
            assert field in data

        assert data["total_invoices"] == 0
        assert data["total_amount_gross"] == 0.0

    def test_get_invoice_summary_with_data(self, client: TestClient):
        """Test invoice summary with data."""
        # Create client and invoices
        client_data = {
            "name": "Test Client",
            "nip": "1234567890",
            "street": "ul. Test 1",
            "city": "Warszawa",
            "postal_code": "00-001"
        }

        client_response = client.post("/api/v1/clients/", json=client_data)
        created_client = client_response.json()

        # Create and issue an invoice
        invoice_data = {
            "client_id": created_client["id"],
            "issue_date": "2024-06-15",
            "place_of_issue": "Warszawa",
            "items": [
                {
                    "description": "Test service",
                    "quantity": 1.0,
                    "unit_price_net": 100.00,
                    "vat_rate": 23.00
                }
            ]
        }

        create_response = client.post("/api/v1/invoices/", json=invoice_data)
        created_invoice = create_response.json()

        # Issue the invoice
        client.post(f"/api/v1/invoices/{created_invoice['id']}/issue/")

        # Get summary
        response = client.get("/api/v1/invoices/summary/")

        assert response.status_code == 200
        data = response.json()

        assert data["total_invoices"] == 1
        assert data["total_amount_net"] == 100.0
        assert data["total_amount_vat"] == 23.0
        assert data["total_amount_gross"] == 123.0
        assert data["outstanding_amount"] == 123.0  # Issued but not paid
        assert "issued" in data["by_status"]
        assert data["by_status"]["issued"]["count"] == 1
