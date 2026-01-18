import { renderHook, act, waitFor } from '@testing-library/react';
import { useCampaigns } from './useCampaigns';
import { campaignApi } from '../services/api';

// Mock the API
jest.mock('../services/api', () => ({
  campaignApi: {
    getAll: jest.fn(),
    getById: jest.fn(),
    create: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
    publish: jest.fn(),
    pause: jest.fn(),
    enable: jest.fn(),
    validate: jest.fn(),
  },
}));

const mockCampaignApi = campaignApi as jest.Mocked<typeof campaignApi>;

describe('useCampaigns', () => {
  const mockCampaigns = [
    { id: '1', name: 'Campaign 1', status: 'DRAFT' },
    { id: '2', name: 'Campaign 2', status: 'PUBLISHED' },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    mockCampaignApi.getAll.mockResolvedValue(mockCampaigns as any);
  });

  describe('initial state and fetch', () => {
    it('fetches campaigns on mount', async () => {
      const { result } = renderHook(() => useCampaigns());

      await waitFor(() => {
        expect(result.current.campaigns).toEqual(mockCampaigns);
      });

      expect(mockCampaignApi.getAll).toHaveBeenCalledTimes(1);
    });

    it('sets loading state during fetch', async () => {
      let resolvePromise: (value: any) => void;
      mockCampaignApi.getAll.mockReturnValue(
        new Promise((resolve) => {
          resolvePromise = resolve;
        })
      );

      const { result } = renderHook(() => useCampaigns());

      expect(result.current.loading).toBe(true);
      expect(result.current.loadingState.fetch).toBe(true);

      await act(async () => {
        resolvePromise!(mockCampaigns);
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
    });

    it('handles fetch error', async () => {
      mockCampaignApi.getAll.mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useCampaigns());

      await waitFor(() => {
        expect(result.current.error).toBe('Network error');
      });
    });
  });

  describe('fetchCampaigns', () => {
    it('fetches campaigns with status filter', async () => {
      const { result } = renderHook(() => useCampaigns());

      await waitFor(() => {
        expect(result.current.campaigns).toEqual(mockCampaigns);
      });

      const draftCampaigns = [{ id: '1', name: 'Draft Campaign', status: 'DRAFT' }];
      mockCampaignApi.getAll.mockResolvedValue(draftCampaigns as any);

      await act(async () => {
        await result.current.fetchCampaigns('DRAFT');
      });

      expect(mockCampaignApi.getAll).toHaveBeenCalledWith('DRAFT');
      expect(result.current.campaigns).toEqual(draftCampaigns);
    });
  });

  describe('createCampaign', () => {
    it('creates a campaign and adds it to the list', async () => {
      const { result } = renderHook(() => useCampaigns());

      await waitFor(() => {
        expect(result.current.campaigns).toEqual(mockCampaigns);
      });

      const newCampaign = { id: '3', name: 'New Campaign', status: 'DRAFT' };
      mockCampaignApi.create.mockResolvedValue(newCampaign as any);

      await act(async () => {
        const created = await result.current.createCampaign({
          name: 'New Campaign',
          objective: 'SALES',
          campaign_type: 'DEMAND_GEN',
          daily_budget: 1000,
          start_date: '2030-01-01',
        });
        expect(created).toEqual(newCampaign);
      });

      expect(result.current.campaigns[0]).toEqual(newCampaign);
    });

    it('handles create error', async () => {
      const { result } = renderHook(() => useCampaigns());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      mockCampaignApi.create.mockRejectedValue({
        response: { data: { error: 'Validation failed' } },
      });

      await act(async () => {
        await expect(
          result.current.createCampaign({
            name: 'Test',
            objective: 'SALES',
            campaign_type: 'DEMAND_GEN',
            daily_budget: 1000,
            start_date: '2030-01-01',
          })
        ).rejects.toThrow('Validation failed');
      });

      expect(result.current.error).toBe('Validation failed');
    });
  });

  describe('updateCampaign', () => {
    it('updates a campaign in the list', async () => {
      const { result } = renderHook(() => useCampaigns());

      await waitFor(() => {
        expect(result.current.campaigns).toEqual(mockCampaigns);
      });

      const updatedCampaign = { id: '1', name: 'Updated Campaign', status: 'DRAFT' };
      mockCampaignApi.update.mockResolvedValue(updatedCampaign as any);

      await act(async () => {
        const updated = await result.current.updateCampaign('1', {
          name: 'Updated Campaign',
          objective: 'SALES',
          campaign_type: 'DEMAND_GEN',
          daily_budget: 1000,
          start_date: '2030-01-01',
        });
        expect(updated).toEqual(updatedCampaign);
      });

      expect(result.current.campaigns.find((c) => c.id === '1')?.name).toBe('Updated Campaign');
    });

    it('sets loading state for specific campaign', async () => {
      const { result } = renderHook(() => useCampaigns());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      let resolvePromise: (value: any) => void;
      mockCampaignApi.update.mockReturnValue(
        new Promise((resolve) => {
          resolvePromise = resolve;
        })
      );

      act(() => {
        result.current.updateCampaign('1', {
          name: 'Test',
          objective: 'SALES',
          campaign_type: 'DEMAND_GEN',
          daily_budget: 1000,
          start_date: '2030-01-01',
        });
      });

      expect(result.current.isOperationLoading('update', '1')).toBe(true);

      await act(async () => {
        resolvePromise!({ id: '1', name: 'Test' });
      });

      await waitFor(() => {
        expect(result.current.isOperationLoading('update', '1')).toBe(false);
      });
    });
  });

  describe('publishCampaign', () => {
    it('publishes a campaign and updates status', async () => {
      const { result } = renderHook(() => useCampaigns());

      await waitFor(() => {
        expect(result.current.campaigns).toEqual(mockCampaigns);
      });

      const publishedCampaign = { id: '1', name: 'Campaign 1', status: 'PUBLISHED' };
      mockCampaignApi.publish.mockResolvedValue({
        message: 'Published',
        campaign: publishedCampaign,
        google_ads: { campaign_id: '123' },
      } as any);

      await act(async () => {
        await result.current.publishCampaign('1');
      });

      expect(result.current.campaigns.find((c) => c.id === '1')?.status).toBe('PUBLISHED');
    });

    it('handles publish error', async () => {
      const { result } = renderHook(() => useCampaigns());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      mockCampaignApi.publish.mockRejectedValue(new Error('Publish failed'));

      await act(async () => {
        await expect(result.current.publishCampaign('1')).rejects.toThrow('Publish failed');
      });

      expect(result.current.error).toBe('Publish failed');
    });
  });

  describe('pauseCampaign', () => {
    it('pauses a campaign and updates status', async () => {
      const { result } = renderHook(() => useCampaigns());

      await waitFor(() => {
        expect(result.current.campaigns).toEqual(mockCampaigns);
      });

      const pausedCampaign = { id: '2', name: 'Campaign 2', status: 'PAUSED' };
      mockCampaignApi.pause.mockResolvedValue({
        message: 'Paused',
        campaign: pausedCampaign,
      } as any);

      await act(async () => {
        await result.current.pauseCampaign('2');
      });

      expect(result.current.campaigns.find((c) => c.id === '2')?.status).toBe('PAUSED');
    });
  });

  describe('enableCampaign', () => {
    it('enables a campaign and updates status', async () => {
      const { result } = renderHook(() => useCampaigns());

      await waitFor(() => {
        expect(result.current.campaigns).toEqual(mockCampaigns);
      });

      const enabledCampaign = { id: '1', name: 'Campaign 1', status: 'PUBLISHED' };
      mockCampaignApi.enable.mockResolvedValue({
        message: 'Enabled',
        campaign: enabledCampaign,
      } as any);

      await act(async () => {
        await result.current.enableCampaign('1');
      });

      expect(result.current.campaigns.find((c) => c.id === '1')?.status).toBe('PUBLISHED');
    });
  });

  describe('deleteCampaign', () => {
    it('deletes a campaign from the list', async () => {
      const { result } = renderHook(() => useCampaigns());

      await waitFor(() => {
        expect(result.current.campaigns).toEqual(mockCampaigns);
      });

      mockCampaignApi.delete.mockResolvedValue(undefined);

      await act(async () => {
        await result.current.deleteCampaign('1');
      });

      expect(result.current.campaigns.find((c) => c.id === '1')).toBeUndefined();
      expect(result.current.campaigns).toHaveLength(1);
    });

    it('handles delete error', async () => {
      const { result } = renderHook(() => useCampaigns());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      mockCampaignApi.delete.mockRejectedValue(new Error('Delete failed'));

      await act(async () => {
        await expect(result.current.deleteCampaign('1')).rejects.toThrow('Delete failed');
      });

      expect(result.current.error).toBe('Delete failed');
    });
  });

  describe('validateCampaign', () => {
    it('validates a campaign and returns result', async () => {
      const { result } = renderHook(() => useCampaigns());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const validationResult = { valid: true, errors: [], campaign_type: 'DEMAND_GEN' };
      mockCampaignApi.validate.mockResolvedValue(validationResult as any);

      let validateResult: any;
      await act(async () => {
        validateResult = await result.current.validateCampaign('1');
      });

      expect(validateResult).toEqual(validationResult);
      expect(mockCampaignApi.validate).toHaveBeenCalledWith('1');
    });

    it('handles validation error', async () => {
      const { result } = renderHook(() => useCampaigns());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      mockCampaignApi.validate.mockRejectedValue(new Error('Validation error'));

      await act(async () => {
        await expect(result.current.validateCampaign('1')).rejects.toThrow('Validation error');
      });

      expect(result.current.error).toBe('Validation error');
    });
  });

  describe('clearError', () => {
    it('clears the error state', async () => {
      mockCampaignApi.getAll.mockRejectedValue(new Error('Test error'));

      const { result } = renderHook(() => useCampaigns());

      await waitFor(() => {
        expect(result.current.error).toBe('Test error');
      });

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe('isOperationLoading', () => {
    it('returns correct loading state for operations', async () => {
      const { result } = renderHook(() => useCampaigns());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.isOperationLoading('fetch')).toBe(false);
      expect(result.current.isOperationLoading('create')).toBe(false);
      expect(result.current.isOperationLoading('publish', '123')).toBe(false);
    });
  });
});
