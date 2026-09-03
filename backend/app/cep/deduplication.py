import hashlib
from datetime import datetime
from typing import Optional
from app.models.domain import IntelligenceIncident

class IncidentDeduplicator:
    """
    Prevents duplicate incidents by generating deterministic fingerprints.
    """
    
    @staticmethod
    def generate_fingerprint(incident_type: str, region_id: int, active_time_bucket: str) -> str:
        """
        Creates a deterministic hash representing a unique incident occurrence.
        """
        raw_string = f"{incident_type}_{region_id}_{active_time_bucket}"
        return hashlib.sha256(raw_string.encode('utf-8')).hexdigest()
        
    @staticmethod
    def get_time_bucket(timestamp: datetime, bucket_hours: int = 6) -> str:
        """
        Buckets time into intervals (e.g., 6 hour chunks).
        """
        bucket_index = timestamp.hour // bucket_hours
        return f"{timestamp.date().isoformat()}_{bucket_index}"
        
    @staticmethod
    def is_duplicate(existing_incident: IntelligenceIncident, new_event_id: str) -> bool:
        """
        Checks if an event is already part of the incident.
        """
        if existing_incident.source_event_ids and new_event_id in existing_incident.source_event_ids:
            return True
        return False
