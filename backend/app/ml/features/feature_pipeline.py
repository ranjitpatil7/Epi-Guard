from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.feature_engineering_service import FeatureEngineeringService
from app.services.spatiotemporal_service import SpatiotemporalIntelligenceService

class FeatureEngineeringPipeline:
    """
    ML Data Pipeline for feature extraction.
    Transforms raw database signals into the exact feature vector expected by the XGBoost model.
    """
    
    # The exact features required by the XGBoost model in order.
    REQUIRED_FEATURES = [
        "rainfall_24h",
        "rainfall_7d",
        "temperature_7d_avg",
        "humidity_7d_avg",
        "turbidity_7d_avg",
        "ph_7d_avg",
        "cases_7d",
        "cases_14d",
        "disease_growth_rate",
        "reports_7d",
        "severe_reports_7d",
        "anomaly_count_7d",
        # Phase 6 Spatiotemporal Features
        "rainfall_lag_1d",
        "rainfall_lag_3d",
        "rainfall_lag_7d",
        "rainfall_lag_14d",
        "rainfall_rolling_mean_3d",
        "rainfall_rolling_mean_7d",
        "rainfall_rolling_mean_14d",
        "cases_lag_1d",
        "cases_lag_3d",
        "cases_lag_7d",
        "cases_lag_14d",
        "cases_rolling_mean_3d",
        "cases_rolling_mean_7d",
        "cases_rolling_mean_14d",
        "rainfall_rolling_std_7d",
        "rainfall_rolling_std_14d",
        "cases_rolling_std_7d",
        "cases_rolling_std_14d",
        "cases_percentage_change",
        "cases_acceleration",
        "is_monsoon_season",
        "distance_weighted_neighbor_risk",
        "neighbor_count",
        "nearby_anomaly_count_7d",
        "nearby_community_report_density_7d",
        "hotspot_density",
        "regional_risk_propagation"
    ]

    @staticmethod
    async def extract_features(db: AsyncSession, region_id: int, target_date: datetime) -> Dict[str, float]:
        """
        Extracts all ML features for a region at a specific date.
        Returns a dictionary of feature values.
        """
        raw_features = await FeatureEngineeringService.get_all_features(db, region_id, target_date)
        spatio_features = await SpatiotemporalIntelligenceService.get_all_spatiotemporal_features(db, region_id, target_date)
        
        all_features = {**raw_features, **spatio_features}
        
        vector = {}
        for feat in FeatureEngineeringPipeline.REQUIRED_FEATURES:
            # Default to 0.0 if a feature is completely missing (DataQualityEngine should flag this later)
            vector[feat] = float(all_features.get(feat, 0.0))
            
        return vector

    @staticmethod
    def get_feature_names() -> List[str]:
        return FeatureEngineeringPipeline.REQUIRED_FEATURES
