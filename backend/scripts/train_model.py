import os
import asyncio
import pandas as pd
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.models.domain import ModelVersion
from app.ml.models.risk_model import MLRiskModel
from app.ml.evaluation.evaluator import ModelEvaluator
from app.ml.features.feature_pipeline import FeatureEngineeringPipeline

DATA_DIR = os.path.join(os.path.dirname(__file__), "../app/ml/data")

async def train_and_register_model(version_tag: str):
    """
    Trains the XGBoost model on the synthetic dataset, evaluates it,
    and registers it in the ModelVersion database table.
    """
    print(f"Starting training for model version: {version_tag}")
    
    # 1. Load Data
    train_path = os.path.join(DATA_DIR, "synthetic_train.csv")
    val_path = os.path.join(DATA_DIR, "synthetic_val.csv")
    test_path = os.path.join(DATA_DIR, "synthetic_test.csv")
    
    if not os.path.exists(train_path):
        raise FileNotFoundError("Synthetic training data not found. Run generate_training_data.py first.")
        
    df_train = pd.read_csv(train_path)
    df_val = pd.read_csv(val_path)
    df_test = pd.read_csv(test_path)
    
    target_col = "target_risk_score"
    
    X_train = df_train.drop(columns=["sample_id", target_col, "target_risk_level"])
    y_train = df_train[target_col]
    
    X_val = df_val.drop(columns=["sample_id", target_col, "target_risk_level"])
    y_val = df_val[target_col]
    
    X_test = df_test.drop(columns=["sample_id", target_col, "target_risk_level"])
    y_test = df_test[target_col]
    
    # 2. Train Model
    model = MLRiskModel(model_version=version_tag)
    model.train(X_train, y_train, X_val, y_val)
    print("Model training complete.")
    
    # 3. Evaluate Model
    metrics = ModelEvaluator.evaluate_regression(model, X_test, y_test)
    print(f"Evaluation Metrics: {metrics}")
    
    # 4. Save Artifact
    model.save()
    print("Model artifact saved.")
    
    # 5. Register in DB
    async with AsyncSessionLocal() as db:
        new_version = ModelVersion(
            version=version_tag,
            training_date=datetime.now(timezone.utc),
            dataset_version="synthetic_v1",
            precision=None, # Regression proxy
            recall=None,
            f1_score=None,
            roc_auc=None,
            # We store mae/rmse in JSON/text normally, but since domain.py has specific columns,
            # we'll use calibration or add new columns if needed. Wait, domain.py doesn't have MAE.
            # We'll map MAE to calibration for demo, or just not store it if we can't alter schema without alembic.
            # Let's map it to JSON if we had a metrics column. Since we don't, we just log it.
            calibration=metrics["r2"] # Store R2 as a proxy in the calibration column for now
        )
        db.add(new_version)
        await db.commit()
        print("Model version registered in database.")

if __name__ == "__main__":
    asyncio.run(train_and_register_model("v1.0.0"))
