# 🧪 InFirma Testing Interface

This is a **temporary HTML interface** for testing the InFirma API functionality. It will be replaced with a modern Vue.js Single Page Application in Phase 2.

## 🚀 Quick Start

1. **Start the server:**
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```

2. **Open your browser:**
   ```
   http://localhost:8000/
   ```

## 📱 Available Pages

### 🏠 Dashboard (`/`)
- Overview of all modules and their status
- Progress tracking (currently 5/14 tasks complete - 35.7%)
- Quick navigation to all features

### 🏢 Company Management (`/web/company`)
- **Create company profile** with NIP validation
- **View current settings** (company info, tax settings, ZUS settings)
- **Polish NIP validation** with proper checksums
- Integration with existing company API endpoints

### 👥 Client Management (`/web/clients`)
- **Add new clients** with optional NIP validation
- **View all clients** with pagination (10 per page)
- **Search functionality** by name, city, or email
- **Client statistics** (total, active, inactive)
- Full CRUD operations through forms

### 💰 ZUS Calculator (`/web/zus`)
- **Monthly ZUS calculation** with optional income input
- **Detailed breakdown** of all contributions:
  - Emerytalne (19.52%)
  - Rentowe (8.00%)
  - Wypadkowe (1.67%)
  - Chorobowe (2.45%, optional)
  - Labor Fund (2.45%)
  - FEP (0.10%, optional)
- **Health insurance calculation** with tier-based logic
- **Total monthly payment** summary
- **Professional result display** with proper Polish formatting

## ✨ Features

### 🎨 Design
- **Responsive design** that works on desktop and mobile
- **Clean, professional styling** with modern CSS
- **Intuitive navigation** with clear visual hierarchy
- **Success/error messaging** for user feedback

### 🔧 Technical
- **Form validation** with proper error handling
- **Integration with FastAPI backend** using existing endpoints
- **Jinja2 templating** with template inheritance
- **Mobile-responsive** grid layouts

### 📊 Data Display
- **Professional tables** with proper formatting
- **Polish currency formatting** (PLN)
- **Status indicators** (active/inactive, success/error)
- **Pagination controls** for large datasets

## 🧪 Testing Workflow

1. **Start with Company Setup:**
   - Go to `/web/company`
   - Create your company profile with valid Polish NIP
   - Verify tax and ZUS settings are created automatically

2. **Add Some Clients:**
   - Go to `/web/clients`
   - Add a few test clients (with and without NIP)
   - Test the search functionality
   - Verify pagination works

3. **Calculate ZUS:**
   - Go to `/web/zus`
   - Try calculations with different income levels
   - Verify all contributions are calculated correctly
   - Check health insurance tier logic

4. **API Documentation:**
   - Visit `/docs` for complete API documentation
   - Test API endpoints directly through Swagger UI

## ⚠️ Important Notes

- **This is a temporary interface** - clearly marked throughout
- **Will be deleted** when Vue.js SPA is implemented in Phase 2
- **For testing purposes only** - not production-ready
- **No authentication** - single-user testing environment
- **SQLite database** - data is persistent between sessions

## 🔗 API Integration

The HTML interface uses these API endpoints:
- `POST /api/v1/company/profile/` - Create company
- `GET /api/v1/company/profile/` - Get company info
- `POST /api/v1/clients/` - Create client
- `GET /api/v1/clients/` - List clients with pagination/search
- `POST /api/v1/zus/calculate/` - Calculate ZUS contributions

## 📈 Current Status

**Completed Modules (5/14 - 35.7%):**
- ✅ Project Setup
- ✅ Company Profile & Settings
- ✅ Client Management
- ✅ ZUS Calculation Service
- ✅ Health Insurance Logic

**Next Steps:**
- 🔄 Expense Tracking Module
- ⏳ Invoice Management
- ⏳ VAT & PIT Calculations
- ⏳ Monthly Reports

## 🎯 Phase 2 Preview

In Phase 2, this will be replaced with:
- **Vue.js 3** with Composition API
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **Vue Router** for navigation
- **Pinia** for state management
- **Modern component architecture**

---

**Happy Testing! 🚀**
