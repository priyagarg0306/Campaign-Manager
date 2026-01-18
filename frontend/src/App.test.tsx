import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from './App';
import { useCampaigns } from './hooks/useCampaigns';

// Mock the useCampaigns hook
const mockUseCampaigns = {
  campaigns: [],
  loading: false,
  error: null,
  fetchCampaigns: jest.fn(),
  createCampaign: jest.fn(),
  updateCampaign: jest.fn(),
  publishCampaign: jest.fn(),
  pauseCampaign: jest.fn(),
  enableCampaign: jest.fn(),
  deleteCampaign: jest.fn(),
  clearError: jest.fn(),
};

jest.mock('./hooks/useCampaigns', () => ({
  useCampaigns: jest.fn(() => mockUseCampaigns),
}));

const mockUseCampaignsHook = useCampaigns as jest.MockedFunction<typeof useCampaigns>;

describe('App', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseCampaignsHook.mockReturnValue(mockUseCampaigns as any);
  });

  describe('rendering', () => {
    it('renders the header', () => {
      render(<App />);
      expect(screen.getByText('Google Ads Campaign Manager')).toBeInTheDocument();
    });

    it('renders the subheader', () => {
      render(<App />);
      expect(screen.getByText('Create and manage your marketing campaigns')).toBeInTheDocument();
    });

    it('renders the navigation buttons', () => {
      render(<App />);
      expect(screen.getByText('Campaign List')).toBeInTheDocument();
      expect(screen.getByText('Create Campaign')).toBeInTheDocument();
    });

    it('renders the footer', () => {
      render(<App />);
      expect(screen.getByText(/Built with React, Flask, and PostgreSQL/i)).toBeInTheDocument();
    });

    it('shows campaign list by default', () => {
      render(<App />);
      expect(screen.getByText(/No campaigns found/i)).toBeInTheDocument();
    });

    it('shows refresh button on list view', () => {
      render(<App />);
      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });
  });

  describe('navigation', () => {
    it('switches to create form when clicking Create Campaign', () => {
      render(<App />);
      fireEvent.click(screen.getByText('Create Campaign'));
      expect(screen.getByText('Create New Campaign')).toBeInTheDocument();
    });

    it('switches back to list when clicking Campaign List', () => {
      render(<App />);
      fireEvent.click(screen.getByText('Create Campaign'));
      expect(screen.getByText('Create New Campaign')).toBeInTheDocument();

      fireEvent.click(screen.getByText('Campaign List'));
      expect(screen.getByText(/No campaigns found/i)).toBeInTheDocument();
    });

    it('hides refresh button when on form view', () => {
      render(<App />);
      expect(screen.getByText('Refresh')).toBeInTheDocument();

      fireEvent.click(screen.getByText('Create Campaign'));
      expect(screen.queryByText('Refresh')).not.toBeInTheDocument();
    });

    it('highlights active navigation button', () => {
      render(<App />);
      const listBtn = screen.getByText('Campaign List');
      expect(listBtn.className).toContain('active');

      fireEvent.click(screen.getByText('Create Campaign'));
      const createBtn = screen.getByText('Create Campaign');
      expect(createBtn.className).toContain('active');
    });
  });

  describe('error handling', () => {
    it('displays error when present', () => {
      mockUseCampaignsHook.mockReturnValue({
        ...mockUseCampaigns,
        error: 'Failed to fetch campaigns',
      } as any);

      render(<App />);
      expect(screen.getByText('Failed to fetch campaigns')).toBeInTheDocument();
    });

    it('calls clearError when dismiss button clicked', () => {
      const mockClearError = jest.fn();
      mockUseCampaignsHook.mockReturnValue({
        ...mockUseCampaigns,
        error: 'Some error',
        clearError: mockClearError,
      } as any);

      render(<App />);
      const dismissButton = screen.getByRole('button', { name: /dismiss error/i });
      fireEvent.click(dismissButton);

      expect(mockClearError).toHaveBeenCalled();
    });

    it('does not display error alert when no error', () => {
      render(<App />);
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  describe('refresh functionality', () => {
    it('calls fetchCampaigns and clearError when refresh clicked', () => {
      const mockFetchCampaigns = jest.fn();
      const mockClearError = jest.fn();
      mockUseCampaignsHook.mockReturnValue({
        ...mockUseCampaigns,
        fetchCampaigns: mockFetchCampaigns,
        clearError: mockClearError,
      } as any);

      render(<App />);
      fireEvent.click(screen.getByText('Refresh'));

      expect(mockClearError).toHaveBeenCalled();
      expect(mockFetchCampaigns).toHaveBeenCalled();
    });
  });

  describe('campaign list with campaigns', () => {
    const mockCampaigns = [
      {
        id: '1',
        name: 'Test Campaign',
        status: 'DRAFT',
        campaign_type: 'DEMAND_GEN',
        objective: 'SALES',
        daily_budget: 1000,
        start_date: '2030-01-01',
      },
    ];

    it('renders campaigns in the list', () => {
      mockUseCampaignsHook.mockReturnValue({
        ...mockUseCampaigns,
        campaigns: mockCampaigns,
      } as any);

      render(<App />);
      expect(screen.getByText('Test Campaign')).toBeInTheDocument();
    });

    it('calls onEdit when edit button clicked', () => {
      mockUseCampaignsHook.mockReturnValue({
        ...mockUseCampaigns,
        campaigns: mockCampaigns,
      } as any);

      render(<App />);
      const editButton = screen.getByRole('button', { name: /edit/i });
      fireEvent.click(editButton);

      // Should switch to form view in edit mode
      expect(screen.getByText('Edit Campaign')).toBeInTheDocument();
    });
  });

  describe('form interactions', () => {
    it('shows create form in create mode', () => {
      render(<App />);
      fireEvent.click(screen.getByText('Create Campaign'));
      expect(screen.getByText('Create New Campaign')).toBeInTheDocument();
    });

    it('shows edit form in edit mode', () => {
      const mockCampaigns = [
        {
          id: '1',
          name: 'Test Campaign',
          status: 'DRAFT',
          campaign_type: 'DEMAND_GEN',
          objective: 'SALES',
          daily_budget: 1000,
          start_date: '2030-01-01',
        },
      ];

      mockUseCampaignsHook.mockReturnValue({
        ...mockUseCampaigns,
        campaigns: mockCampaigns,
      } as any);

      render(<App />);

      // Click edit button
      const editButton = screen.getByRole('button', { name: /edit/i });
      fireEvent.click(editButton);

      expect(screen.getByText('Edit Campaign')).toBeInTheDocument();
    });

    it('returns to list view after canceling form', () => {
      render(<App />);
      fireEvent.click(screen.getByText('Create Campaign'));
      expect(screen.getByText('Create New Campaign')).toBeInTheDocument();

      fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
      expect(screen.getByText(/No campaigns found/i)).toBeInTheDocument();
    });

    it('passes initialData to form in edit mode', () => {
      const mockCampaigns = [
        {
          id: '1',
          name: 'Test Campaign',
          status: 'DRAFT',
          campaign_type: 'DEMAND_GEN',
          objective: 'SALES',
          daily_budget: 1000,
          start_date: '2030-01-01',
        },
      ];

      mockUseCampaignsHook.mockReturnValue({
        ...mockUseCampaigns,
        campaigns: mockCampaigns,
      } as any);

      render(<App />);
      const editButton = screen.getByRole('button', { name: /edit/i });
      fireEvent.click(editButton);

      // The form should have the campaign name pre-filled
      const nameInput = screen.getByLabelText(/campaign name/i) as HTMLInputElement;
      expect(nameInput.value).toBe('Test Campaign');
    });
  });

  describe('loading state', () => {
    it('passes loading state to components', () => {
      mockUseCampaignsHook.mockReturnValue({
        ...mockUseCampaigns,
        loading: true,
      } as any);

      render(<App />);
      fireEvent.click(screen.getByText('Create Campaign'));

      // Form should be disabled when loading
      expect(screen.getByLabelText(/campaign name/i)).toBeDisabled();
    });
  });
});
