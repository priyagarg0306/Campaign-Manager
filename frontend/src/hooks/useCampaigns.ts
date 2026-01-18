/**
 * Custom hook for managing campaigns
 */
import { useState, useCallback, useEffect, useMemo } from 'react';
import { Campaign, CreateCampaignRequest, CampaignStatus, ValidationResult } from '../types/campaign';
import { campaignApi } from '../services/api';

interface LoadingState {
  fetch: boolean;
  create: boolean;
  [key: string]: boolean; // Per-campaign operation loading (e.g., "publish_abc123")
}

interface UseCampaignsReturn {
  campaigns: Campaign[];
  loading: boolean;
  loadingState: LoadingState;
  isOperationLoading: (operation: string, campaignId?: string) => boolean;
  error: string | null;
  fetchCampaigns: (status?: CampaignStatus) => Promise<void>;
  createCampaign: (data: CreateCampaignRequest) => Promise<Campaign>;
  updateCampaign: (id: string, data: CreateCampaignRequest) => Promise<Campaign>;
  publishCampaign: (id: string) => Promise<void>;
  pauseCampaign: (id: string) => Promise<void>;
  enableCampaign: (id: string) => Promise<void>;
  deleteCampaign: (id: string) => Promise<void>;
  validateCampaign: (id: string) => Promise<ValidationResult>;
  clearError: () => void;
}

export function useCampaigns(): UseCampaignsReturn {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loadingState, setLoadingState] = useState<LoadingState>({
    fetch: false,
    create: false,
  });
  const [error, setError] = useState<string | null>(null);

  // Helper to set loading for specific operations
  const setOperationLoading = useCallback((key: string, isLoading: boolean) => {
    setLoadingState(prev => ({ ...prev, [key]: isLoading }));
  }, []);

  // Check if a specific operation is loading
  const isOperationLoading = useCallback((operation: string, campaignId?: string) => {
    const key = campaignId ? `${operation}_${campaignId}` : operation;
    return loadingState[key] || false;
  }, [loadingState]);

  // Global loading state for backwards compatibility
  const loading = useMemo(() => {
    return Object.values(loadingState).some(v => v);
  }, [loadingState]);

  const fetchCampaigns = useCallback(async (status?: CampaignStatus) => {
    setOperationLoading('fetch', true);
    setError(null);
    try {
      const data = await campaignApi.getAll(status);
      setCampaigns(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch campaigns';
      setError(message);
    } finally {
      setOperationLoading('fetch', false);
    }
  }, [setOperationLoading]);

  const createCampaign = useCallback(async (data: CreateCampaignRequest): Promise<Campaign> => {
    setOperationLoading('create', true);
    setError(null);
    try {
      const campaign = await campaignApi.create(data);
      setCampaigns((prev) => [campaign, ...prev]);
      return campaign;
    } catch (err: any) {
      const message = err.response?.data?.error || err.message || 'Failed to create campaign';
      setError(message);
      throw new Error(message);
    } finally {
      setOperationLoading('create', false);
    }
  }, [setOperationLoading]);

  const updateCampaign = useCallback(async (id: string, data: CreateCampaignRequest): Promise<Campaign> => {
    const loadingKey = `update_${id}`;
    setOperationLoading(loadingKey, true);
    setError(null);
    try {
      const updated = await campaignApi.update(id, data);
      setCampaigns((prev) => prev.map((c) => (c.id === id ? updated : c)));
      return updated;
    } catch (err: any) {
      const message = err.response?.data?.error || err.message || 'Failed to update campaign';
      setError(message);
      throw new Error(message);
    } finally {
      setOperationLoading(loadingKey, false);
    }
  }, [setOperationLoading]);

  const publishCampaign = useCallback(async (id: string) => {
    const loadingKey = `publish_${id}`;
    setOperationLoading(loadingKey, true);
    setError(null);
    try {
      const response = await campaignApi.publish(id);
      setCampaigns((prev) =>
        prev.map((c) => (c.id === id ? response.campaign : c))
      );
    } catch (err: any) {
      const message = err.response?.data?.error || err.message || 'Failed to publish campaign';
      setError(message);
      throw new Error(message);
    } finally {
      setOperationLoading(loadingKey, false);
    }
  }, [setOperationLoading]);

  const pauseCampaign = useCallback(async (id: string) => {
    const loadingKey = `pause_${id}`;
    setOperationLoading(loadingKey, true);
    setError(null);
    try {
      const response = await campaignApi.pause(id);
      setCampaigns((prev) =>
        prev.map((c) => (c.id === id ? response.campaign : c))
      );
    } catch (err: any) {
      const message = err.response?.data?.error || err.message || 'Failed to pause campaign';
      setError(message);
      throw new Error(message);
    } finally {
      setOperationLoading(loadingKey, false);
    }
  }, [setOperationLoading]);

  const enableCampaign = useCallback(async (id: string) => {
    const loadingKey = `enable_${id}`;
    setOperationLoading(loadingKey, true);
    setError(null);
    try {
      const response = await campaignApi.enable(id);
      setCampaigns((prev) =>
        prev.map((c) => (c.id === id ? response.campaign : c))
      );
    } catch (err: any) {
      const message = err.response?.data?.error || err.message || 'Failed to enable campaign';
      setError(message);
      throw new Error(message);
    } finally {
      setOperationLoading(loadingKey, false);
    }
  }, [setOperationLoading]);

  const deleteCampaign = useCallback(async (id: string) => {
    const loadingKey = `delete_${id}`;
    setOperationLoading(loadingKey, true);
    setError(null);
    try {
      await campaignApi.delete(id);
      setCampaigns((prev) => prev.filter((c) => c.id !== id));
    } catch (err: any) {
      const message = err.response?.data?.error || err.message || 'Failed to delete campaign';
      setError(message);
      throw new Error(message);
    } finally {
      setOperationLoading(loadingKey, false);
    }
  }, [setOperationLoading]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const validateCampaign = useCallback(async (id: string): Promise<ValidationResult> => {
    const loadingKey = `validate_${id}`;
    setOperationLoading(loadingKey, true);
    setError(null);
    try {
      const result = await campaignApi.validate(id);
      return result;
    } catch (err: any) {
      const message = err.response?.data?.error || err.message || 'Failed to validate campaign';
      setError(message);
      throw new Error(message);
    } finally {
      setOperationLoading(loadingKey, false);
    }
  }, [setOperationLoading]);

  // Fetch campaigns on mount
  useEffect(() => {
    fetchCampaigns();
  }, [fetchCampaigns]);

  return {
    campaigns,
    loading,
    loadingState,
    isOperationLoading,
    error,
    fetchCampaigns,
    createCampaign,
    updateCampaign,
    publishCampaign,
    pauseCampaign,
    enableCampaign,
    deleteCampaign,
    validateCampaign,
    clearError,
  };
}
