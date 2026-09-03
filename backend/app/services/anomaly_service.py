import math
from typing import List, Dict, Any
from datetime import datetime, timezone

class AnomalyDetectionService:
    """
    Identifies statistical anomalies in time-series data using Z-score.
    Useful for detecting sudden spikes in rainfall or disease cases.
    """
    
    @staticmethod
    def calculate_z_scores(values: List[float]) -> List[float]:
        if not values or len(values) < 2:
            return [0.0] * len(values)
            
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        std_dev = math.sqrt(variance)
        
        if std_dev == 0:
            return [0.0] * len(values)
            
        return [(x - mean) / std_dev for x in values]

    @staticmethod
    def detect_anomalies(data_points: List[Dict[str, Any]], value_key: str, base_threshold: float = 2.5) -> List[Dict[str, Any]]:
        """
        Takes a list of dictionaries with a specific value_key.
        Returns a list of identified anomalies with dynamic seasonality adjustment.
        """
        # Monsoon months (July, August, September) typically see spikes in rainfall/turbidity
        # We increase the threshold multiplier to suppress false positives during this season.
        SEASONALITY_MULTIPLIER = {
            7: 1.5, # July
            8: 1.5, # August
            9: 1.5  # September
        }

        values = [float(dp[value_key]) for dp in data_points]
        z_scores = AnomalyDetectionService.calculate_z_scores(values)
        
        mean = sum(values) / len(values) if values else 0
        
        anomalies = []
        for idx, (dp, z) in enumerate(zip(data_points, z_scores)):
            # Extract month to apply seasonality
            timestamp = dp.get("timestamp") or dp.get("date")
            month = timestamp.month if hasattr(timestamp, 'month') else datetime.now(timezone.utc).month
            
            # Apply multiplier if we are tracking rainfall or turbidity
            multiplier = 1.0
            if value_key in ["rainfall", "turbidity"] and month in SEASONALITY_MULTIPLIER:
                multiplier = SEASONALITY_MULTIPLIER[month]
                
            dynamic_threshold = base_threshold * multiplier

            if abs(z) > dynamic_threshold:
                severity = "HIGH" if abs(z) > (3.5 * multiplier) else "MEDIUM"
                anomalies.append({
                    "timestamp": timestamp,
                    "feature": value_key,
                    "observed_value": dp[value_key],
                    "expected_mean": round(mean, 2),
                    "z_score": round(z, 2),
                    "severity": severity,
                    "explanation": f"{value_key} spike detected. Observed: {dp[value_key]}, Expected Mean: {round(mean, 2)} (Z={round(z, 2)}). Seasonal threshold applied.",
                    "original_record": dp
                })
        return anomalies
