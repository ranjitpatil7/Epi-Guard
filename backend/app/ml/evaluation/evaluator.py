import pandas as pd
import numpy as np
from typing import Dict, Any
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from app.ml.models.risk_model import MLRiskModel

class ModelEvaluator:
    """
    Evaluates ML Risk Models on a test dataset.
    Generates regression metrics and classification proxy metrics.
    """
    
    @staticmethod
    def evaluate_regression(model: MLRiskModel, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
        X_test_filtered = X_test[model.feature_names]
        preds = model.model.predict(X_test_filtered)
        
        # Clip
        preds = np.clip(preds, 0, 100)
        
        mae = mean_absolute_error(y_test, preds)
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        r2 = r2_score(y_test, preds)
        
        return {
            "mae": round(float(mae), 3),
            "rmse": round(float(rmse), 3),
            "r2": round(float(r2), 3)
        }
