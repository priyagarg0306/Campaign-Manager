import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { CampaignList } from './CampaignList';
import { Campaign } from '../types/campaign';

describe('CampaignList', () => {
  const mockCampaigns: Campaign[] = [
    {
      id: '1',
      name: 'Test Campaign 1',
      objective: 'SALES',
      campaign_type: 'DEMAND_GEN',
      daily_budget: 10000000,
      daily_budget_usd: 10,
      start_date: '2024-01-20',
      end_date: null,
      status: 'DRAFT',
      google_campaign_id: null,
      google_ad_group_id: null,
      google_ad_id: null,
      ad_group_name: null,
      ad_headline: null,
      ad_description: null,
      asset_url: null,
      final_url: null,
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:00:00Z',
    },
    {
      id: '2',
      name: 'Test Campaign 2',
      objective: 'LEADS',
      campaign_type: 'DISPLAY',
      daily_budget: 5000000,
      daily_budget_usd: 5,
      start_date: '2024-01-25',
      end_date: '2024-02-25',
      status: 'PUBLISHED',
      google_campaign_id: '123456',
      google_ad_group_id: '789012',
      google_ad_id: '345678',
      ad_group_name: 'Test Group',
      ad_headline: 'Test Headline',
      ad_description: 'Test Description',
      asset_url: null,
      final_url: 'https://example.com',
      created_at: '2024-01-14T10:00:00Z',
      updated_at: '2024-01-14T12:00:00Z',
    },
  ];

  const mockOnPublish = jest.fn();
  const mockOnPause = jest.fn();
  const mockOnEnable = jest.fn();
  const mockOnDelete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders empty state when no campaigns', () => {
    render(
      <CampaignList
        campaigns={[]}
        loading={false}
        onPublish={mockOnPublish}
        onPause={mockOnPause}
        onEnable={mockOnEnable}
        onDelete={mockOnDelete}
      />
    );

    expect(screen.getByText(/no campaigns found/i)).toBeInTheDocument();
  });

  it('renders loading state', () => {
    render(
      <CampaignList
        campaigns={[]}
        loading={true}
        onPublish={mockOnPublish}
        onPause={mockOnPause}
        onEnable={mockOnEnable}
        onDelete={mockOnDelete}
      />
    );

    expect(screen.getByText(/loading campaigns/i)).toBeInTheDocument();
  });

  it('renders campaign list', () => {
    render(
      <CampaignList
        campaigns={mockCampaigns}
        loading={false}
        onPublish={mockOnPublish}
        onPause={mockOnPause}
        onEnable={mockOnEnable}
        onDelete={mockOnDelete}
      />
    );

    expect(screen.getByText('Test Campaign 1')).toBeInTheDocument();
    expect(screen.getByText('Test Campaign 2')).toBeInTheDocument();
    expect(screen.getByText('Campaigns (2)')).toBeInTheDocument();
  });

  it('shows Publish button for DRAFT campaigns', () => {
    render(
      <CampaignList
        campaigns={mockCampaigns}
        loading={false}
        onPublish={mockOnPublish}
        onPause={mockOnPause}
        onEnable={mockOnEnable}
        onDelete={mockOnDelete}
      />
    );

    const publishButtons = screen.getAllByText('Publish');
    expect(publishButtons.length).toBe(1);
  });

  it('shows Pause button for PUBLISHED campaigns', () => {
    render(
      <CampaignList
        campaigns={mockCampaigns}
        loading={false}
        onPublish={mockOnPublish}
        onPause={mockOnPause}
        onEnable={mockOnEnable}
        onDelete={mockOnDelete}
      />
    );

    const pauseButtons = screen.getAllByText('Pause');
    expect(pauseButtons.length).toBe(1);
  });

  it('calls onPublish when Publish button is clicked', async () => {
    render(
      <CampaignList
        campaigns={mockCampaigns}
        loading={false}
        onPublish={mockOnPublish}
        onPause={mockOnPause}
        onEnable={mockOnEnable}
        onDelete={mockOnDelete}
      />
    );

    const publishButton = screen.getByText('Publish');
    fireEvent.click(publishButton);

    expect(mockOnPublish).toHaveBeenCalledWith('1');
  });

  it('calls onPause when Pause button is clicked', () => {
    render(
      <CampaignList
        campaigns={mockCampaigns}
        loading={false}
        onPublish={mockOnPublish}
        onPause={mockOnPause}
        onEnable={mockOnEnable}
        onDelete={mockOnDelete}
      />
    );

    const pauseButton = screen.getByText('Pause');
    fireEvent.click(pauseButton);

    expect(mockOnPause).toHaveBeenCalledWith('2');
  });

  it('displays Google Campaign ID for published campaigns', () => {
    render(
      <CampaignList
        campaigns={mockCampaigns}
        loading={false}
        onPublish={mockOnPublish}
        onPause={mockOnPause}
        onEnable={mockOnEnable}
        onDelete={mockOnDelete}
      />
    );

    expect(screen.getByText('123456')).toBeInTheDocument();
  });

  it('shows confirmation dialog before deleting', () => {
    window.confirm = jest.fn(() => true);

    render(
      <CampaignList
        campaigns={mockCampaigns}
        loading={false}
        onPublish={mockOnPublish}
        onPause={mockOnPause}
        onEnable={mockOnEnable}
        onDelete={mockOnDelete}
      />
    );

    const deleteButton = screen.getByText('Delete');
    fireEvent.click(deleteButton);

    expect(window.confirm).toHaveBeenCalled();
    expect(mockOnDelete).toHaveBeenCalledWith('1');
  });

  it('does not delete when confirmation is cancelled', () => {
    window.confirm = jest.fn(() => false);

    render(
      <CampaignList
        campaigns={mockCampaigns}
        loading={false}
        onPublish={mockOnPublish}
        onPause={mockOnPause}
        onEnable={mockOnEnable}
        onDelete={mockOnDelete}
      />
    );

    const deleteButton = screen.getByText('Delete');
    fireEvent.click(deleteButton);

    expect(window.confirm).toHaveBeenCalled();
    expect(mockOnDelete).not.toHaveBeenCalled();
  });
});
