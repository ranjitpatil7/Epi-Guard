import { client } from './client';

export interface CommunityReportItem {
  id: number;
  text: string;
  nlp_severity: number;
  status: string;
  created_at: string;
}

export const getCommunityReports = async (regionId?: number, limit = 50): Promise<{ data: CommunityReportItem[] }> => {
  const params = new URLSearchParams();
  if (regionId) params.append('region_id', regionId.toString());
  params.append('limit', limit.toString());
  
  const response = await client.get(`/community-reports/?${params.toString()}`);
  return response.data;
};
