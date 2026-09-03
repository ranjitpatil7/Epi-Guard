import { client } from './client';

export interface DataSourceStatus {
  name: string;
  status: string;
  quality: number;
}

export interface DataQualityMetrics {
  overall_quality: number;
  completeness: number;
  freshness: number;
  validity: number;
  coverage: number;
  sources: DataSourceStatus[];
}

export const getDataQuality = async (): Promise<DataQualityMetrics> => {
  const response = await client.get(`/data-quality/`);
  return response.data;
};
