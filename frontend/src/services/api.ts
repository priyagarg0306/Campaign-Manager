/**
 * API service for backend communication
 */
import axios, { AxiosError, AxiosResponse } from 'axios';
import {
  Campaign,
  CreateCampaignRequest,
  UpdateCampaignRequest,
  PublishCampaignResponse,
  ApiError,
  ValidationResult
} from '../types/campaign';

// Create axios instance with base URL and timeout
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError<ApiError>) => {
    const message = error.response?.data?.error || error.message || 'An error occurred';
    console.error('API Error:', message);
    return Promise.reject(error);
  }
);

/**
 * Campaign API functions
 */
export const campaignApi = {
  /**
   * Get all campaigns
   */
  getAll: async (status?: string): Promise<Campaign[]> => {
    const params = status ? { status } : {};
    const response = await api.get<{ campaigns: Campaign[]; pagination: any }>('/campaigns', { params });
    return response.data.campaigns;
  },

  /**
   * Get a single campaign by ID
   */
  getById: async (id: string): Promise<Campaign> => {
    const response = await api.get<Campaign>(`/campaigns/${id}`);
    return response.data;
  },

  /**
   * Create a new campaign
   */
  create: async (data: CreateCampaignRequest): Promise<Campaign> => {
    const response = await api.post<Campaign>('/campaigns', data);
    return response.data;
  },

  /**
   * Update an existing campaign
   */
  update: async (id: string, data: UpdateCampaignRequest): Promise<Campaign> => {
    const response = await api.put<Campaign>(`/campaigns/${id}`, data);
    return response.data;
  },

  /**
   * Delete a campaign
   */
  delete: async (id: string): Promise<void> => {
    await api.delete(`/campaigns/${id}`);
  },

  /**
   * Publish a campaign to Google Ads
   */
  publish: async (id: string): Promise<PublishCampaignResponse> => {
    const response = await api.post<PublishCampaignResponse>(`/campaigns/${id}/publish`);
    return response.data;
  },

  /**
   * Pause a campaign in Google Ads
   */
  pause: async (id: string): Promise<{ message: string; campaign: Campaign }> => {
    const response = await api.post<{ message: string; campaign: Campaign }>(`/campaigns/${id}/pause`);
    return response.data;
  },

  /**
   * Enable a paused campaign in Google Ads
   */
  enable: async (id: string): Promise<{ message: string; campaign: Campaign }> => {
    const response = await api.post<{ message: string; campaign: Campaign }>(`/campaigns/${id}/enable`);
    return response.data;
  },

  /**
   * Validate a campaign before publishing
   * Pre-flight validation to check if campaign meets all Google Ads requirements
   */
  validate: async (id: string): Promise<ValidationResult> => {
    const response = await api.post<ValidationResult>(`/campaigns/${id}/validate`);
    return response.data;
  },
};

/**
 * Health check API
 */
export const healthApi = {
  check: async (): Promise<{
    status: string;
    checks: {
      database: { healthy: boolean; message: string };
      google_ads: { healthy: boolean; configured: boolean; message: string };
    };
  }> => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;
