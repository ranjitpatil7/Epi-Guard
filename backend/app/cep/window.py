from typing import List, Dict
from datetime import datetime, timedelta, timezone
from app.realtime.event_schema import IntelligenceEvent

class TemporalWindowEngine:
    """
    Utility for managing and querying events within configurable temporal windows.
    """
    
    @staticmethod
    def get_events_in_window(events: List[IntelligenceEvent], window_delta: timedelta, reference_time: datetime = None) -> List[IntelligenceEvent]:
        """
        Filters events to only those occurring within the given timedelta leading up to reference_time.
        Handles out-of-order events by relying on the event's internal timestamp.
        """
        if reference_time is None:
            reference_time = datetime.now(timezone.utc)
            
        start_time = reference_time - window_delta
        
        # We also want to exclude events in the future (beyond reference_time)
        filtered_events = [
            e for e in events 
            if start_time <= e.timestamp <= reference_time
        ]
        return sorted(filtered_events, key=lambda x: x.timestamp)

    @staticmethod
    def group_events_by_region(events: List[IntelligenceEvent]) -> Dict[int, List[IntelligenceEvent]]:
        """Groups events by their region_id."""
        grouped = {}
        for e in events:
            if e.region_id not in grouped:
                grouped[e.region_id] = []
            grouped[e.region_id].append(e)
        return grouped

    @staticmethod
    def group_events_by_type(events: List[IntelligenceEvent]) -> Dict[str, List[IntelligenceEvent]]:
        """Groups events by their event_type."""
        grouped = {}
        for e in events:
            if e.event_type not in grouped:
                grouped[e.event_type] = []
            grouped[e.event_type].append(e)
        return grouped

    @staticmethod
    def calculate_event_velocity(events: List[IntelligenceEvent], window_delta: timedelta) -> float:
        """
        Calculates the velocity of events (events per hour).
        """
        if not events:
            return 0.0
            
        hours = window_delta.total_seconds() / 3600.0
        if hours <= 0:
            return 0.0
            
        return len(events) / hours

    @staticmethod
    def calculate_event_acceleration(events: List[IntelligenceEvent], window_delta: timedelta, reference_time: datetime = None) -> float:
        """
        Calculates the acceleration of events by comparing the first half of the window to the second half.
        Returns the change in velocity (events/hour/hour).
        """
        if reference_time is None:
            reference_time = datetime.now(timezone.utc)
            
        half_delta = window_delta / 2
        mid_time = reference_time - half_delta
        
        first_half_events = [e for e in events if e.timestamp < mid_time]
        second_half_events = [e for e in events if e.timestamp >= mid_time]
        
        v1 = TemporalWindowEngine.calculate_event_velocity(first_half_events, half_delta)
        v2 = TemporalWindowEngine.calculate_event_velocity(second_half_events, half_delta)
        
        hours = window_delta.total_seconds() / 3600.0
        if hours <= 0:
            return 0.0
            
        return (v2 - v1) / hours
