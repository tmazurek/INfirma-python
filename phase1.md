Okay, FastAPI is an excellent choice for a Python-based API, especially if you value high performance, modern Python features (like type hints and async), and automatic interactive documentation! This changes the framework but the core requirements, data models, and overall project structure will be adapted.

Let's completely rewrite the blueprint for **Phase 1 (Backend API Development)** using **FastAPI**. Phase 2 (Frontend UI) would likely involve a separate frontend framework (like React, Vue, Svelte) or server-side rendering with Jinja2 templates if you want to keep it within a Python ecosystem for rendering, though FastAPI itself is unopinionated about the frontend. For now, we focus solely on the API.

**Primary Guiding Models (FastAPI Context):**

1.  **Jobs-to-be-Done (JTBD):** The API must serve as the robust, reliable "engine" for a Polish accounting application, handling complex calculations and data management with precision for IT freelancers/small businesses using "ryczałt."
2.  **Falsifiability & Robustness (Python Testing with FastAPI):** Comprehensive testing using `pytest` and FastAPI's `TestClient` is crucial. All financial logic must be provably correct.
3.  **Accuracy & Precision (Python `Decimal` & Pydantic):** Python's `Decimal` type for financial math, combined with Pydantic models for data validation and serialization, will ensure data integrity and accuracy.
4.  **Modularity & Maintainability (FastAPI Routers & Services):** Structuring the API with FastAPI routers for different resource groups and service layers for business logic will promote good organization.
5.  **Configuration over Hardcoding:** Application settings (including default tax rates, ZUS parameters) will be managed through a configuration system (e.g., Pydantic's `BaseSettings` or environment variables).

**Confidence Score:** High (that these detailed requirements can be effectively mapped to a robust FastAPI backend blueprint).

**Key Assumptions (FastAPI Context):**

1.  **Target User:** Small IT businesses/freelancers in Poland, primarily using "ryczałt."
2.  **Initial Focus:** Backend API development and testing.
3.  **Database & ORM:** SQLite database. We'll use **SQLAlchemy Core** for query building and database interaction, often paired with an async library like `databases` for async support with FastAPI, or a full ORM like **SQLModel** (which combines Pydantic and SQLAlchemy) or standard SQLAlchemy ORM. For simplicity and directness, this blueprint will lean towards SQLModel or SQLAlchemy ORM for managing models and interactions, as it integrates well with Pydantic.
4.  **Criticality of Calculations:** Precision using Python's `Decimal` type is paramount.
5.  **Testing Rigor:** Multi-layered testing (unit tests for services/utils, integration/E2E API tests with FastAPI's `TestClient`).
6.  **Configuration:** ZUS rates, tax parameters will be highly configurable.
7.  **Technology Stack:** Python with FastAPI, Pydantic, SQLModel/SQLAlchemy, `python-jose` for potential JWT auth later, `pytest`.

---

Here's the completely rewritten blueprint for the FastAPI-based backend API.

<MARKDOWN_DOCUMENT title="InFirma - FastAPI Backend API MVP Blueprint">

## InFirma - FastAPI Backend API MVP Blueprint

This document outlines the blueprint for a Minimum Viable Product (MVP) focusing on the backend API for a Polish accounting application, built using Python with the FastAPI framework. It is tailored for small IT businesses and freelancers, emphasizing accurate financial calculations, robust testing, and configurability according to Polish tax regulations.

---

**I. High-Level Architecture & Technology Stack (Backend - Phase 1):**

*   **Framework:** FastAPI (leveraging Pydantic for data validation and serialization, and dependency injection).
*   **Database:** SQLite.
*   **ORM/Database Toolkit:** SQLModel (combines Pydantic and SQLAlchemy, ideal for FastAPI) or standard SQLAlchemy ORM with `databases` for async support. This blueprint will assume **SQLModel** for conciseness in defining models that are also Pydantic schemas.
*   **Data Handling:** Python's built-in `Decimal` type for all financial calculations, enforced via Pydantic models.
*   **API Design:**
    *   RESTful principles.
    *   JSON for request and response payloads.
    *   Pydantic models define request/response schemas and perform automatic validation.
    *   FastAPI `APIRouter` for organizing endpoints.
    *   Automatic interactive API documentation (Swagger UI and ReDoc) provided by FastAPI.
    *   API versioning (e.g., prefix `/api/v1` in routers).
*   **Asynchronous Operations:** FastAPI encourages async operations; database interactions will be designed to be async where appropriate (using `async/await` with compatible database drivers/libraries like `aiosqlite` if using `databases` or async SQLAlchemy).
*   **Development Workflow & Quality Assurance:**
    *   **Testing Framework:** `pytest` with FastAPI's `TestClient`.
        *   **Unit Tests:** For individual functions, calculation services, utility modules.
        *   **Integration/E2E API Tests:** Using `TestClient` to test API endpoints, request validation, business logic execution, database interactions, and response accuracy.
    *   **Linter:** `Flake8` (or `Pylint`, `Ruff`).
    *   **Formatter:** `Black`.
    *   **Type Checking:** `Mypy` (FastAPI and Pydantic heavily leverage type hints).
    *   **Process:** Test-Driven Development (TDD) or Behavior-Driven Development (BDD). Continuous linting, formatting, and type checking.
*   **Configuration Management:**
    *   Pydantic's `BaseSettings` to manage application settings from environment variables or `.env` files.
*   **Security:**
    *   Automatic request data validation by Pydantic.
    *   SQLAlchemy ORM/SQLModel helps prevent SQL injection.
    *   Dependencies like `passlib` and `python-jose` for password hashing and JWTs if/when authentication is added.

**II. Core API Modules & Endpoints (MVP - Phase 1):**

The project will be structured with FastAPI `APIRouter` instances for different logical modules. Shared business logic will reside in service layers or utility modules. Database models will be defined using SQLModel.

**1. Company Profile & Settings Module (`routers/company.py`, `models/company_models.py`, `services/company_service.py`)**
    *   **JTBD:** "Efficiently manage my company's core identity, tax details, and complex ZUS parameters with precision."
    *   **SQLModel Models (also act as Pydantic schemas):**
        *   `CompanyProfile`: Stores primary company info (id, name, nip, address, etc.).
        *   `TaxSettings`: Linked to `CompanyProfile` (e.g., via `company_profile_id` foreign key). Stores VAT payer status, tax type (e.g., "ryczałt").
        *   `ZUSSettings` (or `ZUSContributionScheme`): Linked to `CompanyProfile`. Stores `fiscal_year_start` (or effective date), `zus_base_amount` (Decimal, default 5203.80), individual rates (Decimal) for Emerytalne (default 19.52), Rentowe (default 8.00), Wypadkowe (default 1.67), Sickness (default 2.45, boolean `is_sickness_active`), LaborFund (default 2.45), FEP (default 0.10, boolean `is_fep_active`). `health_insurance_tier` (Enum: 'low', 'medium', 'high').
    *   **Pydantic Schemas (for API input/output, may derive from SQLModel):** Separate `CompanyProfileCreate`, `CompanyProfileRead`, `ZUSSettingsUpdate`, etc., if different fields are needed for different operations.
    *   **API Endpoints (FastAPI APIRouter mounted at `/api/v1/company`):**
        *   `POST /profile/`: Create company profile.
        *   `GET /profile/`: Retrieve company profile.
        *   `PUT /profile/`: Update company profile.
        *   `GET /settings/tax/`: Retrieve tax settings.
        *   `PUT /settings/tax/`: Update tax settings.
        *   `GET /settings/zus/`: Retrieve current ZUS settings.
        *   `PUT /settings/zus/`: Update ZUS settings.
    *   **Key Logic/Services (`services/company_service.py`):** NIP validation. Default value provisioning for settings. Validation of rates (0-100) and ZUS base (positive).

**2. Client Management Module (`routers/clients.py`, `models/client_models.py`, `services/client_service.py`)**
    *   **JTBD:** "Effectively maintain my client database for invoicing and tracking."
    *   **SQLModel Model:** `Client`: id, name, nip, address_details (could be a JSON field or separate related model), contact_info.
    *   **API Endpoints (FastAPI APIRouter mounted at `/api/v1/clients`):** Full CRUD operations.
    *   **Key Logic/Services:** NIP format and checksum validation.

**3. Invoice Management Module (`routers/invoices.py`, `models/invoice_models.py`, `services/invoice_service.py`)**
    *   **JTBD:** "Seamlessly create, manage, track payments for, and generate PDFs of compliant Polish invoices."
    *   **SQLModel Models:**
        *   `Invoice`: id, `invoice_number` (str, unique), `client_id` (FK to Client), `issue_date`, `due_date`, `payment_terms`, `total_net` (Decimal), `total_gross` (Decimal), `total_vat` (Decimal), `status` (Enum: Draft, Issued, Paid, Archived), `currency` (str, default "PLN"). Related `InvoiceItem` models.
        *   `InvoiceItem`: id, `invoice_id` (FK to Invoice), `description`, `quantity` (Decimal), `unit_price_net` (Decimal), `vat_rate` (Decimal, default 23.00), `item_total_net` (Decimal), `item_total_gross` (Decimal), `item_total_vat` (Decimal).
    *   **API Endpoints (FastAPI APIRouter mounted at `/api/v1/invoices`):**
        *   `POST /`: Create a new invoice (request body includes invoice details and list of items).
        *   `GET /`: List invoices (with filtering by status, date, client; pagination).
        *   `GET /{invoice_id}/`: Retrieve a specific invoice (with its items).
        *   `PUT /{invoice_id}/`: Update an invoice.
        *   `DELETE /{invoice_id}/`: Delete an invoice (if "Draft").
        *   `POST /{invoice_id}/issue/`: Transition status to "Issued".
        *   `POST /{invoice_id}/mark-paid/`: Transition status to "Paid".
        *   `GET /{invoice_id}/pdf/`: Generate and return invoice as PDF (`StreamingResponse` or `FileResponse`).
    *   **Key Logic/Services (`services/invoice_service.py`):** Unique invoice numbering. Accurate `Decimal` calculations for all totals. Default VAT rate. PDF generation logic (e.g., using `reportlab` or HTML-to-PDF with `xhtml2pdf` or `WeasyPrint` run in a separate thread/process if blocking). Status transition validation.

**4. Expense Tracking Module (`routers/expenses.py`, `models/expense_models.py`, `services/expense_service.py`)**
    *   **JTBD:** "Quickly and accurately log my business expenses for tax purposes."
    *   **SQLModel Model:** `Expense`: id, `expense_date`, `vendor_name`, `description`, `category`, `amount_net` (Decimal), `vat_amount` (Decimal), `amount_gross` (Decimal), `payment_method`, `is_vat_deductible` (bool), `document_reference` (str, optional).
    *   **API Endpoints (FastAPI APIRouter mounted at `/api/v1/expenses`):** Full CRUD.
    *   **Key Logic/Services:** Calculation of gross from net+VAT or vice-versa if one is missing. Validation.

**5. Tax Calculation Engine & Reporting Module (`routers/reports.py`, `services/tax_calculations.py`, `services/zus_calculations.py`)**
    *   **JTBD:** "Reliably calculate my monthly tax (VAT, PIT 'ryczałt') and detailed ZUS obligations based on my financial activity and current system settings."
    *   **Services (No direct DB models for calculations, uses other models' data):**
        *   `services/vat_service.py` (or `tax_calculations.py`):
            *   Function `calculate_monthly_vat(db_session, month, year)`: Fetches invoices/expenses, calculates VAT collected, VAT paid, Net VAT due.
        *   `services/pit_service.py` (or `tax_calculations.py`):
            *   Function `calculate_monthly_pit_ryczalt(db_session, month, year)`: Fetches invoices, applies 12% ryczałt rate to IT income.
        *   `services/zus_service.py` (or `zus_calculations.py`):
            *   Function `calculate_monthly_zus(db_session, month, year, company_profile_id)`:
                *   Fetches current ZUS settings for the company.
                *   Uses `Decimal` for all calculations.
                *   Calculates each component (Emerytalne, Rentowe, etc.) based on ZUS base and active rates.
                *   Handles optional contributions (Chorobowe, FEP).
                *   Calculates Health Insurance based on income thresholds (logic to determine YTD income for tier may be complex for MVP, might require simplified input or YTD accumulation).
                *   Rounds each component and total to 0.01 PLN.
    *   **API Endpoints (FastAPI APIRouter mounted at `/api/v1/reports`):**
        *   `GET /monthly-summary/`: Query params `month` (YYYY-MM). Returns a comprehensive summary response model.
            *   Response Model (Pydantic): Includes total income, expenses, VAT details, PIT details, detailed ZUS breakdown (each component and total), and other metrics like #invoices, avg invoice amount.
        *   `GET /zus-summary/`: Query param `year` (YYYY). (Optional for MVP, could be yearly ZUS).
    *   **Key Logic:** Heavy use of `Decimal`. Precise rounding. Correct application of all configurable rules from settings. Logic for health insurance tier determination.

**III. Technical Requirements & Implementation Details (FastAPI Backend):**

*   **Database Schema & SQLModel:** Define all SQLModel classes representing database tables. Use Alembic for database migrations.
*   **Calculation Engine (`services/`):**
    *   All financial math uses `Decimal`. Encapsulate in service functions.
    *   All rates/rules are fetched from settings (via Company Profile related models) or app configuration.
    *   Implement Polish rounding standards (round half up to 0.01 PLN for final amounts).
    *   Validate calculation inputs rigorously.
*   **Data Validation (Pydantic):** Pydantic models automatically validate request bodies. Use custom validators for complex rules (e.g., NIP checksum).
*   **Code Quality:**
    *   Use type hints extensively (FastAPI relies on them). Run `Mypy`.
    *   `Flake8` for linting, `Black` for formatting.
    *   API documentation via FastAPI's auto-generated Swagger/ReDoc. Add descriptions to Pydantic models and path operations.
*   **Async Operations:** Design service functions and database interactions to be `async` where beneficial, using `await` with SQLAlchemy's async features or `databases` library.
*   **Configuration:** Use Pydantic's `BaseSettings` to load DB URLs, default rates, etc., from environment variables or a `.env` file.

**IV. Testing Strategy (FastAPI Backend):**

*   **Unit Tests (`pytest`):**
    *   Focus: Individual calculation functions within services (e.g., `calculate_single_zus_component`, `calculate_vat_on_item`), utility functions, Pydantic model custom validators.
    *   Coverage: Edge cases, rounding rules, optional contribution logic, formula correctness.
*   **Integration/E2E API Tests (`pytest` + FastAPI `TestClient`):**
    *   Focus: Full request-response cycles for ALL API endpoints.
    *   Coverage: Test API contracts (request/response schemas), business logic execution through API calls, data persistence and retrieval, error handling (4xx, 5xx status codes), impact of settings changes on report outputs. Simulate realistic user workflows.

**V. Development Plan & Task Breakdown (Illustrative - FastAPI Backend First):**

(Commit frequently after each logical, tested task)

1.  **Task FAPI_B01:** Project Setup: FastAPI, SQLModel, SQLite (async setup), `pytest`, `TestClient`, Linters/Formatters/Type Checker, `Decimal`, Pydantic `BaseSettings` for config. Basic "hello world" endpoint with tests. Setup Alembic for migrations.
2.  **Task FAPI_B02:** Company Profile & Settings Module - SQLModels & basic CRUD API (profile info).
3.  **Task FAPI_B03:** ZUS & Tax Settings - SQLModels & API for configuring (linked to Company Profile).
4.  **Task FAPI_B04:** Client Management Module - SQLModel & CRUD API. NIP validation logic.
5.  **Task FAPI_B05:** ZUS Calculation Service - Unit tests & implementation for all components (using `Decimal`, fetching settings).
6.  **Task FAPI_B06:** Health Insurance Logic (within ZUS Service) - Unit tests & implementation.
7.  **Task FAPI_B07:** Expense Tracking Module - SQLModel & CRUD API.
8.  **Task FAPI_B08:** VAT & PIT ("Ryczałt") Calculation Services - Unit tests & implementations.
9.  **Task FAPI_B09:** Invoice Module - SQLModels (Invoice, InvoiceItem) & Invoice creation API (data & calculations).
10. **Task FAPI_B10:** Invoice Module - Listing/retrieval, PDF generation (`StreamingResponse`).
11. **Task FAPI_B11:** Invoice Module - Status management endpoints.
12. **Task FAPI_B12:** Monthly Financial Summary Report API Endpoint - Integrate calculation services. Define comprehensive Pydantic response model.
13. **Task FAPI_B13:** Comprehensive E2E API testing for core workflows.
14. **Task FAPI_B14:** Review & Refine: Error handling, API consistency, auto-generated docs.
15. **Task FAPI_B15:** Data Backup consideration (script for SQLite for MVP).

**VI. Future Enhancements (Post-FastAPI Backend MVP):**

*   **Phase 2: Frontend UI Development** (e.g., React, Vue, Svelte consuming this API, or server-side rendering with Jinja2 if desired).
*   Authentication & Authorization (e.g., OAuth2 with JWTs, FastAPI has good support).
*   ...and other items from your previous detailed list.

This FastAPI blueprint provides a modern, performant, and well-structured approach to building your Polish accounting application's backend. The emphasis on type hints, Pydantic, and async capabilities will contribute to a robust and maintainable system.

---

## 📊 DEVELOPMENT PROGRESS TRACKER

### ✅ COMPLETED TASKS:
- **✅ FAPI_B01**: Project Setup Complete
  - FastAPI application structure with async SQLite database
  - SQLModel for database models with Company, Tax, and ZUS settings
  - Pydantic schemas for API request/response validation
  - Code quality tools: Black, Flake8, MyPy configuration
  - Environment-based configuration with pydantic-settings
  - **Status**: ✅ COMPLETE

- **✅ FAPI_B02**: Company Profile & Settings Module Complete
  - Company profile CRUD API endpoints
  - Tax settings management API
  - ZUS settings management API
  - Polish NIP validation with correct checksums
  - Comprehensive test suite (19/19 tests passing)
  - API documentation available at `/docs`
  - **Status**: ✅ COMPLETE - API working 100%

- **✅ FAPI_B04**: Client Management Module Complete
  - SQLModel Client model with full business information
  - Complete CRUD API endpoints at `/api/v1/clients`
  - Advanced features: pagination, search, NIP validation
  - Client summary endpoint for dropdowns
  - Search by NIP functionality
  - Soft delete (is_active flag) for data integrity
  - Comprehensive test suite (28 tests) - all passing
  - **Status**: ✅ COMPLETE - All features working 100%

### 🔄 CURRENT TASK:
- **🔄 FAPI_B05**: ZUS Calculation Service (NEXT)

### 📋 REMAINING TASKS:
- **FAPI_B05**: ZUS Calculation Service
- **FAPI_B06**: Health Insurance Logic
- **FAPI_B07**: Expense Tracking Module
- **FAPI_B08**: VAT & PIT Calculation Services
- **FAPI_B09**: Invoice Module - SQLModels & creation API
- **FAPI_B10**: Invoice Module - Listing/retrieval, PDF generation
- **FAPI_B11**: Invoice Module - Status management endpoints
- **FAPI_B12**: Monthly Financial Summary Reports
- **FAPI_B13**: Comprehensive E2E testing
- **FAPI_B14**: Review & refinement

### 📈 OVERALL PROGRESS: 3/14 tasks complete (21.4%)

**Last Updated**: 2025-06-06 13:30 CET

</MARKDOWN_DOCUMENT>