import logging
from typing import List, Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.domain import IntelligenceIncident, IntelligenceEvent
from app.cep.spatial import SpatialCorrelationEngine
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

class IncidentCorrelator:
    """
    Correlates individual events and PatternMatches with existing incidents.
    Decides whether to create a new incident or update an existing one.
    """
    
    @staticmethod
    async def find_related_incidents(
        db: AsyncSession, 
        region_ids: List[int], 
        incident_type: str, 
        active_window: timedelta = timedelta(hours=6)
    ) -> List[IntelligenceIncident]:
        """
        Finds existing OPEN, INVESTIGATING, or ESCALATED incidents of the same type
        in the same or neighboring regions within the active time window.
        """
        if not region_ids:
            return []
            
        time_threshold = datetime.now(timezone.utc) - active_window
        
        # We need to find incidents that overlap with these regions.
        # This requires checking if the incident's region is in region_ids 
        # or if it's a neighbor (we'll fetch neighbors first).
        
        expanded_region_ids = set(region_ids)
        for r_id in region_ids:
            neighbors = await SpatialCorrelationEngine.get_neighboring_regions(db, r_id)
            expanded_region_ids.update(neighbors)
            
        stmt = select(IntelligenceIncident).where(
            and_(
                IntelligenceIncident.status.in_(["OPEN", "INVESTIGATING", "ESCALATED"]),
                IntelligenceIncident.incident_type == incident_type,
                IntelligenceIncident.last_updated_at >= time_threshold,
                IntelligenceIncident.region_id.in_(list(expanded_region_ids))
            )
        )
        
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def calculate_correlation_score(
        event: IntelligenceEvent, 
        incident: IntelligenceIncident
    ) -> Tuple[float, str]:
        """
        Calculates a correlation score (0.0 to 1.0) and provides a reason.
        """
        score = 0.0
        reasons = []
        
        # Temporal proximity
        time_diff = abs((event.timestamp - incident.last_updated_at).total_seconds())
        if time_diff < 3600: # 1 hour
            score += 0.4
            reasons.append("Close temporal proximity (<1h)")
        elif time_diff < 86400: # 24 hours
            score += 0.2
            reasons.append("Moderate temporal proximity (<24h)")
            
        # Spatial proximity (exact match)
        if event.region_id == incident.region_id:
            score += 0.5
            reasons.append("Exact spatial match")
            
        # Semantic mapping
        if incident.incident_type == "RAPID_RISK_ESCALATION" and event.event_type == "RISK_CHANGED":
            score += 0.3
            reasons.append("Direct semantic mapping (Risk Event -> Risk Incident)")
            
        score = min(1.0, score)
        return score, ", ".join(reasons)
