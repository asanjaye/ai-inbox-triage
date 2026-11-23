"""Audit log endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_session
from ...models import AuditLog, AuditAction
from ...services import AuditService

router = APIRouter()


async def get_audit_service(session: AsyncSession = Depends(get_session)) -> AuditService:
    return AuditService(session)


@router.get("/", response_model=list[AuditLog])
async def list_audit_logs(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    service: AuditService = Depends(get_audit_service),
):
    """
    List audit logs with optional filters.
    
    Returns immutable audit trail of all system actions.
    """
    action_enum = AuditAction(action) if action else None
    return await service.get_logs(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action_enum,
        limit=limit,
        offset=offset,
    )


@router.get("/entity/{entity_type}/{entity_id}", response_model=list[AuditLog])
async def get_entity_history(
    entity_type: str,
    entity_id: str,
    service: AuditService = Depends(get_audit_service),
):
    """Get complete audit history for a specific entity."""
    return await service.get_entity_history(entity_type, entity_id)
