from typing import List, Dict, Any, Type
from pydantic import BaseModel, ValidationError
from datetime import datetime, timezone

class DataQualityEngine:
    """
    Engine to evaluate data quality and validate incoming records.
    Calculates a score (0-100) based on:
    - Completeness (missing values)
    - Freshness (time since collection)
    - Plausibility (valid bounds, handled via Pydantic but we track rejected vs accepted)
    """

    def __init__(self):
        pass
        
    def evaluate_batch(self, raw_records: List[Dict[str, Any]], schema: Type[BaseModel]) -> Dict[str, Any]:
        """
        Validates a batch of records against a Pydantic schema and calculates a quality score.
        Returns accepted records, rejected records (with reasons), and the quality score.
        """
        accepted = []
        rejected = []
        
        total_fields_expected = 0
        fields_present = 0
        
        current_time = datetime.now(timezone.utc)
        total_age_seconds = 0
        
        for record in raw_records:
            try:
                # 1. Validation (Plausibility & Types)
                validated = schema(**record)
                accepted.append(validated)
                
                # 2. Completeness Check
                record_dict = validated.dict()
                for key, value in record_dict.items():
                    total_fields_expected += 1
                    if value is not None:
                        fields_present += 1
                        
                # 3. Freshness Check (if timestamp exists)
                timestamp = record_dict.get('timestamp') or record_dict.get('date')
                if timestamp:
                    # ensure it's timezone aware for math
                    if timestamp.tzinfo is None:
                        timestamp = timestamp.replace(tzinfo=timezone.utc)
                    age = max(0, (current_time - timestamp).total_seconds())
                    total_age_seconds += age
                
            except ValidationError as e:
                rejected.append({
                    "record": record,
                    "errors": e.errors()
                })

        # Calculate Scores
        completeness_score = 100.0
        if total_fields_expected > 0:
            completeness_score = (fields_present / total_fields_expected) * 100.0
            
        validity_score = 100.0
        if len(raw_records) > 0:
            validity_score = (len(accepted) / len(raw_records)) * 100.0
            
        freshness_score = 100.0
        if len(accepted) > 0:
            avg_age_days = (total_age_seconds / len(accepted)) / 86400.0
            # Deduct 5 points for every day old, max deduction 50
            freshness_score = max(50.0, 100.0 - (avg_age_days * 5.0))
            
        # Composite Data Quality Score (0-100)
        # Weights: Completeness 40%, Validity 40%, Freshness 20%
        overall_score = (completeness_score * 0.4) + (validity_score * 0.4) + (freshness_score * 0.2)

        return {
            "accepted": accepted,
            "rejected": rejected,
            "metrics": {
                "total_processed": len(raw_records),
                "total_accepted": len(accepted),
                "total_rejected": len(rejected),
                "completeness_score": round(completeness_score, 2),
                "validity_score": round(validity_score, 2),
                "freshness_score": round(freshness_score, 2),
                "overall_quality_score": round(overall_score, 2)
            }
        }
