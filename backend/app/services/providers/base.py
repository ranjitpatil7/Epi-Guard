from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

class BaseDataProvider(ABC):
    """
    Abstract Base Class for Data Providers.
    All data providers (real or simulated) must implement these methods.
    """
    
    @abstractmethod
    async def fetch_environmental_data(self, region_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch weather/environmental data for a region."""
        pass
        
    @abstractmethod
    async def fetch_water_quality_data(self, region_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch water quality records for a region."""
        pass
        
    @abstractmethod
    async def fetch_disease_data(self, region_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch disease surveillance records."""
        pass
        
    @abstractmethod
    async def fetch_community_reports(self, region_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch community submitted reports."""
        pass
