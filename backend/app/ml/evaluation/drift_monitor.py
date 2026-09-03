import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.domain import ModelDriftEvent
from scipy.stats import ks_2samp, wasserstein_distance

class ModelDriftMonitor:
    """
    Monitors feature distributions for data drift using PSI (Population Stability Index).
    """
    
    @staticmethod
    def calculate_psi(expected: pd.Series, actual: pd.Series, buckets: int = 10) -> float:
        """
        Calculates Population Stability Index.
        PSI < 0.1: No significant changes
        PSI >= 0.1 and < 0.2: Moderate changes
        PSI >= 0.2: Significant changes (Drift detected)
        """
        def get_breakpoints(data):
            # Using quantiles
            try:
                return np.unique(np.percentile(data, np.arange(0, 101, 100/buckets)))
            except Exception:
                return np.linspace(min(data), max(data), buckets+1)
                
        breakpoints = get_breakpoints(expected)
        
        expected_percents = np.histogram(expected, breakpoints)[0] / len(expected)
        actual_percents = np.histogram(actual, breakpoints)[0] / len(actual)
        
        # Avoid division by zero or log(0)
        expected_percents = np.where(expected_percents == 0, 0.0001, expected_percents)
        actual_percents = np.where(actual_percents == 0, 0.0001, actual_percents)
        
        psi = np.sum((actual_percents - expected_percents) * np.log(actual_percents / expected_percents))
        return float(psi)

    @staticmethod
    def calculate_ks_test(expected: pd.Series, actual: pd.Series) -> float:
        """Kolmogorov-Smirnov test for drift detection."""
        try:
            stat, p_value = ks_2samp(expected, actual)
            return p_value # p_value < 0.05 indicates different distributions
        except Exception:
            return 1.0
            
    @staticmethod
    def calculate_wasserstein(expected: pd.Series, actual: pd.Series) -> float:
        """Wasserstein distance (Earth Mover's Distance)."""
        try:
            return wasserstein_distance(expected, actual)
        except Exception:
            return 0.0

    @staticmethod
    async def monitor_drift(db: AsyncSession, model_version: str, expected_features: pd.DataFrame, recent_features: pd.DataFrame, expected_preds: pd.Series = None, recent_preds: pd.Series = None) -> List[Dict[str, Any]]:
        """
        Calculates multiple drift metrics (PSI, KS Test, Missing Data) and records events.
        """
        events = []
        timestamp = datetime.now(timezone.utc)
        
        # 1. Feature Drift (PSI & Missing Data)
        for feature in expected_features.columns:
            if feature not in recent_features.columns:
                continue
                
            expected = expected_features[feature]
            actual = recent_features[feature]
            
            # Missing Data Drift
            exp_missing = expected.isna().mean()
            act_missing = actual.isna().mean()
            missing_diff = act_missing - exp_missing
            
            if missing_diff > 0.15: # 15% increase in missing data
                status = "CRITICAL" if missing_diff > 0.3 else "WARNING"
                event = ModelDriftEvent(
                    model_version=model_version,
                    feature_name=feature,
                    drift_score=missing_diff,
                    status=status,
                    timestamp=timestamp
                )
                db.add(event)
                events.append({"feature": feature, "type": "missing_data", "score": missing_diff, "status": status})
                
            # PSI & KS Test
            expected_clean = expected.dropna()
            actual_clean = actual.dropna()
            
            if len(expected_clean) < 10 or len(actual_clean) < 10:
                continue
                
            psi = ModelDriftMonitor.calculate_psi(expected_clean, actual_clean)
            ks_p = ModelDriftMonitor.calculate_ks_test(expected_clean, actual_clean)
            
            status = "NORMAL"
            if psi >= 0.2 or ks_p < 0.01:
                status = "CRITICAL"
            elif psi >= 0.1 or ks_p < 0.05:
                status = "WARNING"
                
            if status in ["WARNING", "CRITICAL"]:
                event = ModelDriftEvent(
                    model_version=model_version,
                    feature_name=feature,
                    drift_score=round(psi, 3),
                    status=status,
                    timestamp=timestamp
                )
                db.add(event)
                events.append({"feature": feature, "type": "distribution_drift", "score": round(psi, 3), "status": status})
                
        # 2. Prediction Drift
        if expected_preds is not None and recent_preds is not None:
            wd = ModelDriftMonitor.calculate_wasserstein(expected_preds.dropna(), recent_preds.dropna())
            if wd > 5.0: # threshold for 0-100 scale
                status = "CRITICAL" if wd > 10.0 else "WARNING"
                event = ModelDriftEvent(
                    model_version=model_version,
                    feature_name="prediction_target",
                    drift_score=round(wd, 3),
                    status=status,
                    timestamp=timestamp
                )
                db.add(event)
                events.append({"feature": "prediction_target", "type": "prediction_drift", "score": round(wd, 3), "status": status})
                
        await db.commit()
        return events
