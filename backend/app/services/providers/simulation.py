import random
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.services.providers.base import BaseDataProvider

class SimulationDataProvider(BaseDataProvider):
    """
    Software-only demo provider that generates internally consistent, correlated data.
    Higher rainfall -> Higher turbidity -> More community reports -> Higher disease cases.
    """
    
    def _generate_daily_series(self, start_date: datetime, end_date: datetime) -> List[datetime]:
        """Generate a list of daily timestamps."""
        days = (end_date - start_date).days
        return [start_date + timedelta(days=i) for i in range(max(1, days + 1))]

    async def fetch_environmental_data(self, region_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        dates = self._generate_daily_series(start_date, end_date)
        records = []
        
        # Base trends
        base_temp = random.uniform(22.0, 28.0)
        is_monsoon = start_date.month in [6, 7, 8, 9]
        
        for d in dates:
            # Simulate a continuous weather pattern with some random walk
            temp = random.gauss(base_temp + (2.0 if not is_monsoon else -2.0), 1.5)
            humidity = random.gauss(85.0 if is_monsoon else 65.0, 5.0)
            
            # Rainfall bursts
            rainfall = 0.0
            if random.random() < (0.6 if is_monsoon else 0.1):
                rainfall = random.expovariate(1.0 / (40.0 if is_monsoon else 10.0))
            
            records.append({
                "region_id": region_id,
                "timestamp": d,
                "temperature": max(15.0, min(45.0, temp)),
                "humidity": max(30.0, min(100.0, humidity)),
                "rainfall": max(0.0, rainfall)
            })
        return records

    async def fetch_water_quality_data(self, region_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        # For realistic simulation, we need to base water quality on rainfall.
        # Since this provider interface is abstract, in a real scenario we'd query real API.
        # Here we just generate it, but we'll try to sync it conceptually if called sequentially.
        # We will use random seeds based on region_id and date to keep cross-provider correlation stable!
        
        dates = self._generate_daily_series(start_date, end_date)
        records = []
        
        for d in dates:
            random.seed(f"weather_{region_id}_{d.strftime('%Y-%m-%d')}")
            is_monsoon = d.month in [6, 7, 8, 9]
            rainfall = 0.0
            if random.random() < (0.6 if is_monsoon else 0.1):
                rainfall = random.expovariate(1.0 / (40.0 if is_monsoon else 10.0))
            
            # Correlation: High rainfall -> High turbidity and lower pH
            # Reset seed for independent noise
            random.seed()
            
            base_turbidity = 2.0 + (rainfall * 0.15)
            turbidity = max(0.5, random.gauss(base_turbidity, base_turbidity * 0.2))
            
            ph = random.gauss(7.2 - (rainfall * 0.01), 0.3)
            
            # Coliform probability increases with rainfall and turbidity
            coliform_prob = min(0.9, 0.05 + (turbidity * 0.02) + (rainfall * 0.005))
            coliform_presence = random.random() < coliform_prob
            
            records.append({
                "region_id": region_id,
                "timestamp": d,
                "turbidity": turbidity,
                "ph": max(6.0, min(8.5, ph)),
                "coliform_presence": coliform_presence
            })
        return records

    async def fetch_disease_data(self, region_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        dates = self._generate_daily_series(start_date, end_date)
        records = []
        
        for d in dates:
            # Sync with rainfall using same deterministic seed logic
            random.seed(f"weather_{region_id}_{d.strftime('%Y-%m-%d')}")
            is_monsoon = d.month in [6, 7, 8, 9]
            rainfall = 0.0
            if random.random() < (0.6 if is_monsoon else 0.1):
                rainfall = random.expovariate(1.0 / (40.0 if is_monsoon else 10.0))
            random.seed()
            
            # Cases lag behind rainfall/contamination. We'll simplify and say high recent probability
            # drives base risk.
            base_cases = 0 if not is_monsoon else 2
            if rainfall > 50:
                base_cases += int(rainfall / 20)
                
            cases = max(0, int(random.gauss(base_cases, 2)))
            
            if cases > 0:
                records.append({
                    "region_id": region_id,
                    "date": d,
                    "disease_type": random.choice(["Cholera", "Typhoid", "Acute Diarrheal Disease"]),
                    "case_count": cases
                })
        return records

    async def fetch_community_reports(self, region_id: int, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        dates = self._generate_daily_series(start_date, end_date)
        records = []
        
        for d in dates:
            random.seed(f"weather_{region_id}_{d.strftime('%Y-%m-%d')}")
            is_monsoon = d.month in [6, 7, 8, 9]
            rainfall = 0.0
            if random.random() < (0.6 if is_monsoon else 0.1):
                rainfall = random.expovariate(1.0 / (40.0 if is_monsoon else 10.0))
            random.seed()
            
            report_prob = 0.05 + (0.3 if rainfall > 50 else 0)
            
            if random.random() < report_prob:
                templates = [
                    "Water looks very murky today.",
                    "Several people in my village are sick with stomach pain.",
                    "Flooding has reached the main well.",
                    "The water smells bad since yesterday's rain.",
                    "We need fresh drinking water supplies."
                ]
                text = random.choice(templates)
                severity = 0.5 + (0.4 if "sick" in text or "Flooding" in text else 0.0) + random.uniform(-0.1, 0.1)
                
                records.append({
                    "region_id": region_id,
                    "timestamp": d,
                    "text_content": text,
                    "nlp_severity": max(0.0, min(1.0, severity))
                })
        return records
