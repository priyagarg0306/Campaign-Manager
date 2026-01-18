/**
 * Campaign List Component
 * Displays all campaigns with actions
 */
import React, { useState, useMemo, useCallback, memo } from 'react';
import { Campaign, CampaignStatus } from '../types/campaign';
import './CampaignList.css';

interface CampaignListProps {
  campaigns: Campaign[];
  loading: boolean;
  onPublish: (id: string) => Promise<void>;
  onPause: (id: string) => Promise<void>;
  onEnable: (id: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onEdit: (campaign: Campaign) => void;
}

const statusColors: Record<CampaignStatus, string> = {
  DRAFT: '#ffc107',
  PUBLISHED: '#28a745',
  PAUSED: '#6c757d',
  ERROR: '#dc3545',
};

// Memoized currency formatter to avoid recreation on every render
const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
});

// Memoized date formatter
const dateFormatter = new Intl.DateTimeFormat('en-US');

const formatDate = (dateString: string | null): string => {
  if (!dateString) return '-';
  return dateFormatter.format(new Date(dateString));
};

const formatCurrency = (amount: number): string => {
  return currencyFormatter.format(amount);
};

const CampaignListComponent: React.FC<CampaignListProps> = ({
  campaigns,
  loading,
  onPublish,
  onPause,
  onEnable,
  onDelete,
  onEdit,
}) => {
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const handleAction = useCallback(async (
    action: (id: string) => Promise<void>,
    id: string,
    actionName: string
  ) => {
    setProcessingId(id);
    setActionError(null);
    try {
      await action(id);
    } catch (error) {
      setActionError(`Failed to ${actionName} campaign`);
    } finally {
      setProcessingId(null);
    }
  }, []);

  const handleDelete = useCallback(async (id: string, name: string) => {
    if (window.confirm(`Are you sure you want to delete "${name}"?`)) {
      await handleAction(onDelete, id, 'delete');
    }
  }, [handleAction, onDelete]);

  const handlePublish = useCallback((id: string) => handleAction(onPublish, id, 'publish'), [handleAction, onPublish]);
  const handlePause = useCallback((id: string) => handleAction(onPause, id, 'pause'), [handleAction, onPause]);
  const handleEnable = useCallback((id: string) => handleAction(onEnable, id, 'enable'), [handleAction, onEnable]);

  if (loading && campaigns.length === 0) {
    return <div className="campaign-list-loading">Loading campaigns...</div>;
  }

  if (campaigns.length === 0) {
    return (
      <div className="campaign-list-empty">
        <p>No campaigns found.</p>
        <p>Create your first campaign to get started!</p>
      </div>
    );
  }

  return (
    <div className="campaign-list">
      <h2>Campaigns ({campaigns.length})</h2>

      {actionError && (
        <div className="alert alert-error" role="alert">
          {actionError}
          <button
            className="alert-close"
            onClick={() => setActionError(null)}
            aria-label="Close"
          >
            x
          </button>
        </div>
      )}

      <div className="campaign-table-container">
        <table className="campaign-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Objective</th>
              <th>Type</th>
              <th>Budget</th>
              <th>Start Date</th>
              <th>Status</th>
              <th>Google Campaign ID</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {campaigns.map((campaign) => (
              <tr key={campaign.id}>
                <td className="campaign-name">{campaign.name}</td>
                <td>{campaign.objective}</td>
                <td>{campaign.campaign_type}</td>
                <td>{formatCurrency(campaign.daily_budget_usd)}/day</td>
                <td>{formatDate(campaign.start_date)}</td>
                <td>
                  <span
                    className="status-badge"
                    style={{ backgroundColor: statusColors[campaign.status] }}
                  >
                    {campaign.status}
                  </span>
                </td>
                <td className="google-id">
                  {campaign.google_campaign_id || '-'}
                </td>
                <td className="actions">
                  {campaign.status === 'DRAFT' && (
                    <>
                      <button
                        className="btn btn-sm btn-secondary"
                        onClick={() => onEdit(campaign)}
                        disabled={processingId === campaign.id}
                      >
                        Edit
                      </button>
                      <button
                        className="btn btn-sm btn-primary"
                        onClick={() => handlePublish(campaign.id)}
                        disabled={processingId === campaign.id}
                      >
                        {processingId === campaign.id ? '...' : 'Publish'}
                      </button>
                      <button
                        className="btn btn-sm btn-danger"
                        onClick={() => handleDelete(campaign.id, campaign.name)}
                        disabled={processingId === campaign.id}
                      >
                        Delete
                      </button>
                    </>
                  )}
                  {campaign.status === 'PUBLISHED' && (
                    <button
                      className="btn btn-sm btn-warning"
                      onClick={() => handlePause(campaign.id)}
                      disabled={processingId === campaign.id}
                    >
                      {processingId === campaign.id ? '...' : 'Pause'}
                    </button>
                  )}
                  {campaign.status === 'PAUSED' && (
                    <button
                      className="btn btn-sm btn-success"
                      onClick={() => handleEnable(campaign.id)}
                      disabled={processingId === campaign.id}
                    >
                      {processingId === campaign.id ? '...' : 'Enable'}
                    </button>
                  )}
                  {campaign.status === 'ERROR' && (
                    <span className="error-text">Publishing failed</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Export memoized component to prevent unnecessary re-renders
export const CampaignList = memo(CampaignListComponent);

export default CampaignList;
