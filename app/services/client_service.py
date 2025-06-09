"""Client management business logic."""

import math
from typing import Optional, List, Tuple
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.models.client_models import Client
from app.services.company_service import validate_nip


async def create_client(session: AsyncSession, client_data: dict) -> Client:
    """
    Create a new client.
    
    Args:
        session: Database session
        client_data: Client data
        
    Returns:
        Created Client
        
    Raises:
        ValueError: If NIP is invalid
    """
    # Validate NIP if provided
    if client_data.get("nip") and not validate_nip(client_data["nip"]):
        raise ValueError("Invalid NIP number")
    
    # Create client
    client = Client(**client_data)
    session.add(client)
    await session.commit()
    await session.refresh(client)
    
    return client


async def get_client_by_id(session: AsyncSession, client_id: int) -> Optional[Client]:
    """
    Get a client by ID.
    
    Args:
        session: Database session
        client_id: Client ID
        
    Returns:
        Client if found, None otherwise
    """
    statement = select(Client).where(Client.id == client_id)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_clients(
    session: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    active_only: bool = True
) -> Tuple[List[Client], int]:
    """
    Get clients with pagination and optional search.
    
    Args:
        session: Database session
        page: Page number (1-based)
        per_page: Items per page
        search: Search term for name, city, or email
        active_only: Filter only active clients
        
    Returns:
        Tuple of (clients list, total count)
    """
    # Build base query
    statement = select(Client)
    count_statement = select(func.count(Client.id))
    
    # Apply filters
    if active_only:
        statement = statement.where(Client.is_active == True)
        count_statement = count_statement.where(Client.is_active == True)
    
    if search:
        search_filter = or_(
            Client.name.ilike(f"%{search}%"),
            Client.city.ilike(f"%{search}%"),
            Client.email.ilike(f"%{search}%")
        )
        statement = statement.where(search_filter)
        count_statement = count_statement.where(search_filter)
    
    # Get total count
    count_result = await session.execute(count_statement)
    total = count_result.scalar()
    
    # Apply pagination and ordering
    offset = (page - 1) * per_page
    statement = statement.order_by(Client.name).offset(offset).limit(per_page)
    
    # Execute query
    result = await session.execute(statement)
    clients = result.scalars().all()
    
    return list(clients), total


async def update_client(
    session: AsyncSession,
    client_id: int,
    update_data: dict
) -> Optional[Client]:
    """
    Update a client.
    
    Args:
        session: Database session
        client_id: Client ID
        update_data: Data to update
        
    Returns:
        Updated Client if found, None otherwise
        
    Raises:
        ValueError: If NIP is invalid
    """
    # Get existing client
    client = await get_client_by_id(session, client_id)
    if not client:
        return None
    
    # Validate NIP if being updated
    if "nip" in update_data and update_data["nip"] and not validate_nip(update_data["nip"]):
        raise ValueError("Invalid NIP number")
    
    # Update fields
    for field, value in update_data.items():
        if hasattr(client, field):
            setattr(client, field, value)
    
    # Update timestamp
    client.updated_at = datetime.now(timezone.utc)
    
    await session.commit()
    await session.refresh(client)
    
    return client


async def delete_client(session: AsyncSession, client_id: int) -> bool:
    """
    Delete a client (soft delete by setting is_active to False).
    
    Args:
        session: Database session
        client_id: Client ID
        
    Returns:
        True if client was found and deleted, False otherwise
    """
    client = await get_client_by_id(session, client_id)
    if not client:
        return False
    
    client.is_active = False
    client.updated_at = datetime.now(timezone.utc)
    
    await session.commit()
    return True


async def get_active_clients_summary(session: AsyncSession) -> List[Client]:
    """
    Get a summary list of active clients (for dropdowns, etc.).
    
    Args:
        session: Database session
        
    Returns:
        List of active clients with basic info
    """
    statement = select(Client).where(Client.is_active == True).order_by(Client.name)
    result = await session.execute(statement)
    return list(result.scalars().all())


async def search_clients_by_nip(session: AsyncSession, nip: str) -> Optional[Client]:
    """
    Search for a client by NIP number.
    
    Args:
        session: Database session
        nip: NIP number to search for
        
    Returns:
        Client if found, None otherwise
    """
    if not nip:
        return None
    
    statement = select(Client).where(Client.nip == nip, Client.is_active == True)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


def calculate_pagination_info(total: int, page: int, per_page: int) -> dict:
    """
    Calculate pagination information.
    
    Args:
        total: Total number of items
        page: Current page
        per_page: Items per page
        
    Returns:
        Dictionary with pagination info
    """
    total_pages = math.ceil(total / per_page) if total > 0 else 1
    
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }
