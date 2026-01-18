import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CampaignForm } from './CampaignForm';

describe('CampaignForm', () => {
  const mockOnSubmit = jest.fn();
  const mockOnCancel = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders all form fields', () => {
    render(<CampaignForm onSubmit={mockOnSubmit} />);

    expect(screen.getByLabelText(/campaign name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^objective/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/campaign type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/daily budget/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/start date/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/end date/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/ad group name/i)).toBeInTheDocument();
    // New dynamic form uses Headlines and Descriptions sections
    expect(screen.getByText(/headlines/i)).toBeInTheDocument();
    expect(screen.getByText(/descriptions/i)).toBeInTheDocument();
  });

  it('shows validation errors for required fields', async () => {
    render(<CampaignForm onSubmit={mockOnSubmit} />);

    const submitButton = screen.getByRole('button', { name: /save campaign/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/campaign name is required/i)).toBeInTheDocument();
    });
  });

  it('calls onCancel when cancel button is clicked', () => {
    render(<CampaignForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);

    expect(mockOnCancel).toHaveBeenCalled();
  });

  it('disables form when loading', () => {
    render(<CampaignForm onSubmit={mockOnSubmit} loading={true} />);

    expect(screen.getByLabelText(/campaign name/i)).toBeDisabled();
    expect(screen.getByRole('button', { name: /saving/i })).toBeDisabled();
  });

  it('has correct default values', () => {
    render(<CampaignForm onSubmit={mockOnSubmit} />);

    const objectiveSelect = screen.getByLabelText(/^objective/i) as HTMLSelectElement;
    expect(objectiveSelect.value).toBe('SALES');

    const campaignTypeSelect = screen.getByLabelText(/campaign type/i) as HTMLSelectElement;
    expect(campaignTypeSelect.value).toBe('DEMAND_GEN');
  });

  it('shows all objective options', () => {
    render(<CampaignForm onSubmit={mockOnSubmit} />);

    const objectiveSelect = screen.getByLabelText(/^objective/i);
    expect(objectiveSelect).toContainHTML('Sales');
    expect(objectiveSelect).toContainHTML('Leads');
    expect(objectiveSelect).toContainHTML('Website Traffic');
  });

  it('shows all campaign type options', () => {
    render(<CampaignForm onSubmit={mockOnSubmit} />);

    const typeSelect = screen.getByLabelText(/campaign type/i);
    expect(typeSelect).toContainHTML('Demand Gen');
    expect(typeSelect).toContainHTML('Search');
    expect(typeSelect).toContainHTML('Display');
  });
});
