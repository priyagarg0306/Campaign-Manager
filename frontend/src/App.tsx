/**
 * Main Application Component
 * Google Ads Campaign Manager
 */
import React, { useState } from 'react';
import { CampaignForm } from './components/CampaignForm';
import { CampaignList } from './components/CampaignList';
import { useCampaigns } from './hooks/useCampaigns';
import { Campaign } from './types/campaign';
import { CampaignFormValues } from './utils/validation';
import './App.css';

type View = 'list' | 'form';

function App() {
  const [view, setView] = useState<View>('list');
  const [editingCampaign, setEditingCampaign] = useState<Campaign | null>(null);
  const {
    campaigns,
    loading,
    error,
    createCampaign,
    updateCampaign,
    publishCampaign,
    pauseCampaign,
    enableCampaign,
    deleteCampaign,
    clearError,
    fetchCampaigns,
  } = useCampaigns();

  const handleEdit = (campaign: Campaign) => {
    setEditingCampaign(campaign);
    setView('form');
  };

  const handleCreateNew = () => {
    setEditingCampaign(null);
    setView('form');
  };

  const handleFormSubmit = async (data: CampaignFormValues) => {
    if (editingCampaign) {
      await updateCampaign(editingCampaign.id, data as any);
    } else {
      await createCampaign(data as any);
    }
    setView('list');
    setEditingCampaign(null);
  };

  const handleCancel = () => {
    setView('list');
    setEditingCampaign(null);
  };

  const handleRefresh = () => {
    clearError();
    fetchCampaigns();
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>Google Ads Campaign Manager</h1>
          <p>Create and manage your marketing campaigns</p>
        </div>
      </header>

      <nav className="app-nav">
        <button
          className={`nav-btn ${view === 'list' ? 'active' : ''}`}
          onClick={() => { setView('list'); setEditingCampaign(null); }}
        >
          Campaign List
        </button>
        <button
          className={`nav-btn ${view === 'form' && !editingCampaign ? 'active' : ''}`}
          onClick={handleCreateNew}
        >
          Create Campaign
        </button>
        {view === 'list' && (
          <button className="nav-btn refresh-btn" onClick={handleRefresh}>
            Refresh
          </button>
        )}
      </nav>

      <main className="app-main">
        {error && (
          <div className="global-error" role="alert">
            <span>{error}</span>
            <button onClick={clearError} aria-label="Dismiss error">
              x
            </button>
          </div>
        )}

        {view === 'form' ? (
          <CampaignForm
            onSubmit={handleFormSubmit}
            onCancel={handleCancel}
            loading={loading}
            initialData={editingCampaign}
            mode={editingCampaign ? 'edit' : 'create'}
          />
        ) : (
          <CampaignList
            campaigns={campaigns}
            loading={loading}
            onPublish={publishCampaign}
            onPause={pauseCampaign}
            onEnable={enableCampaign}
            onDelete={deleteCampaign}
            onEdit={handleEdit}
          />
        )}
      </main>

      <footer className="app-footer">
        <p>
          Google Ads Campaign Manager - Built with React, Flask, and PostgreSQL
        </p>
      </footer>
    </div>
  );
}

export default App;
