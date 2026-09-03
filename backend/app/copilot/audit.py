# Copilot Audit Module
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.domain import AuditLog
from datetime import datetime

async def log_copilot_action(db: AsyncSession, user_id: int, action: str, details: dict):
    # Construct a descriptive action string since AuditLog lacks a details field
    query = details.get("query", "Unknown query")[:150]
    action_str = f"{action}: {query}"
    
    log_entry = AuditLog(
        user_id=user_id,
        action=action_str,
    )
    db.add(log_entry)
    # The caller will commit
