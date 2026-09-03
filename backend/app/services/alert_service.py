from sqlalchemy.ext.asyncio import AsyncSession
from app.models.domain import Alert

class AlertService:
    """
    Handles generation of early warning alerts based on risk levels.
    """
    
    @staticmethod
    async def generate_alerts_if_needed(db: AsyncSession, region_id: int, risk_score: float, risk_level: str):
        """
        Creates an alert in the database if the risk level is HIGH or CRITICAL.
        """
        if risk_level in ["HIGH", "CRITICAL"]:
            # Check if an active alert already exists for this region to prevent spam
            # (Stub for Phase 2: Just create it)
            alert = Alert(
                region_id=region_id,
                severity=risk_level,
                message=f"Early Warning: {risk_level} risk of water-borne disease outbreak detected. Please initiate preventive measures.",
                is_active=True
            )
            db.add(alert)
            await db.commit()
            return True
        return False
