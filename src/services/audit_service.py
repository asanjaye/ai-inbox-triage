"""Audit logging service - immutable record of all actions."""
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AuditLog, AuditAction
from ..database import AuditLogTable


class AuditService:
    """Service for recording and querying audit logs."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def log(
        self,
        action: AuditAction,
        entity_type: str,
        entity_id: str,
        actor: str = "system",
        details: Optional[dict[str, Any]] = None,
    ) -> AuditLog:
        """Record an audit log entry."""
        log_entry = AuditLog(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor=actor,
            details=details,
        )
        
        db_entry = AuditLogTable(
            id=log_entry.id,
            timestamp=log_entry.timestamp,
            action=log_entry.action.value,
            entity_type=log_entry.entity_type,
            entity_id=log_entry.entity_id,
            actor=log_entry.actor,
            details=log_entry.details,
        )
        
        self.session.add(db_entry)
        await self.session.commit()
        
        return log_entry
    
    async def get_logs(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Query audit logs with optional filters."""
        query = select(AuditLogTable)
        
        if entity_type:
            query = query.where(AuditLogTable.entity_type == entity_type)
        if entity_id:
            query = query.where(AuditLogTable.entity_id == entity_id)
        if action:
            query = query.where(AuditLogTable.action == action.value)
        
        query = query.order_by(desc(AuditLogTable.timestamp))
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        rows = result.scalars().all()
        
        return [
            AuditLog(
                id=row.id,
                timestamp=row.timestamp,
                action=AuditAction(row.action),
                entity_type=row.entity_type,
                entity_id=row.entity_id,
                actor=row.actor,
                details=row.details,
            )
            for row in rows
        ]
    
    async def get_entity_history(self, entity_type: str, entity_id: str) -> list[AuditLog]:
        """Get complete audit history for a specific entity."""
        return await self.get_logs(entity_type=entity_type, entity_id=entity_id, limit=1000)
