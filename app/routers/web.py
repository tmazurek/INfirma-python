"""Simple HTML web interface for testing (temporary - will be replaced in Phase 2)."""

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from typing import Optional

from app.database import get_session
from app.config import settings
from app.services import company_service, client_service, zus_service

router = APIRouter(tags=["web-interface"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with dashboard."""
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "version": settings.app_version
        }
    )


@router.get("/web/company", response_class=HTMLResponse)
async def company_page(
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """Company management page."""
    company_profile = await company_service.get_company_profile(session)
    tax_settings = None
    zus_settings = None
    
    if company_profile:
        tax_settings = await company_service.get_tax_settings(session, company_profile.id)
        zus_settings = await company_service.get_zus_settings(session, company_profile.id)
    
    return templates.TemplateResponse(
        "company.html",
        {
            "request": request,
            "version": settings.app_version,
            "company_profile": company_profile,
            "tax_settings": tax_settings,
            "zus_settings": zus_settings
        }
    )


@router.post("/web/company/create")
async def create_company(
    request: Request,
    name: str = Form(...),
    nip: str = Form(...),
    street: str = Form(...),
    city: str = Form(...),
    postal_code: str = Form(...),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_session)
):
    """Create company profile."""
    try:
        profile_data = {
            "name": name,
            "nip": nip,
            "street": street,
            "city": city,
            "postal_code": postal_code,
            "email": email,
            "phone": phone
        }
        
        await company_service.create_company_profile(session, profile_data)
        return RedirectResponse(url="/web/company?success=created", status_code=303)
        
    except ValueError as e:
        return RedirectResponse(url=f"/web/company?error={str(e)}", status_code=303)


@router.get("/web/clients", response_class=HTMLResponse)
async def clients_page(
    request: Request,
    page: int = 1,
    search: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
):
    """Clients management page."""
    clients, total = await client_service.get_clients(
        session, page=page, per_page=10, search=search
    )
    
    pagination_info = client_service.calculate_pagination_info(total, page, 10)
    
    return templates.TemplateResponse(
        "clients.html",
        {
            "request": request,
            "version": settings.app_version,
            "clients": clients,
            "pagination": pagination_info,
            "search": search or ""
        }
    )


@router.post("/web/clients/create")
async def create_client(
    request: Request,
    name: str = Form(...),
    nip: Optional[str] = Form(None),
    street: str = Form(...),
    city: str = Form(...),
    postal_code: str = Form(...),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_session)
):
    """Create client."""
    try:
        client_data = {
            "name": name,
            "nip": nip if nip else None,
            "street": street,
            "city": city,
            "postal_code": postal_code,
            "email": email,
            "phone": phone
        }
        
        await client_service.create_client(session, client_data)
        return RedirectResponse(url="/web/clients?success=created", status_code=303)
        
    except ValueError as e:
        return RedirectResponse(url=f"/web/clients?error={str(e)}", status_code=303)


@router.get("/web/zus", response_class=HTMLResponse)
async def zus_page(request: Request):
    """ZUS calculator page."""
    return templates.TemplateResponse(
        "zus.html",
        {
            "request": request,
            "version": settings.app_version
        }
    )


@router.post("/web/zus/calculate")
async def calculate_zus_web(
    request: Request,
    monthly_income: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_session)
):
    """Calculate ZUS via web form."""
    try:
        # Get company profile
        company_profile = await company_service.get_company_profile(session)
        if not company_profile:
            return RedirectResponse(
                url="/web/zus?error=No company profile found. Please create one first.",
                status_code=303
            )
        
        # Parse income
        income = None
        if monthly_income and monthly_income.strip():
            try:
                income = Decimal(monthly_income.replace(",", "."))
            except:
                return RedirectResponse(
                    url="/web/zus?error=Invalid income amount",
                    status_code=303
                )
        
        # Calculate ZUS
        result = await zus_service.calculate_monthly_zus(
            session, company_profile.id, income
        )
        
        return templates.TemplateResponse(
            "zus_result.html",
            {
                "request": request,
                "version": settings.app_version,
                "result": result,
                "monthly_income": income
            }
        )
        
    except Exception as e:
        return RedirectResponse(
            url=f"/web/zus?error={str(e)}",
            status_code=303
        )
