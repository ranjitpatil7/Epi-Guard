import { apiClient } from './client';

export interface UserProfileUpdate {
  full_name?: string;
  email?: string;
  region_id?: number;
}

export interface UserPreferences {
  dark_mode: boolean;
  animations_enabled: boolean;
  email_notifications: boolean;
  sms_notifications: boolean;
  risk_threshold: number;
  strict_guardrails: boolean;
  primary_model: string;
  anomaly_sensitivity: number;
  gemini_api_key: string | null;
  imd_weather_sync: boolean;
  hospital_sync: boolean;
}

export const usersApi = {
  updateProfile: async (data: UserProfileUpdate) => {
    const response = await apiClient.patch('/users/me', data);
    return response.data;
  },

  getPreferences: async (): Promise<UserPreferences> => {
    const response = await apiClient.get('/users/me/preferences');
    return response.data;
  },

  updatePreferences: async (data: Partial<UserPreferences>): Promise<UserPreferences> => {
    const response = await apiClient.patch('/users/me/preferences', data);
    return response.data;
  },

  getUsers: async () => {
    const response = await apiClient.get('/users');
    return response.data;
  },

  createUser: async (data: any) => {
    const response = await apiClient.post('/users', data);
    return response.data;
  },

  updateUserStatus: async (userId: number, status: string) => {
    const response = await apiClient.patch(`/users/${userId}/status?status=${status}`);
    return response.data;
  },

  changePassword: async (data: any) => {
    const response = await apiClient.patch('/users/me/password', data);
    return response.data;
  }
};
