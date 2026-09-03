import os
import pickle
import pandas as pd
from typing import Dict, Any, Tuple
from app.ml.features.feature_pipeline import FeatureEngineeringPipeline

MODEL_DIR = os.path.join(os.path.dirname(__file__), "../data")

class MLRandomForestModel:
    """
    Random Forest Machine Learning Risk Engine for predicting Regional Risk.
    Predicts a score between 0 and 100.
    """
    
    def __init__(self, model_version: str = "v1.0.0"):
        self.model_version = model_version
        self.model = None
        
    def _get_model_path(self) -> str:
        return os.path.join(MODEL_DIR, f"random_forest_{self.model_version}.pkl")
        
    def load(self) -> bool:
        """Loads the pre-trained model artifact if it exists."""
        model_path = self._get_model_path()
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            return True
        return False
        
    def get_expected_features(self) -> list:
        if not self.model:
            return FeatureEngineeringPipeline.get_feature_names()
        try:
            return list(self.model.feature_names_in_)
        except AttributeError:
            return FeatureEngineeringPipeline.get_feature_names()

    def predict(self, features: Dict[str, float]) -> Tuple[float, str]:
        """
        Predicts the risk score (0-100) and risk level given a feature dictionary.
        Returns (score, level).
        """
        if not self.model:
            raise RuntimeError("Random Forest model is not loaded. Cannot predict.")
            
        expected_features = self.get_expected_features()
            
        # Convert single dict to DataFrame using exact expected feature order
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
