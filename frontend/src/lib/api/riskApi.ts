import { client } from "./client";

export interface RiskAssessment {
  region_id: number;
  region_name: string;
  calculation_timestamp: string;
  forecast_date?: string;
  risk_score?: number;
  estimated_risk_score: number;
  risk_level: "LOW" | "GUARDED" | "MODERATE" | "HIGH" | "CRITICAL" | string;
  contributing_factors: Array<{
    feature: string;
    value: number;
    impact: number;
    direction: string;
    explanation: string;
  }>;
  features_used: Record<string, any>;
  forecast_24h?: number;
  forecast_3d?: number;
  forecast_7d?: number;
}

export const getCurrentRisk = async (): Promise<RiskAssessment[]> => {
  const { data } = await client.get("/risk/current");
  return data.data; // The API returns { data: [...] }
};

export const simulateWhatIf = async (
  regionId: number, 
  overrides: Record<string, number>
): Promise<any> => {
  const { data } = await client.post(`/risk/what-if?region_id=${regionId}`, overrides);
  return data;
};

export interface MLRiskAssessment {
  region_id: number;
  calculation_timestamp: string;
  target_date: string;
  estimated_risk_score: number;
  risk_level: string;
  confidence_score: number;
  data_quality_score: number;
  model_version: string;
  is_synthetic_training_based: boolean;
  features_used: Record<string, any>;
  contributing_factors: Array<{
    feature: string;
    value: number;
    impact: number;
    direction: string;
    explanation: string;
  }>;
  forecasts: Array<{
    horizon: string;
    prediction: number;
    lower_bound: number;
    upper_bound: number;
    confidence: number;
    model_version: string;
  }>;
}

export const getMLRisk = async (regionId: number): Promise<MLRiskAssessment> => {
  const { data } = await client.get(`/ml/risk/${regionId}`);
  return data;
};

export interface RiskSnapshotInfo {
  snapshot_id: string;
  timestamp: string;
  current_risk: number;
  previous_risk: number;
  risk_delta: number;
  confidence: number;
}

export interface RiskLineageInfo {
  snapshot_id: string;
  region_id: number;
  timestamp: string;
  current_risk: number;
  previous_risk: number;
  risk_delta: number;
  model_version: string;
  feature_snapshot: Record<string, any>;
  explanation: {
    uncertainty_explanation: string;
    contributing_factors: Array<{
      feature: string;
      value: number;
      impact: number;
      direction: string;
      explanation: string;
    }>;
  };
  triggering_event: {
    event_id: string;
    event_type: string;
    source: string;
    timestamp: string;
    payload: Record<string, any>;
  } | null;
}

export const getRiskHistory = async (regionId: number): Promise<RiskSnapshotInfo[]> => {
  const { data } = await client.get(`/risk/${regionId}/history`);
  return data;
};

export const getSnapshotLineage = async (snapshotId: string): Promise<RiskLineageInfo> => {
  const { data } = await client.get(`/risk/snapshots/${snapshotId}/lineage`);
  return data;
};
