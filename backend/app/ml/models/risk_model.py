import os
import pickle
import xgboost as xgb
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from app.ml.features.feature_pipeline import FeatureEngineeringPipeline

MODEL_DIR = os.path.join(os.path.dirname(__file__), "../data")

class MLRiskModel:
    """
    XGBoost-based Machine Learning Risk Engine for predicting Regional Risk.
    Predicts a score between 0 and 100.
    """
    
    def __init__(self, model_version: str = "v1.0.0"):
        self.model_version = model_version
        self.model = None
        self.feature_names = FeatureEngineeringPipeline.get_feature_names()
        
    def _get_model_path(self) -> str:
        return os.path.join(MODEL_DIR, f"risk_model_{self.model_version}.pkl")
        
    def load(self) -> bool:
        """Loads the pre-trained model artifact if it exists."""
        model_path = self._get_model_path()
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            return True
        return False
        
    def save(self):
        """Saves the trained model artifact."""
        os.makedirs(MODEL_DIR, exist_ok=True)
        with open(self._get_model_path(), 'wb') as f:
            pickle.dump(self.model, f)
            
    def train(self, X_train: pd.DataFrame, y_train: pd.Series, X_val: pd.DataFrame, y_val: pd.Series):
        """Trains the XGBoost regression model."""
        # Ensure features match
        X_train = X_train[self.feature_names]
        X_val = X_val[self.feature_names]
        
        # We use a simple XGBRegressor for the 0-100 risk score
        self.model = xgb.XGBRegressor(
            objective='reg:squarederror',
            n_estimators=200,
            learning_rate=0.05,
            max_depth=5,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            early_stopping_rounds=10
        )
        
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_train, y_train), (X_val, y_val)],
            verbose=False
        )
        
    def get_expected_features(self) -> list:
        if not self.model:
            return self.feature_names
        try:
            expected_features = self.model.get_booster().feature_names
            if expected_features is None:
                return self.feature_names
            return expected_features
        except AttributeError:
            return getattr(self.model, "feature_names_in_", self.feature_names)

    def predict(self, features: Dict[str, float]) -> Tuple[float, str]:
        """
        Predicts the risk score (0-100) and risk level given a feature dictionary.
        Returns (score, level).
        """
        if not self.model:
            raise RuntimeError("Model is not loaded. Cannot predict.")
            
        expected_features = self.get_expected_features()
            
        # Convert single dict to DataFrame
        df = pd.DataFrame([features])[expected_features]
        
        # Predict
        raw_score = self.model.predict(df)[0]
        
        # Clip between 0 and 100
        score = float(max(0.0, min(100.0, raw_score)))
        
        # Determine level based on configurable thresholds
        if score < 20: level = "LOW"
        elif score < 40: level = "GUARDED"
        elif score < 60: level = "MODERATE"
        elif score < 80: level = "HIGH"
        else: level = "CRITICAL"
        
        return score, level
        
    def calculate_confidence(self, features: Dict[str, float], data_quality_score: float = 1.0) -> float:
        """
        Calculates a heuristic prediction confidence based on data completeness and missing signals.
        """
        confidence = 100.0
        
        # Example penalty: if severe reports are missing or rainfall is exact 0 but it's monsoon
        # Real confidence would use model uncertainty, but for XGBoost regression without quantile loss, 
        # we rely on feature availability heuristics + data quality score.
        
        # Data Quality Engine penalty
        confidence *= data_quality_score
        
        # Check for missing/defaulted features (e.g., if everything is exactly 0)
        zeros = sum(1 for v in features.values() if v == 0.0)
        if zeros > len(features) // 2:
            confidence -= 20.0 # High penalty for sparse data
            
        return max(0.0, min(100.0, confidence))
