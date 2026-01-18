import axios from 'axios';
import { campaignApi, healthApi } from './api';

// Mock axios
jest.mock('axios', () => {
  const mockAxiosInstance = {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    interceptors: {
      response: {
        use: jest.fn(),
      },
    },
  };
  return {
    create: jest.fn(() => mockAxiosInstance),
    ...mockAxiosInstance,
  };
});

const mockAxios = axios.create() as jest.Mocked<typeof axios>;

describe('campaignApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getAll', () => {
    it('fetches all campaigns', async () => {
      const mockCampaigns = [
        { id: '1', name: 'Campaign 1' },
        { id: '2', name: 'Campaign 2' },
      ];
      (mockAxios.get as jest.Mock).mockResolvedValueOnce({
        data: { campaigns: mockCampaigns, pagination: {} },
      });

      const result = await campaignApi.getAll();

      expect(mockAxios.get).toHaveBeenCalledWith('/campaigns', { params: {} });
      expect(result).toEqual(mockCampaigns);
    });

    it('fetches campaigns with status filter', async () => {
      const mockCampaigns = [{ id: '1', name: 'Campaign 1', status: 'DRAFT' }];
      (mockAxios.get as jest.Mock).mockResolvedValueOnce({
        data: { campaigns: mockCampaigns, pagination: {} },
      });

      const result = await campaignApi.getAll('DRAFT');

      expect(mockAxios.get).toHaveBeenCalledWith('/campaigns', { params: { status: 'DRAFT' } });
      expect(result).toEqual(mockCampaigns);
    });
  });

  describe('getById', () => {
    it('fetches a single campaign by ID', async () => {
      const mockCampaign = { id: '123', name: 'Test Campaign' };
      (mockAxios.get as jest.Mock).mockResolvedValueOnce({ data: mockCampaign });

      const result = await campaignApi.getById('123');

      expect(mockAxios.get).toHaveBeenCalledWith('/campaigns/123');
      expect(result).toEqual(mockCampaign);
    });
  });

  describe('create', () => {
    it('creates a new campaign', async () => {
      const newCampaign = {
        name: 'New Campaign',
        objective: 'SALES' as const,
        campaign_type: 'DEMAND_GEN' as const,
        daily_budget: 1000000,
        start_date: '2030-01-01',
      };
      const createdCampaign = { id: '123', ...newCampaign };
      (mockAxios.post as jest.Mock).mockResolvedValueOnce({ data: createdCampaign });

      const result = await campaignApi.create(newCampaign);

      expect(mockAxios.post).toHaveBeenCalledWith('/campaigns', newCampaign);
      expect(result).toEqual(createdCampaign);
    });
  });

  describe('update', () => {
    it('updates an existing campaign', async () => {
      const updateData = { name: 'Updated Campaign' };
      const updatedCampaign = { id: '123', name: 'Updated Campaign' };
      (mockAxios.put as jest.Mock).mockResolvedValueOnce({ data: updatedCampaign });

      const result = await campaignApi.update('123', updateData);

      expect(mockAxios.put).toHaveBeenCalledWith('/campaigns/123', updateData);
      expect(result).toEqual(updatedCampaign);
    });
  });

  describe('delete', () => {
    it('deletes a campaign', async () => {
      (mockAxios.delete as jest.Mock).mockResolvedValueOnce({});

      await campaignApi.delete('123');

      expect(mockAxios.delete).toHaveBeenCalledWith('/campaigns/123');
    });
  });

  describe('publish', () => {
    it('publishes a campaign to Google Ads', async () => {
      const publishResponse = {
        message: 'Campaign published successfully',
        campaign: { id: '123', status: 'PUBLISHED' },
        google_ads: { campaign_id: '456' },
      };
      (mockAxios.post as jest.Mock).mockResolvedValueOnce({ data: publishResponse });

      const result = await campaignApi.publish('123');

      expect(mockAxios.post).toHaveBeenCalledWith('/campaigns/123/publish');
      expect(result).toEqual(publishResponse);
    });
  });

  describe('pause', () => {
    it('pauses a campaign', async () => {
      const pauseResponse = {
        message: 'Campaign paused',
        campaign: { id: '123', status: 'PAUSED' },
      };
      (mockAxios.post as jest.Mock).mockResolvedValueOnce({ data: pauseResponse });

      const result = await campaignApi.pause('123');

      expect(mockAxios.post).toHaveBeenCalledWith('/campaigns/123/pause');
      expect(result).toEqual(pauseResponse);
    });
  });

  describe('enable', () => {
    it('enables a paused campaign', async () => {
      const enableResponse = {
        message: 'Campaign enabled',
        campaign: { id: '123', status: 'PUBLISHED' },
      };
      (mockAxios.post as jest.Mock).mockResolvedValueOnce({ data: enableResponse });

      const result = await campaignApi.enable('123');

      expect(mockAxios.post).toHaveBeenCalledWith('/campaigns/123/enable');
      expect(result).toEqual(enableResponse);
    });
  });

  describe('validate', () => {
    it('validates a campaign before publishing', async () => {
      const validationResult = {
        valid: true,
        errors: [],
        campaign_type: 'DEMAND_GEN',
      };
      (mockAxios.post as jest.Mock).mockResolvedValueOnce({ data: validationResult });

      const result = await campaignApi.validate('123');

      expect(mockAxios.post).toHaveBeenCalledWith('/campaigns/123/validate');
      expect(result).toEqual(validationResult);
    });

    it('returns validation errors when campaign is invalid', async () => {
      const validationResult = {
        valid: false,
        errors: ['Missing required field: headlines', 'Missing required field: descriptions'],
        campaign_type: 'DEMAND_GEN',
      };
      (mockAxios.post as jest.Mock).mockResolvedValueOnce({ data: validationResult });

      const result = await campaignApi.validate('123');

      expect(result.valid).toBe(false);
      expect(result.errors).toHaveLength(2);
    });
  });
});

describe('healthApi', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('check', () => {
    it('returns health status', async () => {
      const healthResponse = {
        status: 'healthy',
        checks: {
          database: { healthy: true, message: 'Database connection OK' },
          google_ads: { healthy: true, configured: true, message: 'Google Ads API configured' },
        },
      };
      (mockAxios.get as jest.Mock).mockResolvedValueOnce({ data: healthResponse });

      const result = await healthApi.check();

      expect(mockAxios.get).toHaveBeenCalledWith('/health');
      expect(result).toEqual(healthResponse);
    });

    it('returns unhealthy status when services are down', async () => {
      const healthResponse = {
        status: 'unhealthy',
        checks: {
          database: { healthy: false, message: 'Database connection failed' },
          google_ads: { healthy: true, configured: false, message: 'Google Ads API not configured' },
        },
      };
      (mockAxios.get as jest.Mock).mockResolvedValueOnce({ data: healthResponse });

      const result = await healthApi.check();

      expect(result.status).toBe('unhealthy');
      expect(result.checks.database.healthy).toBe(false);
    });
  });
});
