import math
import numpy as np
import pandas as pd
from typing import List, Dict, Any
from sklearn.ensemble import IsolationForest

class AdvancedAnomalyDetector:
    """
    Advanced Anomaly Detection Service supporting Z-Score, IQR, and Isolation Forest.
    """
    
    @staticmethod
    def detect_z_score(values: List[float], threshold: float = 2.5) -> List[bool]:
        """Detects anomalies using Z-score."""
        if not values or len(values) < 2:
            return [False] * len(values)
            
        mean = np.mean(values)
        std_dev = np.std(values)
        
        if std_dev == 0:
            return [False] * len(values)
            
        z_scores = [(x - mean) / std_dev for x in values]
        return [abs(z) > threshold for z in z_scores]
        
    @staticmethod
    def detect_iqr(values: List[float]) -> List[bool]:
        """Detects anomalies using Interquartile Range (IQR)."""
        if not values or len(values) < 4:
            return [False] * len(values)
            
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)
        
        return [(x < lower_bound or x > upper_bound) for x in values]
        
    @staticmethod
    def detect_isolation_forest(data: pd.DataFrame, contamination: float = 0.05) -> List[bool]:
        """
        Multivariate anomaly detection using Isolation Forest.
        Expects a DataFrame of numerical features.
        """
        if data.empty or len(data) < 10:
            return [False] * len(data)
            
        clf = IsolationForest(contamination=contamination, random_state=42)
        preds = clf.fit_predict(data)
        
        # IsolationForest returns -1 for anomalies, 1 for normal
        return [True if p == -1 else False for p in preds]

    @staticmethod
    def analyze_region_history(data_points: List[Dict[str, Any]], features_to_check: List[str]) -> List[Dict[str, Any]]:
        """
        Analyzes a history of data points and returns detected anomalies.
        Uses a combination of IQR and Isolation Forest.
        """
        if not data_points:
            return []
            
        df = pd.DataFrame(data_points)
        
        # Filter to only the features we actually have in the data
        available_features = [f for f in features_to_check if f in df.columns]
        
        if not available_features:
            return []
            
        anomalies = []
        
        # 1. Univariate checks (IQR) for extreme spikes in specific features like rainfall
        for feature in available_features:
            values = df[feature].tolist()
            iqr_anomalies = AdvancedAnomalyDetector.detect_iqr(values)
            z_anomalies = AdvancedAnomalyDetector.detect_z_score(values)
            
            for idx, (is_iqr, is_z) in enumerate(zip(iqr_anomalies, z_anomalies)):
                # If it's an anomaly by both methods, flag it
                if is_iqr and is_z:
                    val = values[idx]
                    mean_val = np.mean(values)
                    anomalies.append({
                        "timestamp": df.iloc[idx].get("timestamp") or df.iloc[idx].get("date"),
                        "feature": feature,
                        "observed_value": val,
                        "expected_mean": mean_val,
                        "method": "IQR+Z-Score",
                        "severity": "HIGH",
                        "explanation": f"Extreme {feature} spike detected. Observed: {val:.2f}, Expected: {mean_val:.2f}"
                    })
                    
        # 2. Multivariate check (Isolation Forest)
        # Fill NaNs with 0 for Isolation Forest to work
        df_imputed = df[available_features].fillna(0)
        if len(df_imputed) >= 10:
            if_anomalies = AdvancedAnomalyDetector.detect_isolation_forest(df_imputed)
            
            for idx, is_anomaly in enumerate(if_anomalies):
                if is_anomaly:
                    anomalies.append({
                        "timestamp": df.iloc[idx].get("timestamp") or df.iloc[idx].get("date"),
                        "feature": "MULTIVARIATE",
                        "observed_value": 0.0, # N/A for multivariate
                        "expected_mean": 0.0,
                        "method": "IsolationForest",
                        "severity": "MEDIUM",
                        "explanation": f"Complex multivariate anomaly detected across features: {', '.join(available_features)}"
                    })
                    
        return anomalies
