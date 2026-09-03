from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
import math
from sqlalchemy import select, func, text, cast, Float
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.domain import Region, EnvironmentalData, DiseaseRecord, CommunityReport, Anomaly, RiskAssessment

class SpatiotemporalIntelligenceService:
    """
    Phase 6: Advanced Spatiotemporal Intelligence.
    Computes time-series lags, rolling windows, trend acceleration, and spatial propagation.
    """

    @staticmethod
    async def get_temporal_features(db: AsyncSession, region_id: int, target_date: datetime) -> Dict[str, float]:
        """Calculates lag, rolling mean, std, acceleration and seasonality for rainfall and disease."""
        if target_date.tzinfo is None:
            target_date = target_date.replace(tzinfo=timezone.utc)
            
        features = {}
        
        # Helper to get aggregated data for a specific window
        async def fetch_agg(model, column, agg_func, days_back_start, days_back_end):
            start = target_date - timedelta(days=days_back_start)
            end = target_date - timedelta(days=days_back_end)
            stmt = select(agg_func(getattr(model, column))).where(
                model.region_id == region_id,
                model.timestamp >= start if hasattr(model, 'timestamp') else model.date >= start,
                model.timestamp <= end if hasattr(model, 'timestamp') else model.date <= end
            )
            val = (await db.execute(stmt)).scalar()
            return float(val) if val is not None else 0.0

        # 1. Lags & Rolling Means (Rainfall)
        rain_1d = await fetch_agg(EnvironmentalData, 'rainfall', func.sum, 1, 0)
        rain_3d = await fetch_agg(EnvironmentalData, 'rainfall', func.sum, 3, 0)
        rain_7d = await fetch_agg(EnvironmentalData, 'rainfall', func.sum, 7, 0)
        rain_14d = await fetch_agg(EnvironmentalData, 'rainfall', func.sum, 14, 0)
        
        features["rainfall_lag_1d"] = rain_1d
        features["rainfall_lag_3d"] = rain_3d
        features["rainfall_lag_7d"] = rain_7d
        features["rainfall_lag_14d"] = rain_14d
        
        features["rainfall_rolling_mean_3d"] = rain_3d / 3.0
        features["rainfall_rolling_mean_7d"] = rain_7d / 7.0
        features["rainfall_rolling_mean_14d"] = rain_14d / 14.0

        # Disease Lags
        cases_1d = await fetch_agg(DiseaseRecord, 'case_count', func.sum, 1, 0)
        cases_3d = await fetch_agg(DiseaseRecord, 'case_count', func.sum, 3, 0)
        cases_7d = await fetch_agg(DiseaseRecord, 'case_count', func.sum, 7, 0)
        cases_14d = await fetch_agg(DiseaseRecord, 'case_count', func.sum, 14, 0)
        
        features["cases_lag_1d"] = cases_1d
        features["cases_lag_3d"] = cases_3d
        features["cases_lag_7d"] = cases_7d
        features["cases_lag_14d"] = cases_14d

        features["cases_rolling_mean_3d"] = cases_3d / 3.0
        features["cases_rolling_mean_7d"] = cases_7d / 7.0
        features["cases_rolling_mean_14d"] = cases_14d / 14.0

        # Standard Deviations (requires raw window queries)
        # Using PostgreSQL stddev_pop
        async def fetch_std(model, column, days):
            start = target_date - timedelta(days=days)
            stmt = select(func.stddev_pop(getattr(model, column))).where(
                model.region_id == region_id,
                model.timestamp >= start if hasattr(model, 'timestamp') else model.date >= start,
                model.timestamp <= target_date if hasattr(model, 'timestamp') else model.date <= target_date
            )
            val = (await db.execute(stmt)).scalar()
            return float(val) if val is not None else 0.0

        features["rainfall_rolling_std_7d"] = await fetch_std(EnvironmentalData, 'rainfall', 7)
        features["rainfall_rolling_std_14d"] = await fetch_std(EnvironmentalData, 'rainfall', 14)
        
        features["cases_rolling_std_7d"] = await fetch_std(DiseaseRecord, 'case_count', 7)
        features["cases_rolling_std_14d"] = await fetch_std(DiseaseRecord, 'case_count', 14)

        # Trend and Acceleration
        cases_prev_7d = await fetch_agg(DiseaseRecord, 'case_count', func.sum, 14, 7)
        features["cases_percentage_change"] = ((cases_7d - cases_prev_7d) / cases_prev_7d) if cases_prev_7d > 0 else 0.0
        
        cases_prev_prev_7d = await fetch_agg(DiseaseRecord, 'case_count', func.sum, 21, 14)
        vel1 = cases_7d - cases_prev_7d
        vel2 = cases_prev_7d - cases_prev_prev_7d
        features["cases_acceleration"] = vel1 - vel2

        # Seasonality Indicator (Monsoon approx: June-Sept)
        month = target_date.month
        features["is_monsoon_season"] = 1.0 if 6 <= month <= 9 else 0.0

        return features


    @staticmethod
    async def get_spatial_features(db: AsyncSession, region_id: int, target_date: datetime) -> Dict[str, float]:
        """Calculates PostGIS distance-weighted risk and neighbor propagation."""
        features = {}
        
        # 1. Get current region geom
        stmt_geom = select(Region.geometry).where(Region.id == region_id)
        geom_res = await db.execute(stmt_geom)
        geom = geom_res.scalar()
        if not geom:
            return features
            
        # 2. Neighboring Region Risk (within ~50km approx 0.5 degrees)
        # We calculate an inverse distance-weighted average risk of nearby regions.
        # Ensure target_date is timezone aware for queries
        if target_date.tzinfo is None:
            target_date = target_date.replace(tzinfo=timezone.utc)
            
        stmt_neighbors = text("""
            SELECT r.id, ST_Distance(r.geometry, CAST(:geom AS geometry)) as dist
            FROM regions r
            WHERE r.id != :region_id AND ST_DWithin(r.geometry, CAST(:geom AS geometry), 0.5)
        """)
        neighbors = await db.execute(stmt_neighbors, {"geom": geom.desc, "region_id": region_id})
        neighbor_rows = neighbors.fetchall()
        
        neighbor_risk_total = 0.0
        weight_total = 0.0
        
        for n_id, dist in neighbor_rows:
            # Fetch latest risk assessment for neighbor
            stmt_risk = select(RiskAssessment.risk_score).where(
                RiskAssessment.region_id == n_id,
                RiskAssessment.forecast_date <= target_date
            ).order_by(RiskAssessment.forecast_date.desc()).limit(1)
            r_val = (await db.execute(stmt_risk)).scalar()
            
            if r_val is not None:
                # Inverse distance weighting (+0.01 to avoid div by zero)
                weight = 1.0 / (dist + 0.01)
                neighbor_risk_total += r_val * weight
                weight_total += weight
                
        features["distance_weighted_neighbor_risk"] = (neighbor_risk_total / weight_total) if weight_total > 0 else 0.0
        features["neighbor_count"] = len(neighbor_rows)

        # 3. Nearby Anomaly Count
        stmt_anom = select(func.count(Anomaly.id)).join(
            Region, Anomaly.region_id == Region.id
        ).where(
            func.ST_DWithin(Region.geometry, geom, 0.5),
            Anomaly.timestamp >= target_date - timedelta(days=7),
            Anomaly.timestamp <= target_date
        )
        features["nearby_anomaly_count_7d"] = float((await db.execute(stmt_anom)).scalar() or 0)

        # 4. Community Report Density (Reports within ST_DWithin)
        stmt_reports = select(func.count(CommunityReport.id)).where(
            func.ST_DWithin(CommunityReport.location, geom, 0.5),
            CommunityReport.created_at >= target_date - timedelta(days=7),
            CommunityReport.created_at <= target_date
        )
        features["nearby_community_report_density_7d"] = float((await db.execute(stmt_reports)).scalar() or 0)

        # 5. Hotspot density heuristic
        features["hotspot_density"] = (
            (features["nearby_anomaly_count_7d"] * 2.0) + 
            features["nearby_community_report_density_7d"]
        )
        
        # 6. Regional risk propagation (Are neighbors significantly higher risk than us?)
        stmt_my_risk = select(RiskAssessment.risk_score).where(
            RiskAssessment.region_id == region_id,
            RiskAssessment.forecast_date <= target_date
        ).order_by(RiskAssessment.forecast_date.desc()).limit(1)
        my_risk = (await db.execute(stmt_my_risk)).scalar() or 0.0
        
        features["regional_risk_propagation"] = max(0.0, features["distance_weighted_neighbor_risk"] - my_risk)

        return features

    @staticmethod
    async def get_all_spatiotemporal_features(db: AsyncSession, region_id: int, target_date: datetime) -> Dict[str, float]:
        """Combine all temporal and spatial features."""
        temporal = await SpatiotemporalIntelligenceService.get_temporal_features(db, region_id, target_date)
        spatial = await SpatiotemporalIntelligenceService.get_spatial_features(db, region_id, target_date)
        return {**temporal, **spatial}
