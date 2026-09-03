from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.domain import Alert

class EarlyWarningService:
    """
    AI Early Warning Engine.
    Combines Risk Fusion outputs to generate structured public-health alerts.
    """
    
    @staticmethod
    def evaluate_warnings(fused_risk: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluates the current risk intelligence and generates alerts if justified.
        """
        alerts = []
        score = fused_risk["estimated_risk_score"]
        confidence = fused_risk["confidence_score"]
        forecasts = fused_risk["forecasts"]
        anomalies_count = fused_risk["features_used"].get("anomaly_count_7d", 0)
        
        # Determine trend based on +3d forecast
        forecast_3d = next((f for f in forecasts if f["days_ahead"] == 3), None)
        trend_up = forecast_3d and forecast_3d["predicted_risk"] > score + 5.0
        
        severity = None
        message = ""
        evidence = []
        
        if score >= 80:
            severity = "CRITICAL"
            message = "Critical estimated water-borne disease risk detected."
        elif score >= 60 and trend_up:
            severity = "HIGH"
            message = "High estimated risk with worsening short-term forecast."
        elif score >= 60:
            severity = "WARNING"
            message = "Elevated water-borne disease risk detected."
        elif anomalies_count >= 2:
            severity = "WATCH"
            message = "Multiple environmental or epidemiological anomalies detected; monitoring advised."
            
        if severity:
            # Build evidence
            for exp in fused_risk["contributing_factors"][:2]:
                evidence.append(exp["explanation"])
            if confidence < 60:
                evidence.append("Warning: Prediction confidence is low due to incomplete data.")
                
            alerts.append({
                "title": f"{severity} Risk Alert",
                "severity": severity,
                "region_id": fused_risk["region_id"],
                "risk_score": score,
                "detected_factors": [e["feature"] for e in fused_risk["contributing_factors"][:3]],
                "evidence": evidence,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=3)).isoformat(),
                "status": "ACTIVE"
            })
            
        return alerts
        
    @staticmethod
    async def process_and_store_alerts(db: AsyncSession, fused_risk: Dict[str, Any]):
        """
        Evaluates warnings and stores them in the database, handling deduplication.
        """
        new_alerts = EarlyWarningService.evaluate_warnings(fused_risk)
        
        for alert_data in new_alerts:
            # In a real app, query db for active alerts of same region/severity to deduplicate
            # For now, we just insert
            new_alert = Alert(
                region_id=alert_data["region_id"],
                severity=alert_data["severity"],
                message=alert_data["message"],
                is_active=True
            )
            db.add(new_alert)
            
        await db.commit()
        return new_alerts
