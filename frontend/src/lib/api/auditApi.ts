import { client } from './client';

export interface AuditLogItem {
  id: number;
  user_id: number;
  action: string;
  ip_address: string;
  timestamp: string;
}

export const getAuditLogs = async (limit = 50): Promise<{ data: AuditLogItem[] }> => {
  const response = await client.get(`/audit/?limit=${limit}`);
  return response.data;
};
