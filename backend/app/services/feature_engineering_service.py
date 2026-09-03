from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.domain import EnvironmentalData, DiseaseRecord, CommunityReport, WaterQualityRecord

class FeatureEngineeringService:
    """
    Service to compute ML-ready time-series aggregates for a region.
    """
    
    @staticmethod
    async def get_rainfall_features(db: AsyncSession, region_id: int, target_date: datetime):
        """Calculates rainfall_24h, rainfall_7d, and rainfall_30d."""
        if target_date.tzinfo is None:
            target_date = target_date.replace(tzinfo=timezone.utc)
            
        features = {}
        periods = [("24h", 1), ("7d", 7), ("30d", 30)]
        
        for name, days in periods:
            start_date = target_date - timedelta(days=days)
            stmt = select(func.sum(EnvironmentalData.rainfall)).where(
                EnvironmentalData.region_id == region_id,
                EnvironmentalData.timestamp >= start_date,
                EnvironmentalData.timestamp <= target_date
            )
            result = await db.execute(stmt)
            val = result.scalar()
            features[f"rainfall_{name}"] = float(val) if val is not None else 0.0
            
        return features

    @staticmethod
    async def get_disease_features(db: AsyncSession, region_id: int, target_date: datetime):
        """Calculates cases_7d, cases_14d, cases_30d."""
        if target_date.tzinfo is None:
            target_date = target_date.replace(tzinfo=timezone.utc)
            
        features = {}
        periods = [("7d", 7), ("14d", 14), ("30d", 30)]
        
        for name, days in periods:
            start_date = target_date - timedelta(days=days)
            stmt = select(func.sum(DiseaseRecord.case_count)).where(
                DiseaseRecord.region_id == region_id,
                DiseaseRecord.date >= start_date,
                DiseaseRecord.date <= target_date
            )
            result = await db.execute(stmt)
            val = result.scalar()
            features[f"cases_{name}"] = int(val) if val is not None else 0
            
        return features

    @staticmethod
    async def get_community_features(db: AsyncSession, region_id: int, target_date: datetime):
        """Calculates community reports count over 7 days."""
        if target_date.tzinfo is None:
            target_date = target_date.replace(tzinfo=timezone.utc)
            
        start_date = target_date - timedelta(days=7)
        stmt = select(func.count(CommunityReport.id)).where(
            CommunityReport.location != None, # Simplified proxy for region check if we assumed spatial mapping
            # Actually, our schema doesn't have region_id on CommunityReport currently, it uses PostGIS location.
            # To query it by region, we would need to join with Region via ST_Contains.
        )
        
        from app.models.domain import Region
        stmt = select(func.count(CommunityReport.id)).join(
            Region, func.ST_Contains(Region.geometry, CommunityReport.location)
        ).where(
            Region.id == region_id,
            CommunityReport.created_at >= start_date,
            CommunityReport.created_at <= target_date
        )
        
        result = await db.execute(stmt)
        val = result.scalar()
        
        return {
            "reports_7d": int(val) if val is not None else 0
        }
        
    @staticmethod
    async def get_all_features(db: AsyncSession, region_id: int, target_date: datetime):
        """Compiles all feature vectors for risk modeling."""
        rainfall = await FeatureEngineeringService.get_rainfall_features(db, region_id, target_date)
        disease = await FeatureEngineeringService.get_disease_features(db, region_id, target_date)
        reports = await FeatureEngineeringService.get_community_features(db, region_id, target_date)
        
        # Extract Water Quality Features
        water_stmt = select(
            func.avg(WaterQualityRecord.turbidity),
            func.avg(WaterQualityRecord.ph)
        ).where(
            WaterQualityRecord.region_id == region_id,
            WaterQualityRecord.timestamp >= (target_date - timedelta(days=7)),
            WaterQualityRecord.timestamp <= target_date
        )
        water_res = await db.execute(water_stmt)
        turb, ph = water_res.first()
        water_features = {
            "turbidity_7d_avg": float(turb) if turb else 5.0, # default clean water
            "ph_7d_avg": float(ph) if ph else 7.0
        }

        # Extract Env Averages (Temp/Humidity)
        env_stmt = select(
            func.avg(EnvironmentalData.temperature),
            func.avg(EnvironmentalData.humidity)
        ).where(
            EnvironmentalData.region_id == region_id,
            EnvironmentalData.timestamp >= (target_date - timedelta(days=7)),
            EnvironmentalData.timestamp <= target_date
        )
        env_res = await db.execute(env_stmt)
        temp, hum = env_res.first()
        env_features = {
            "temperature_7d_avg": float(temp) if temp else 25.0,
            "humidity_7d_avg": float(hum) if hum else 60.0
        }

        # Calculate Disease Growth Rate
        cases_7d = disease.get("cases_7d", 0)
        cases_14d = disease.get("cases_14d", 0)
        cases_prev_7d = cases_14d - cases_7d
        growth_rate = 0.0
        if cases_prev_7d > 0:
            growth_rate = (cases_7d - cases_prev_7d) / cases_prev_7d
        disease["disease_growth_rate"] = growth_rate

        # Get Anomalies
        from app.models.domain import Anomaly
        anom_stmt = select(func.count(Anomaly.id)).where(
            Anomaly.region_id == region_id,
            Anomaly.timestamp >= (target_date - timedelta(days=7)),
            Anomaly.timestamp <= target_date
        )
        anom_res = await db.execute(anom_stmt)
        anomaly_count = anom_res.scalar() or 0
        
        # Add Severe Reports Stub
        reports["severe_reports_7d"] = reports.get("reports_7d", 0) // 3  # Basic ratio for now

        return {
            **rainfall,
            **disease,
            **reports,
            **water_features,
            **env_features,
            "anomaly_count_7d": anomaly_count
        }
