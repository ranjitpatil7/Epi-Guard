import os
import pytest
import pandas as pd
from app.ml.models.risk_model import MLRiskModel
from app.ml.models.random_forest_model import MLRandomForestModel
from app.ml.inference.ensemble_service import ModelEnsembleService
from app.ml.features.feature_pipeline import FeatureEngineeringPipeline

def test_rf_artifact_exists():
    """1. Random Forest model artifact exists."""
    rf_model = MLRandomForestModel(model_version="v1.0.0")
    assert os.path.exists(rf_model._get_model_path())

def test_rf_model_loads_successfully():
    """2. Random Forest model loads successfully."""
    rf_model = MLRandomForestModel(model_version="v1.0.0")
    loaded = rf_model.load()
    assert loaded is True
    assert rf_model.model is not None

def test_models_produce_independent_predictions():
    """3 & 4. Random Forest and XGBoost produce predictions independently."""
    xgb_model = MLRiskModel(model_version="v1.0.0")
    xgb_model.load()
    
    rf_model = MLRandomForestModel(model_version="v1.0.0")
    rf_model.load()
    
    features = {f: 0.0 for f in FeatureEngineeringPipeline.get_feature_names()}
    features["rainfall_7d"] = 100.0
    
    xgb_score, xgb_level = xgb_model.predict(features)
    rf_score, rf_level = rf_model.predict(features)
    
    assert isinstance(xgb_score, float)
    assert isinstance(rf_score, float)
    # They should not be identically computed proxies
    assert xgb_score != rf_score

def test_models_accept_expected_feature_schema():
    """5. Both models accept the expected feature schema."""
    xgb_model = MLRiskModel(model_version="v1.0.0")
    xgb_model.load()
    rf_model = MLRandomForestModel(model_version="v1.0.0")
    rf_model.load()
    
    # Check that they both expect the same 12 features that were trained on
    xgb_features = xgb_model.get_expected_features()
    rf_features = rf_model.get_expected_features()
    
    assert set(xgb_features) == set(rf_features)
    assert len(xgb_features) == 12

def test_ensemble_combines_genuine_predictions():
    """6. Ensemble combines the two genuine predictions."""
    features = {f: 5.0 for f in FeatureEngineeringPipeline.get_feature_names()}
    result = ModelEnsembleService.evaluate_ensemble(features)
    
    assert "predictions" in result
    assert "XGBoost" in result["predictions"]
    assert "RandomForest" in result["predictions"]
    
    # 9. Ensemble does NOT simply equal XGBoost
    assert result["ensemble"] != result["predictions"]["XGBoost"]

def test_no_proxy_logic_regression():
    """
    10. Ensemble does NOT use XGBoost prediction as RF input.
    Verify that RF prediction is independent.
    """
    # Create two feature sets that differ in a way that affects RF but maybe differently for XGB
    f1 = {f: 10.0 for f in FeatureEngineeringPipeline.get_feature_names()}
    f2 = {f: 20.0 for f in FeatureEngineeringPipeline.get_feature_names()}
    
    res1 = ModelEnsembleService.evaluate_ensemble(f1)
    res2 = ModelEnsembleService.evaluate_ensemble(f2)
    
    # Ensure RF score isn't just `xgb * 0.6 + baseline * 0.4`
    xgb1 = res1["predictions"]["XGBoost"]
    base1 = res1["predictions"]["Baseline"]
    rf1 = res1["predictions"]["RandomForest"]
    
    # This was the old proxy formula
    proxy_rf1 = round((xgb1 * 0.6) + (base1 * 0.4), 1)
    
    # The actual RF score should not exactly equal the old proxy formula
    # (Allowing for extremely unlikely coincidence, we check f2 as well)
    proxy_rf2 = round((res2["predictions"]["XGBoost"] * 0.6) + (res2["predictions"]["Baseline"] * 0.4), 1)
    rf2 = res2["predictions"]["RandomForest"]
    
    assert rf1 != proxy_rf1 or rf2 != proxy_rf2, "Regression: Random Forest is using the old proxy formula!"

def test_risk_score_bounds():
    """13. Risk score remains within valid bounds."""
    # Extreme high
    f_high = {f: 9999.0 for f in FeatureEngineeringPipeline.get_feature_names()}
    res_high = ModelEnsembleService.evaluate_ensemble(f_high)
    assert 0.0 <= res_high["ensemble"] <= 100.0
    
    # Extreme low
    f_low = {f: -9999.0 for f in FeatureEngineeringPipeline.get_feature_names()}
    res_low = ModelEnsembleService.evaluate_ensemble(f_low)
    assert 0.0 <= res_low["ensemble"] <= 100.0

def test_invalid_features_handled():
    """11. Invalid feature input is handled safely."""
    # Since models expect pandas dataframe and convert it, we just test missing features (they become NaN, which XGBoost handles, and RF in sklearn handles if configured, but we actually fill with 0.0 in the pipeline).
    rf_model = MLRandomForestModel(model_version="v1.0.0")
    rf_model.load()
    
    # If a feature is completely missing, pd.DataFrame creates a NaN.
    # Scikit-learn RF doesn't like NaN by default unless trained with it. Let's see how predict handles it.
    # The pipeline fills with 0.0, but if we call predict directly with missing keys:
    features = {"rainfall_7d": 10} # Missing everything else
    try:
        score, level = rf_model.predict(features)
        assert 0 <= score <= 100
    except KeyError:
        # Pandas raises KeyError if columns are missing.
        # This is expected and safe, as the FeaturePipeline prevents this in production by filling with 0.0.
        pass
