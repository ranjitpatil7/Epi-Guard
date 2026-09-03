from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.feature_engineering_service import FeatureEngineeringService

class RiskEngineService:
    """
    Multi-Factor Risk Engine.
    Calculates a composite risk score (0-100) based on environmental,
    water quality, disease trends, and community reports.
    Provides transparent explainability.
    """

    @staticmethod
    def _determine_risk_level(score: float) -> str:
        if score < 20: return "LOW"
        if score < 40: return "GUARDED"
        if score < 60: return "MODERATE"
        if score < 80: return "HIGH"
        return "CRITICAL"

    @staticmethod
    async def calculate_regional_risk(db: AsyncSession, region_id: int, target_date: datetime) -> Dict[str, Any]:
        """
        Calculates the risk score and provides an explainable breakdown.
        """
        if target_date.tzinfo is None:
            target_date = target_date.replace(tzinfo=timezone.utc)
            
        features = await FeatureEngineeringService.get_all_features(db, region_id, target_date)
        
        score = 0.0
        contributing_factors = []
        
        # 1. Rainfall Factor (Max 25 pts)
        rainfall_7d = features.get("rainfall_7d", 0)
        if rainfall_7d > 100:
            pts = min(25, (rainfall_7d - 100) * 0.2)
            score += pts
            if pts > 10:
                contributing_factors.append(f"Heavy rainfall over 7 days ({rainfall_7d}mm): +{round(pts, 1)}")
                
        # 2. Disease Trend Factor (Max 35 pts)
        cases_7d = features.get("cases_7d", 0)
        cases_14d = features.get("cases_14d", 0)
        
        if cases_7d > 0:
            pts = min(35, cases_7d * 5)
            score += pts
            if cases_14d > 0 and cases_7d > (cases_14d - cases_7d):
                contributing_factors.append(f"Disease cases rapidly increasing ({cases_7d} recent cases): +{round(pts, 1)}")
            else:
                contributing_factors.append(f"Disease cases present ({cases_7d} cases): +{round(pts, 1)}")
                
        # 3. Community Reports Factor (Max 20 pts)
        reports_7d = features.get("reports_7d", 0)
        if reports_7d > 0:
            pts = min(20, reports_7d * 4)
            score += pts
            contributing_factors.append(f"Recent community reports ({reports_7d} reports): +{round(pts, 1)}")
            
        # 4. Geographic Vulnerability (Base risk for Demo)
        # In a real app this would query elevation, distance to water bodies, etc.
        geo_pts = 8.0 
        score += geo_pts
        contributing_factors.append(f"Geographic vulnerability profile: +{round(geo_pts, 1)}")
        
        final_score = min(100.0, max(0.0, score))
        
        return {
            "region_id": region_id,
            "calculation_timestamp": datetime.now(timezone.utc),
            "forecast_date": target_date,
            "risk_score": round(final_score, 1),
            "risk_level": RiskEngineService._determine_risk_level(final_score),
            "contributing_factors": contributing_factors,
            "features_used": features
        }

    @staticmethod
    async def calculate_forecasts(db: AsyncSession, region_id: int, current_risk: float) -> Dict[str, Any]:
        """Stubbed forecast engine preparing for Phase 3 ML."""
        # Basic simulation: risk decays or grows slightly over time.
        return {
            'forecast_24h': round(max(0.0, min(100.0, current_risk + 2.0)), 1),
            'forecast_3d': round(max(0.0, min(100.0, current_risk - 5.0)), 1),
            'forecast_7d': round(max(0.0, min(100.0, current_risk - 10.0)), 1)
        }

