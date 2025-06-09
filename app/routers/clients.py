"""Client management API endpoints."""

from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.client_models import Client
from app.schemas.client_schemas import (
    ClientCreate,
    ClientUpdate,
    ClientRead,
    ClientList,
    ClientSummary,
)
from app.services import client_service

router = APIRouter(prefix="/api/v1/clients", tags=["clients"])


@router.post("/", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    session: AsyncSession = Depends(get_session)
) -> Client:
    """Create a new client."""
    try:
        client = await client_service.create_client(
            session, client_data.model_dump()
        )
        return client
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=ClientList)
async def get_clients(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term"),
    active_only: bool = Query(True, description="Show only active clients"),
    session: AsyncSession = Depends(get_session)
) -> ClientList:
    """Get clients with pagination and optional search."""
    clients, total = await client_service.get_clients(
        session, page, per_page, search, active_only
    )
    
    pagination_info = client_service.calculate_pagination_info(total, page, per_page)
    
    return ClientList(
        clients=clients,
        **pagination_info
    )


@router.get("/summary/", response_model=List[ClientSummary])
async def get_clients_summary(
    session: AsyncSession = Depends(get_session)
) -> List[Client]:
    """Get a summary list of active clients (for dropdowns, etc.)."""
    return await client_service.get_active_clients_summary(session)


@router.get("/search/nip/{nip}", response_model=Optional[ClientRead])
async def search_client_by_nip(
    nip: str,
    session: AsyncSession = Depends(get_session)
) -> Optional[Client]:
    """Search for a client by NIP number."""
    return await client_service.search_clients_by_nip(session, nip)


@router.get("/{client_id}", response_model=ClientRead)
async def get_client(
    client_id: int,
    session: AsyncSession = Depends(get_session)
) -> Client:
    """Get a specific client by ID."""
    client = await client_service.get_client_by_id(session, client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    return client


@router.put("/{client_id}", response_model=ClientRead)
async def update_client(
    client_id: int,
    client_data: ClientUpdate,
    session: AsyncSession = Depends(get_session)
) -> Client:
    """Update a client."""
    try:
        update_data = client_data.model_dump(exclude_unset=True)
        updated_client = await client_service.update_client(
            session, client_id, update_data
        )
        
        if not updated_client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found"
            )
        
        return updated_client
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: int,
    session: AsyncSession = Depends(get_session)
) -> None:
    """Delete a client (soft delete)."""
    success = await client_service.delete_client(session, client_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
