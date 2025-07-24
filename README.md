# INfirma - Polish Accounting Application

A modern FastAPI-based accounting application designed specifically for Polish IT freelancers and small businesses using the "ryczałt" tax system.

## 🚀 Features

- **Company Management**: Register and manage company information
- **Client Management**: Track client details and relationships
- **Invoice Management**: Create, track, and manage invoices
- **Expense Tracking**: Record and categorize business expenses
- **Tax Calculations**: Automated Polish tax calculations for "ryczałt" system
- **ZUS Contributions**: Calculate social security contributions
- **Financial Reports**: Generate comprehensive financial reports
- **RESTful API**: Modern FastAPI-based REST API with automatic documentation

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: SQLite with SQLModel ORM
- **Data Validation**: Pydantic models
- **Testing**: pytest with async support
- **Code Quality**: Black, Flake8, MyPy
- **Documentation**: Automatic API docs with Swagger UI and ReDoc

## 📋 Requirements

- Python 3.11 or higher
- pip or poetry for dependency management

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/tmazurek/INfirma-python.git
cd INfirma-python
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
uvicorn app.main:app --reload
```

The application will be available at:
- **API**: http://localhost:8000
- **Interactive API Documentation**: http://localhost:8000/docs
- **Alternative API Documentation**: http://localhost:8000/redoc
- **Web Interface**: http://localhost:8000/ (temporary testing UI)

## 📚 API Documentation

The API provides comprehensive endpoints for:

### Core Resources
- `/api/v1/companies/` - Company management
- `/api/v1/clients/` - Client management
- `/api/v1/invoices/` - Invoice operations
- `/api/v1/expenses/` - Expense tracking
- `/api/v1/taxes/` - Tax calculations
- `/api/v1/zus/` - ZUS contribution calculations

### Key Features
- Automatic request/response validation
- Type hints and schema documentation
- Async/await support for better performance
- Comprehensive error handling

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_company_api.py
```

## 🏗️ Project Structure

```
INfirma-python/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Application configuration
│   ├── database.py          # Database setup and connection
│   ├── models/              # SQLModel database models
│   ├── routers/             # FastAPI route handlers
│   ├── schemas/             # Pydantic request/response schemas
│   └── services/            # Business logic layer
├── tests/                   # Test suite
├── templates/               # HTML templates (temporary UI)
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Tool configuration
└── README.md               # This file
```

## ⚙️ Configuration

The application uses environment-based configuration. Key settings include:

- `DATABASE_URL`: Database connection string
- `APP_NAME`: Application name
- `APP_VERSION`: Application version
- `DEBUG`: Debug mode toggle

## 🇵🇱 Polish Tax System Support

This application is specifically designed for the Polish tax system:

- **Ryczałt Tax Calculations**: Automated calculations for flat-rate taxation
- **ZUS Contributions**: Social security contribution calculations
- **VAT Handling**: Support for Polish VAT regulations
- **Financial Year**: Polish financial year compliance

## 🔧 Development

### Code Quality Tools

```bash
# Format code
black app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/
```

### Database Migrations

The application uses SQLModel with automatic table creation. For production deployments, consider implementing proper migration management.

## 📖 Documentation

- [Phase 1 Development Plan](phase1.md) - Detailed backend development roadmap
- [Phase 2 Development Plan](phase2.md) - Frontend development plans
- [Testing UI Guide](TESTING_UI.md) - Temporary UI testing instructions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the API documentation at `/docs` endpoint
- Review the test files for usage examples

## 🗺️ Roadmap

- **Phase 1**: ✅ Backend API development with core accounting features
- **Phase 2**: 🔄 Modern SPA frontend development
- **Phase 3**: 📋 Advanced reporting and analytics
- **Phase 4**: 🔐 Multi-user support and authentication

---

**Note**: This application is currently in active development. The temporary HTML UI is provided for testing purposes and will be replaced with a modern SPA in Phase 2.
