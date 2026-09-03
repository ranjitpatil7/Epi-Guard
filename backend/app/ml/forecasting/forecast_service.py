from typing import Dict, Any, List
import numpy as np

class ForecastingService:
    """
    Phase 6: Advanced Modular Forecasting Service.
    Supports Baseline, ML-based, and Ensemble Forecasting.
    Generates +1d, +3d, +7d, +14d, +30d forecasts.
    """

    @staticmethod
    def _baseline_forecast(current_risk: float, features: Dict[str, float], days: int) -> float:
        """Statistical Baseline (Exponential smoothing with momentum)."""
        # Calculate momentum
        growth_rate = features.get("cases_percentage_change", features.get("disease_growth_rate", 0.0))
        accel = features.get("cases_acceleration", 0.0)
        recent_rain = features.get("rainfall_lag_7d", features.get("rainfall_7d", 0.0))
        
        daily_drift = (growth_rate * 3.0) + (accel * 0.5)
        if recent_rain > 100:
            daily_drift += 1.0
        elif recent_rain < 10:
            daily_drift -= 1.0
            
        projected = current_risk + (daily_drift * days * (0.85 ** days))
        return max(0.0, min(100.0, projected))

    @staticmethod
    def _ml_forecast(current_risk: float, features: Dict[str, float], days: int) -> float:
        """
        ML-based forecasting (Simulating an XGBoost time-series autoregressor).
        Uses rolling features and spatial neighbors to project future risk.
        """
        spatial_prop = features.get("regional_risk_propagation", 0.0)
        hotspot_density = features.get("hotspot_density", 0.0)
        cases_7d = features.get("cases_lag_7d", features.get("cases_7d", 0.0))
        
        # Simulated learned weights for ML
        base_shift = (spatial_prop * 0.3) + (hotspot_density * 0.1)
        if cases_7d > 50:
            base_shift += 5.0
            
        # ML usually flattens out longer term without active triggers
        projected = current_risk + (base_shift * (days / 7.0) * (0.75 ** (days/3.0)))
        return max(0.0, min(100.0, projected))

    @staticmethod
    def generate_forecast(current_risk: float, features: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Generates ensemble forecasts for +1, +3, +7, +14, +30 days.
        """
        forecasts = []
        horizons = [1, 3, 7, 14, 30]
        
        for days in horizons:
            baseline_pred = ForecastingService._baseline_forecast(current_risk, features, days)
            ml_pred = ForecastingService._ml_forecast(current_risk, features, days)
            
            # Ensemble (Weighted Average: ML gets more weight short-term, Baseline more weight long-term)
            ml_weight = max(0.2, 0.8 - (days * 0.015))
            ensemble_pred = (ml_pred * ml_weight) + (baseline_pred * (1.0 - ml_weight))
            
            # Uncertainty (Model disagreement + temporal decay)
            disagreement = abs(ml_pred - baseline_pred)
            base_uncertainty = (days * 0.5) # Uncertainty grows with time
            total_uncertainty = disagreement + base_uncertainty
            
            lower_bound = max(0.0, ensemble_pred - total_uncertainty)
            upper_bound = min(100.0, ensemble_pred + total_uncertainty)
            
            # Confidence decreases as uncertainty width increases
            confidence_width = upper_bound - lower_bound
            confidence = max(0.1, 1.0 - (confidence_width / 100.0))
            
            forecasts.append({
                "horizon": f"{days}d",
                "prediction": round(ensemble_pred, 1),
                "lower_bound": round(lower_bound, 1),
                "upper_bound": round(upper_bound, 1),
                "confidence": round(confidence, 2),
                "model_version": "ensemble-ts-v1.0"
            })
            
        return forecasts
