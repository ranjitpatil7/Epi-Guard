import shap
import pandas as pd
from typing import Dict, Any, List
from app.ml.models.risk_model import MLRiskModel

class SHAPExplanationService:
    """
    Provides explainable AI insights for XGBoost predictions.
    Extracts top positive and negative risk contributors.
    """
    
    @staticmethod
    def explain_prediction(model: MLRiskModel, features: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Calculates SHAP values for a single prediction and returns structured explanations.
        """
        if not model.model:
            raise RuntimeError("Model is not loaded.")
            
        expected_features = model.get_expected_features()
        df = pd.DataFrame([features])[expected_features]
        
        # Calculate SHAP values
        explainer = shap.TreeExplainer(model.model)
        shap_values = explainer.shap_values(df)
        
        # Base value (average model output over the training dataset)
        # Note: shap.TreeExplainer returns expected_value as a single float or list depending on objective.
        # For reg:squarederror, it's typically a float.
        # However, we mostly care about the feature contributions themselves.
        
        explanations = []
        for i, feature_name in enumerate(expected_features):
            impact = float(shap_values[0][i])
            value = float(features.get(feature_name, 0.0))
            
            if abs(impact) > 0.5: # Only include meaningful impacts to avoid noise
                direction = "positive" if impact > 0 else "negative"
                
                # Human readable logic
                if "rainfall" in feature_name:
                    exp = f"Rainfall levels are driving risk {'up' if direction == 'positive' else 'down'}."
                elif "cases" in feature_name or "growth_rate" in feature_name:
                    exp = f"Disease trends are driving risk {'up' if direction == 'positive' else 'down'}."
                elif "turbidity" in feature_name or "ph" in feature_name:
                    exp = f"Water quality indicators are driving risk {'up' if direction == 'positive' else 'down'}."
                elif "reports" in feature_name:
                    exp = f"Community reports are driving risk {'up' if direction == 'positive' else 'down'}."
                elif "anomaly" in feature_name:
                    exp = f"Detected statistical anomalies are driving risk {'up' if direction == 'positive' else 'down'}."
                else:
                    exp = f"{feature_name} is driving risk {'up' if direction == 'positive' else 'down'}."

                explanations.append({
                    "feature": feature_name,
                    "value": round(value, 2),
                    "impact": round(impact, 2),
                    "direction": direction,
                    "explanation": exp
                })
                
        # Sort by absolute impact descending
        explanations.sort(key=lambda x: abs(x["impact"]), reverse=True)
        return explanations
