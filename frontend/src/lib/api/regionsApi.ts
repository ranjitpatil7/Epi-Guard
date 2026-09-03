import { client } from "./client";

export interface Region {
  id: number;
  name: string;
  state: string;
  district: string;
  population: number;
  lat?: number;
  lng?: number;
}

export interface RegionDetail extends Region {
  geometry?: any; // GeoJSON
}

export const getRegions = async (): Promise<Region[]> => {
  const { data } = await client.get("/regions/");
  return data;
};

export const getRegionDetail = async (id: number): Promise<RegionDetail> => {
  const { data } = await client.get(`/regions/${id}`);
  return data;
};
