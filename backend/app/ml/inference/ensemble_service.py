import time
from typing import Dict, Any, Tuple
from app.ml.models.risk_model import MLRiskModel
from app.ml.models.random_forest_model import MLRandomForestModel

# Instantiate the global ML models
global_xgb_model = MLRiskModel(model_version="v1.0.0")
global_xgb_model.load()

global_rf_model = MLRandomForestModel(model_version="v1.0.0")
global_rf_model.load()

class ModelEnsembleService:
    """
    Phase 6: Model Ensemble Service.
    Executes multiple independent models and calculates true disagreement.
    Both models are trained on synthetic/demo data and are intended for decision-support demonstration, 
    not clinical diagnosis or real-world epidemiological deployment.
    """
    
    @staticmethod
    def _baseline_prediction(features: Dict[str, float]) -> float:
        """Statistical baseline: naive linear combination of critical features."""
        score = 8.0 # Base geographic vulnerability
        
        # Rainfall
        rain = features.get("rainfall_lag_7d", features.get("rainfall_7d", 0.0))
        if rain > 100:
            score += min(25, (rain - 100) * 0.15)
            
        # Disease
        cases = features.get("cases_lag_7d", features.get("cases_7d", 0.0))
        score += min(35, cases * 4.5)
        
        # Reports
        reports = features.get("reports_7d", 0.0)
        score += min(20, reports * 3.5)
        
        return max(0.0, min(100.0, score))

    @staticmethod
    def evaluate_ensemble(features: Dict[str, float]) -> Dict[str, Any]:
        """
        Executes all models in the ensemble and computes final prediction and disagreement.
        """
        start_time = time.perf_counter()
        
        # 1. XGBoost Prediction
        xgb_score = 50.0 # Default fallback
        if global_xgb_model.model:
            xgb_score, _ = global_xgb_model.predict(features)
            
        # 2. Random Forest Prediction (Independent Scikit-Learn Model)
        rf_score = 50.0 # Default fallback
        if global_rf_model.model:
            rf_score, _ = global_rf_model.predict(features)
        
        # 3. Baseline Prediction
        baseline_score = ModelEnsembleService._baseline_prediction(features)
        
        end_time = time.perf_counter()
        inference_latency_ms = (end_time - start_time) * 1000.0
        
        # 4. Ensemble Calculation
        # XGBoost gets highest weight, RF middle, Baseline lowest.
        ensemble_score = (xgb_score * 0.5) + (rf_score * 0.3) + (baseline_score * 0.2)
        
        # 5. Disagreement
        preds = [xgb_score, rf_score, baseline_score]
        mean_pred = sum(preds) / len(preds)
        variance = sum((p - mean_pred) ** 2 for p in preds) / (len(preds) - 1)
        disagreement = variance ** 0.5
        
        # 6. Risk Level for ensemble
        if ensemble_score < 20: level = "LOW"
        elif ensemble_score < 40: level = "GUARDED"
        elif ensemble_score < 60: level = "MODERATE"
        elif ensemble_score < 80: level = "HIGH"
        else: level = "CRITICAL"

        return {
            "predictions": {
                "XGBoost": round(xgb_score, 1),
                "RandomForest": round(rf_score, 1),
                "Baseline": round(baseline_score, 1)
            },
            "ensemble": round(ensemble_score, 1),
            "risk_level": level,
            "disagreement": round(disagreement, 2),
            "inference_latency_ms": round(inference_latency_ms, 2),
            "model_version": "ensemble-v1.0.0",
            "training_dataset_version": "synth-v4"
        }
