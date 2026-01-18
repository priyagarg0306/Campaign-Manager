"""
Pytest configuration and fixtures.
"""
import os

# Set testing environment BEFORE importing app modules
os.environ['FLASK_ENV'] = 'testing'
# Use SQLite in-memory for testing unless explicitly configured otherwise
if not os.environ.get('TEST_DATABASE_URL'):
    os.environ['TEST_DATABASE_URL'] = 'sqlite:///:memory:'

import pytest
from datetime import date, timedelta

from app import create_app, db
from app.models.campaign import Campaign


@pytest.fixture
def app():
    """Create application for testing."""
    from app import limiter

    app = create_app('testing')

    # Disable rate limiting for tests
    limiter.enabled = False

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """
    Create test client (no authentication required).

    This is kept for backward compatibility with existing tests.
    """
    return client


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def sample_campaign_data():
    """Sample campaign data for testing."""
    return {
        'name': 'Test Campaign',
        'objective': 'SALES',
        'campaign_type': 'DEMAND_GEN',
        'daily_budget': 10000000,  # $10 in micros
        'start_date': (date.today() + timedelta(days=1)).isoformat(),
        'end_date': (date.today() + timedelta(days=30)).isoformat(),
        'ad_group_name': 'Test Ad Group',
        'ad_headline': 'Amazing Product',
        'ad_description': 'Check out our amazing product with great features!',
        'asset_url': 'https://example.com/image.jpg',
        'final_url': 'https://example.com/landing',
        # New required fields for DEMAND_GEN campaigns
        'headlines': ['Amazing Product', 'Best Deal Ever'],
        'descriptions': ['Check out our amazing product with great features!'],
        'business_name': 'Test Business',
        'images': {
            'landscape_url': 'https://example.com/landscape.jpg',
            'square_url': 'https://example.com/square.jpg'
        }
    }


@pytest.fixture
def created_campaign(app, sample_campaign_data):
    """Create a campaign in the database."""
    with app.app_context():
        campaign = Campaign(
            name=sample_campaign_data['name'],
            objective=sample_campaign_data['objective'],
            campaign_type=sample_campaign_data['campaign_type'],
            daily_budget=sample_campaign_data['daily_budget'],
            start_date=date.fromisoformat(sample_campaign_data['start_date']),
            end_date=date.fromisoformat(sample_campaign_data['end_date']),
            ad_group_name=sample_campaign_data['ad_group_name'],
            ad_headline=sample_campaign_data['ad_headline'],
            ad_description=sample_campaign_data['ad_description'],
            asset_url=sample_campaign_data['asset_url'],
            final_url=sample_campaign_data['final_url'],
            # New required fields for DEMAND_GEN campaigns
            headlines=sample_campaign_data['headlines'],
            descriptions=sample_campaign_data['descriptions'],
            business_name=sample_campaign_data['business_name'],
            images=sample_campaign_data['images'],
            status='DRAFT'
        )
        db.session.add(campaign)
        db.session.commit()

        yield campaign

        # Cleanup
        db.session.delete(campaign)
        db.session.commit()
