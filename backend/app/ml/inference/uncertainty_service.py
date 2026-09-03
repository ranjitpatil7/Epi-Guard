from typing import Dict, Any, List
import math

class UncertaintyService:
    """
    Phase 6: Uncertainty Quantification Service.
    Uses model disagreement and simulated bootstrap variance to generate heuristic intervals.
    Note: These are model disagreement estimates, not strictly calibrated statistical uncertainty.
    """

    @staticmethod
    def calculate_uncertainty(
        ensemble_prediction: float,
        model_predictions: Dict[str, float],
        features: Dict[str, float],
        data_quality: float
    ) -> Dict[str, Any]:
        """
        Calculates confidence and strict prediction intervals.
        """
        # 1. Calculate Model Disagreement (Variance among base models)
        preds = list(model_predictions.values())
        if len(preds) > 1:
            mean_pred = sum(preds) / len(preds)
            variance = sum((p - mean_pred) ** 2 for p in preds) / (len(preds) - 1)
            disagreement = math.sqrt(variance)
        else:
            disagreement = 5.0 # Fallback if only 1 model
            
        # 2. Heuristic Bootstrap Uncertainty (Feature Space Sparsity)
        # If we have missing data or highly anomalous inputs, uncertainty grows
        sparsity_penalty = (1.0 - data_quality) * 15.0
        
        # High anomalies increase uncertainty
        anomaly_count = features.get("anomaly_count_7d", 0.0)
        anomaly_penalty = min(10.0, anomaly_count * 2.0)
        
        # 3. Total Uncertainty Width
        # 95% Confidence Interval approximate width (Z ~ 1.96 * std_err)
        std_error = disagreement + (sparsity_penalty * 0.3) + (anomaly_penalty * 0.2)
        uncertainty_width = 1.96 * std_error
        
        lower_bound = max(0.0, ensemble_prediction - uncertainty_width)
        upper_bound = min(100.0, ensemble_prediction + uncertainty_width)
        
        # 4. Confidence Calculation
        # Confidence is inversely proportional to uncertainty width.
        # Max acceptable width for "100% confidence" is arbitrarily defined as 5 points.
        confidence = max(0.0, 100.0 - (max(0.0, uncertainty_width - 5.0) * 2.0))
        
        # 5. Explanation Generation
        explanations = []
        if disagreement > 10.0:
            explanations.append(f"High model disagreement (std={round(disagreement, 1)}) indicates complex interacting factors.")
        if data_quality < 0.8:
            explanations.append("Missing or sparse data increases prediction intervals.")
        if anomaly_count > 0:
            explanations.append("Recent anomalies reduce confidence in standard trends.")
            
        if not explanations:
            explanations.append("Models are in agreement with high-quality data.")
            
        return {
            "prediction": round(ensemble_prediction, 1),
            "confidence": round(confidence / 100.0, 2), # Scale 0.0 - 1.0 as requested by prompt
            "uncertainty": {
                "lower": round(lower_bound, 1),
                "upper": round(upper_bound, 1),
                "width": round(upper_bound - lower_bound, 1),
                "disagreement": round(disagreement, 2)
            },
            "explanation": " | ".join(explanations)
        }
