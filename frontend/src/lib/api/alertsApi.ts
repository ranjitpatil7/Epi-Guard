import { client } from './client';

export interface AlertItem {
  id: number;
  region_id: number;
  severity: string;
  message: string;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export const getAlerts = async (activeOnly = true, limit = 50): Promise<{ data: AlertItem[] }> => {
  const response = await client.get(`/alerts/?active_only=${activeOnly}&limit=${limit}`);
  return response.data;
};

export const acknowledgeAlert = async (alertId: number): Promise<{ status: string }> => {
  const response = await client.post(`/alerts/${alertId}/acknowledge`);
  return response.data;
};
