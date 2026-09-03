import { client } from './client';

export interface AnomalyItem {
  id: number;
  region_id: number;
  feature: string;
  observed_value: number;
  expected_mean: number;
  z_score: number;
  severity: string;
  explanation: string;
  timestamp: string;
  status: string;
}

export const getAnomalies = async (regionId?: number, limit = 50): Promise<{ data: AnomalyItem[] }> => {
  const params = new URLSearchParams();
  if (regionId) params.append('region_id', regionId.toString());
  params.append('limit', limit.toString());
  
  const response = await client.get(`/anomalies/?${params.toString()}`);
  return response.data;
};
