import os
import random
import csv
import math
from datetime import datetime, timedelta

def generate_synthetic_data(num_samples: int = 2000, seed: int = 42) -> list:
    """
    Generates realistic, non-deterministic synthetic data for the JalRakshak ML Risk Engine.
    Relationships:
    - High rainfall -> higher turbidity -> higher disease cases.
    - Low pH -> higher disease cases.
    - More cases -> higher severe reports.
    - High anomalies -> higher risk.
    """
    random.seed(seed)
    data = []
    
    for i in range(num_samples):
        # Base environmental
        rainfall_24h = max(0, random.gauss(15, 20))  # mostly low, sometimes high spikes
        if random.random() < 0.1: rainfall_24h += random.uniform(50, 150) # extreme events
        
        rainfall_7d = rainfall_24h + max(0, random.gauss(50, 40))
        temperature_7d_avg = random.uniform(20, 35)
        humidity_7d_avg = random.uniform(40, 95)
        
        # Water Quality is affected by rainfall
        base_turbidity = random.uniform(1.0, 5.0)
        turbidity_7d_avg = base_turbidity + (rainfall_7d * 0.05) + random.uniform(0, 2)
        ph_7d_avg = random.uniform(6.5, 8.5) - (rainfall_7d * 0.005) # slight acidification during heavy rain
        
        # Disease cases driven by water quality and rain
        cases_base = max(0, int(random.gauss(5, 5)))
        cases_multiplier = 1.0 + (turbidity_7d_avg * 0.1) + (1.0 if ph_7d_avg < 6.8 else 0)
        cases_7d = int(cases_base * cases_multiplier)
        cases_14d = cases_7d + max(0, int(random.gauss(10, 5)))
        
        # Growth rate
        cases_prev_7d = cases_14d - cases_7d
        disease_growth_rate = (cases_7d - cases_prev_7d) / max(1, cases_prev_7d)
        
        # Reports
        reports_7d = int(cases_7d * random.uniform(0.5, 1.5))
        severe_reports_7d = int(reports_7d * random.uniform(0.1, 0.4))
        
        # Anomalies
        anomaly_count_7d = 0
        if rainfall_7d > 100: anomaly_count_7d += 1
        if disease_growth_rate > 0.5: anomaly_count_7d += 1
        if turbidity_7d_avg > 10: anomaly_count_7d += 1
        
        # Target: Risk Score (0-100)
        # We simulate the target based on a hidden formula + noise to force XGBoost to learn it.
        risk = 10.0 # base risk
        risk += (rainfall_7d * 0.15)
        risk += (turbidity_7d_avg * 1.5)
        risk += (cases_7d * 2.0)
        risk += (disease_growth_rate * 5.0)
        risk += (severe_reports_7d * 3.0)
        risk += (anomaly_count_7d * 4.0)
        
        # Add noise
        risk += random.gauss(0, 5.0)
        
        risk = max(0.0, min(100.0, risk))
        
        # Risk level for classification
        if risk < 20: risk_level = "LOW"
        elif risk < 40: risk_level = "GUARDED"
        elif risk < 60: risk_level = "MODERATE"
        elif risk < 80: risk_level = "HIGH"
        else: risk_level = "CRITICAL"
        
        row = {
            "sample_id": i,
            "rainfall_24h": round(rainfall_24h, 2),
            "rainfall_7d": round(rainfall_7d, 2),
            "temperature_7d_avg": round(temperature_7d_avg, 2),
            "humidity_7d_avg": round(humidity_7d_avg, 2),
            "turbidity_7d_avg": round(turbidity_7d_avg, 2),
            "ph_7d_avg": round(ph_7d_avg, 2),
            "cases_7d": cases_7d,
            "cases_14d": cases_14d,
            "disease_growth_rate": round(disease_growth_rate, 3),
            "reports_7d": reports_7d,
            "severe_reports_7d": severe_reports_7d,
            "anomaly_count_7d": anomaly_count_7d,
            "target_risk_score": round(risk, 2),
            "target_risk_level": risk_level
        }
        data.append(row)
        
    return data

def save_to_csv(data: list, filepath: str):
    if not data:
        return
        
    keys = data[0].keys()
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)

if __name__ == "__main__":
    print("Generating SYNTHETIC DEMONSTRATION DATA for ML training...")
    
    # Generate 5000 total samples
    full_data = generate_synthetic_data(5000, seed=101)
    
    # Split: 70% train, 15% val, 15% test
    train_size = int(0.7 * len(full_data))
    val_size = int(0.15 * len(full_data))
    
    train_data = full_data[:train_size]
    val_data = full_data[train_size:train_size+val_size]
    test_data = full_data[train_size+val_size:]
    
    # Ensure directory exists
    os.makedirs("app/ml/data", exist_ok=True)
    
    save_to_csv(train_data, "app/ml/data/synthetic_train.csv")
    save_to_csv(val_data, "app/ml/data/synthetic_val.csv")
    save_to_csv(test_data, "app/ml/data/synthetic_test.csv")
    
    print(f"Generated {len(train_data)} training samples.")
    print(f"Generated {len(val_data)} validation samples.")
    print(f"Generated {len(test_data)} test samples.")
    print("Synthetic data saved to backend/app/ml/data/")
