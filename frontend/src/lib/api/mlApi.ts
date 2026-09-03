import { client } from './client';

export interface ModelMetrics {
  version: string;
  training_date: string;
  metrics: {
    r2_calibration: number;
    precision?: number;
    recall?: number;
    f1_score?: number;
    roc_auc?: number;
  };
  dataset_version: string;
}

export interface PredictionHistoryItem {
  region_id: number;
  timestamp: string;
  predicted_risk: number;
  model_version: string;
}

export interface ModelDriftEvent {
  feature: string;
  score: number;
  status: string;
  timestamp: string;
}

export const getActiveModel = async (): Promise<ModelMetrics> => {
  const response = await client.get('/ml/model/active');
  return response.data;
};

export const getPredictionHistory = async (): Promise<{ data: PredictionHistoryItem[] }> => {
  const response = await client.get('/ml/predictions/history');
  return response.data;
};

export const getModelDrift = async (): Promise<{ events: ModelDriftEvent[] }> => {
  const response = await client.get('/ml/model/drift');
  return response.data;
};
