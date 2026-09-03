import os
import sys
import pickle
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Ensure app imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.ml.features.feature_pipeline import FeatureEngineeringPipeline

def train_rf_model():
    print("Training Random Forest Regressor on Synthetic Data...")
    
    # 1. Load Data
    data_dir = os.path.join(os.path.dirname(__file__), '../app/ml/data')
    train_path = os.path.join(data_dir, 'synthetic_train.csv')
    val_path = os.path.join(data_dir, 'synthetic_val.csv')
    
    if not os.path.exists(train_path):
        raise FileNotFoundError(f"Cannot find training data at {train_path}")
        
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    
    # 2. Extract Features (Same schema as XGBoost)
    # The XGBoost model v1.0.0 uses the 12 features present in the synthetic data, not the 39 from Phase 6.
    target_col = "target_risk_score"
    
    if target_col not in train_df.columns:
        raise ValueError(f"Target column '{target_col}' not found in training data.")
        
    feature_names = [c for c in train_df.columns if c not in ["sample_id", "target_risk_score", "target_risk_level"]]
    
    X_train = train_df[feature_names]
    y_train = train_df[target_col]
    X_val = val_df[feature_names]
    y_val = val_df[target_col]
    
    # 3. Initialize and Train Model
    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=8,
        min_samples_split=5,
        min_samples_leaf=2,
        max_features='sqrt',
        random_state=42, # Reproducibility
        n_jobs=-1
    )
    
    rf_model.fit(X_train, y_train)
    
    # 4. Evaluate Model
    y_pred_val = rf_model.predict(X_val)
    mse = mean_squared_error(y_val, y_pred_val)
    mae = mean_absolute_error(y_val, y_pred_val)
    r2 = r2_score(y_val, y_pred_val)
    
    print("\nRandom Forest Evaluation Metrics (Validation):")
    print(f"MSE: {mse:.2f}")
    print(f"MAE: {mae:.2f}")
    print(f"R2 : {r2:.2f}")
    print(f"Feature count: {len(feature_names)}")
    print(f"Training Data Source: Synthetic/Demo Dataset")
    
    # 5. Save Artifact
    model_path = os.path.join(data_dir, 'random_forest_v1.0.0.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(rf_model, f)
        
    print(f"\nRandom Forest model successfully saved to {model_path}")
    
if __name__ == "__main__":
    train_rf_model()
